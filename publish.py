"""Publica no LinkedIn os posts da fila cuja hora já chegou.

Estrutura da fila:
    queue/<id>/post.json   texto, hora de publicação e lista de ficheiros
    queue/<id>/<ficheiros> imagens (.png/.jpg) ou um .pdf para carrossel

post.json:
    {
      "id": "2026-10-20-primeira-pergunta",
      "publishAt": "2026-10-20T09:15:00+01:00",
      "text": "texto do post",
      "media": ["imagem.png"]              # opcional; 1 a 20 imagens, ou 1 PDF
      "documentTitle": "Título do PDF"     # obrigatório se media for um PDF
    }

Os posts publicados ficam registados em published.json (id -> URN e data),
para nunca serem publicados duas vezes.

Variáveis de ambiente (segredos do GitHub):
    LINKEDIN_ACCESS_TOKEN  obrigatório
    LINKEDIN_AUTHOR_URN    opcional; urn:li:person:... ou urn:li:organization:...
                           se faltar, é obtido de /v2/userinfo (perfil pessoal)
    LINKEDIN_VERSION       opcional; versão da API no formato AAAAMM
    DRY_RUN=1              mostra o que faria sem publicar
"""
import datetime as dt
import json
import mimetypes
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
QUEUE = ROOT / "queue"
PUBLISHED = ROOT / "published.json"
API = "https://api.linkedin.com"
TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
VERSION = os.environ.get("LINKEDIN_VERSION", "").strip() or "202605"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


class LinkedInError(Exception):
    pass


def request(method, url, body=None, headers=None, raw=None, rest=True):
    h = {"Authorization": f"Bearer {TOKEN}"}
    if rest:
        h.update({"LinkedIn-Version": VERSION, "X-Restli-Protocol-Version": "2.0.0"})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        h["Content-Type"] = "application/octet-stream"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = r.read().decode("utf-8") or "{}"
            return r.status, dict(r.headers), json.loads(text) if text.strip().startswith(("{", "[")) else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        raise LinkedInError(f"{method} {url} -> {e.code}: {detail}") from None


def author_urn():
    urn = os.environ.get("LINKEDIN_AUTHOR_URN", "").strip()
    if urn:
        return urn
    _, _, info = request("GET", f"{API}/v2/userinfo", rest=False)
    if not info.get("sub"):
        raise LinkedInError("Não consegui obter o autor: defina LINKEDIN_AUTHOR_URN ou ative o produto 'Sign In with LinkedIn using OpenID Connect'.")
    return f"urn:li:person:{info['sub']}"


# Caracteres reservados no formato "little text" da API de posts.
RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")
HASHTAG = re.compile(r"(?<![\w#])#([0-9A-Za-zÀ-ÿ_]+)")


def to_commentary(text):
    """Escapa caracteres reservados e transforma #palavra em hashtags clicáveis."""
    out, last = [], 0
    for m in HASHTAG.finditer(text):
        out.append(RESERVED.sub(r"\\\1", text[last:m.start()]))
        out.append("{hashtag|\\#|" + m.group(1) + "}")
        last = m.end()
    out.append(RESERVED.sub(r"\\\1", text[last:]))
    return "".join(out)


def upload(kind, owner, path):
    """kind: 'images' ou 'documents'. Devolve o URN do ficheiro enviado."""
    _, _, init = request("POST", f"{API}/rest/{kind}?action=initializeUpload",
                         body={"initializeUploadRequest": {"owner": owner}})
    value = init["value"]
    urn = value.get("image") or value.get("document")
    request("PUT", value["uploadUrl"], raw=path.read_bytes(), rest=False)
    # espera que o LinkedIn processe o ficheiro
    for _ in range(30):
        _, _, meta = request("GET", f"{API}/rest/{kind}/{urllib.parse.quote(urn, safe='')}")
        if meta.get("status") == "AVAILABLE":
            return urn
        if meta.get("status") in ("PROCESSING_FAILED",):
            raise LinkedInError(f"O LinkedIn não conseguiu processar {path.name}.")
        time.sleep(4)
    return urn


def publish(post, folder, owner):
    media = [folder / m for m in post.get("media", [])]
    for f in media:
        if not f.is_file():
            raise LinkedInError(f"Ficheiro em falta: {f.relative_to(ROOT)}")
    body = {
        "author": owner,
        "commentary": to_commentary(post["text"]),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    pdfs = [f for f in media if f.suffix.lower() == ".pdf"]
    images = [f for f in media if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif")]
    if pdfs:
        if len(media) != 1:
            raise LinkedInError("Um post com PDF não pode ter outros ficheiros.")
        title = post.get("documentTitle") or post["id"]
        body["content"] = {"media": {"id": upload("documents", owner, pdfs[0]), "title": title}}
    elif len(images) == 1:
        body["content"] = {"media": {"id": upload("images", owner, images[0]),
                                     "altText": post.get("altText", "")[:4086]}}
    elif len(images) > 1:
        body["content"] = {"multiImage": {"images": [{"id": upload("images", owner, f), "altText": ""} for f in images[:20]]}}
    _, headers, _ = request("POST", f"{API}/rest/posts", body=body)
    return headers.get("x-restli-id") or headers.get("X-RestLi-Id") or ""


def main():
    published = json.loads(PUBLISHED.read_text()) if PUBLISHED.exists() else {}
    now = dt.datetime.now(dt.timezone.utc)
    due = []
    for f in sorted(QUEUE.glob("*/post.json")):
        post = json.loads(f.read_text())
        post.setdefault("id", f.parent.name)
        if post["id"] in published:
            continue
        when = dt.datetime.fromisoformat(post["publishAt"])
        if when <= now:
            due.append((post, f.parent))
    if not due:
        print("Nada para publicar agora.")
        return 0
    if not TOKEN and not DRY_RUN:
        print("Falta o segredo LINKEDIN_ACCESS_TOKEN.", file=sys.stderr)
        return 1
    owner = author_urn() if not DRY_RUN else os.environ.get("LINKEDIN_AUTHOR_URN", "urn:li:person:TESTE")
    failures = 0
    for post, folder in due:
        if DRY_RUN:
            print(f"[simulação] publicaria {post['id']} com {post.get('media', [])}")
            print(to_commentary(post["text"])[:300])
            continue
        try:
            urn = publish(post, folder, owner)
            published[post["id"]] = {"urn": urn, "url": f"https://www.linkedin.com/feed/update/{urn}" if urn else "",
                                     "publishedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            PUBLISHED.write_text(json.dumps(published, ensure_ascii=False, indent=1) + "\n")
            print(f"Publicado {post['id']}: {urn}")
        except LinkedInError as e:
            failures += 1
            print(f"Falhou {post['id']}: {e}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
