# linkedinposts

Fila de publicação dos posts aprovados na Central de Conteúdo. O GitHub corre `publish.py` de 15 em 15 minutos e publica no LinkedIn os posts cuja hora já chegou, com imagem ou carrossel em PDF, através da API oficial.

**Atenção:** este repositório é público. Só entram aqui textos e visuais de posts já aprovados. Nunca dados de contactos, e nunca chaves (essas ficam em *Settings → Secrets*).

## Como funciona

- `queue/<id>/post.json` — texto, hora (`publishAt`) e ficheiros de cada post.
- `queue/<id>/*.png | *.pdf` — os visuais.
- `published.json` — o que já saiu, com o link. Um post nunca é publicado duas vezes.
- `.github/workflows/publicar.yml` — a publicação automática. Também se pode correr à mão em *Actions → Publicar no LinkedIn → Run workflow* (com a opção de só simular).
- `.github/workflows/verificar-acesso.yml` — confirma todas as segundas que o acesso ao LinkedIn continua válido.

## Configuração (uma vez)

1. Em [developer.linkedin.com](https://developer.linkedin.com/) → *Create app*, associada à página da empresa.
2. No separador *Products*, pedir **Share on LinkedIn** e **Sign In with LinkedIn using OpenID Connect**.
3. Em *Docs and tools → OAuth Token Tools → Create token*, escolher a app e os âmbitos `openid`, `profile` e `w_member_social`, e autorizar.
4. Neste repositório, *Settings → Secrets and variables → Actions → New repository secret*:
   - `LINKEDIN_ACCESS_TOKEN` — o token gerado no passo 3.
5. Correr *Actions → Verificar acesso ao LinkedIn*. Deve dizer "Acesso OK".

O token dura 60 dias. Quando expirar, repetir o passo 3 e substituir o segredo.

Para publicar na página da empresa em vez do perfil pessoal, é preciso o produto *Community Management API* (aprovação pelo LinkedIn) e o segredo `LINKEDIN_AUTHOR_URN` com `urn:li:organization:<id>`.

## Instagram (via Metricool)

Os posts do Instagram aprovados no painel são publicados pelo Metricool, que precisa de imagens com um link público.

- `render/render.js` — gera os JPG (1080×1350) de um post a partir dos slides do painel, com as letras em `render/fonts/` (Archivo e IBM Plex, licença OFL).
- `ig/<id>/NN.jpg` — as imagens de cada post aprovado, servidas por `raw.githubusercontent.com`.

Uma tarefa agendada no Claude gera as imagens, faz *commit* aqui e agenda o post no Metricool para a hora aprovada.
