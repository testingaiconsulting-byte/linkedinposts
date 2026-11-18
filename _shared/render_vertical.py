"""Reels animados e stories (1080x1920) a partir das imagens de feed (1080x1350) de qualquer cliente.

Uso:
  python3 _shared/render_vertical.py reel  <pasta_com_slides> <saida.mp4> [--bg 0x0044FF] [--music FICHEIRO] [--start 0] [--capa capa.jpg]
  python3 _shared/render_vertical.py story <imagem.jpg|png> <saida.jpg> [--bg 0x0044FF]

Reel: cada slide entra a subir com fade (0,6 s), fica com um zoom lento e passa ao seguinte a deslizar para a
esquerda; atrás, a cor da marca (--bg) ou, sem --bg, o próprio slide desfocado. 1.º slide 3,6 s, os outros 3,2 s,
o último +1 s; um slide sozinho dura 6 s. Música opcional (cortada à duração, com fade), senão áudio mudo.
--capa grava também a imagem de capa do reel (o 1.º slide sobre o fundo).
Story: o slide centrado no fundo (cor da marca ou o slide desfocado).
Precisa de ffmpeg com libx264 e aac.
"""
import argparse, glob, os, subprocess, sys

FPS, W, H, FH, TR = 30, 1080, 1920, 1350, 0.45
Y0 = (H - FH) // 2


def bg_chain(i, bg):
    if bg:
        return f"color=c={bg}:s={W}x{H}:r={FPS}"
    return None


def slides_in(folder):
    fs = glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png"))
    fs = [f for f in fs if os.path.splitext(os.path.basename(f))[0].isdigit()]
    return sorted(fs, key=lambda p: int(os.path.splitext(os.path.basename(p))[0]))


def run(cmd):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + cmd, check=True)


def story(img, out, bg):
    if bg:
        f = f"color=c={bg}:s={W}x{H}[b];[0:v]scale={W}:-2[f];[b][f]overlay=0:(H-h)/2:shortest=1,format=yuvj420p"
    else:
        f = (f"[0:v]split[a][c];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.12[b];"
             f"[c]scale={W}:-2[f];[b][f]overlay=0:(H-h)/2,format=yuvj420p")
    run(["-i", img, "-filter_complex", f, "-frames:v", "1", "-q:v", "2", out])


def reel(folder, out, bg, music, start, capa):
    fs = slides_in(folder)
    if not fs:
        sys.exit("sem slides (01.jpg, 02.jpg… ou 1.png, 2.png…)")
    n = len(fs)
    durs = [6.0] if n == 1 else [3.6] + [3.2] * (n - 2) + [4.2]
    cmd, parts = [], []
    for f, d in zip(fs, durs):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", f]
    total = sum(durs) - TR * (n - 1)
    if music:
        cmd += ["-ss", f"{max(0.0, start):.2f}", "-i", music]
    else:
        cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    for i, d in enumerate(durs):
        fr = int(round(d * FPS))
        if bg:
            parts.append(f"color=c={bg}:s={W}x{H}:r={FPS}:d={d:.2f}[b{i}]")
            parts.append(f"[{i}:v]scale={W}:{FH},setsar=1,format=rgba[s{i}]")
        else:
            parts.append(f"[{i}:v]split[a{i}][s0{i}]")
            parts.append(f"[a{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.12,setsar=1[b{i}]")
            parts.append(f"[s0{i}]scale={W}:{FH},setsar=1,format=rgba[s{i}]")
        # zoom lento (1,00 -> 1,04) no slide, depois entrada a subir com fade
        parts.append(f"[s{i}]scale={W*2}:{FH*2},zoompan=z='1+0.04*on/{fr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{FH}:fps={FPS},"
                     f"format=rgba,fade=t=in:st=0:d=0.45:alpha=1[z{i}]")
        parts.append(f"[b{i}][z{i}]overlay=x=0:y='{Y0}+if(lt(t,0.6),220*pow(1-t/0.6,3),0)':shortest=1,"
                     f"trim=duration={d:.2f},setpts=PTS-STARTPTS,format=yuv420p,fps={FPS}[v{i}]")
    last, off = "v0", 0.0
    for i in range(1, n):
        off += durs[i - 1] - TR
        parts.append(f"[{last}][v{i}]xfade=transition=slideleft:duration={TR}:offset={off:.3f}[x{i}]")
        last = f"x{i}"
    parts.append(f"[{last}]trim=duration={total:.3f},setpts=PTS-STARTPTS[vout]")
    fo = max(0.0, total - 1.2)
    parts.append(f"[{n}:a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.6,afade=t=out:st={fo:.3f}:d=1.2,aresample=44100[aout]")
    run(cmd + ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", "[aout]",
               "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
               "-r", str(FPS), "-b:v", "5M", "-maxrate", "6M", "-bufsize", "10M", "-c:a", "aac", "-b:a", "128k", "-ac", "2",
               "-movflags", "+faststart", "-t", f"{total:.3f}", out])
    if capa:
        story(fs[0], capa, bg)
    print(f"reel {n} slides, {total:.1f}s -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["reel", "story"])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--bg", default="")
    ap.add_argument("--music")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--capa")
    a = ap.parse_args()
    if a.modo == "story":
        story(a.src, a.out, a.bg)
    else:
        reel(a.src, a.out, a.bg, a.music, a.start, a.capa)


if __name__ == "__main__":
    main()
