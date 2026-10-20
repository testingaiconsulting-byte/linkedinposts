"""Turn the approved slide PNGs (1080x1350) into an Instagram Reel (1080x1920, H.264 + AAC).

Usage:
  python3 render_reel.py <slides_dir> <out.mp4> [--music FILE] [--secs 3] [--start 0] [--theme classic]

Each slide sits centred on the theme colour with a slow zoom; slides cross-fade.
The music (optional) starts at --start seconds, is cut to the video length and fades in/out.
Needs ffmpeg with libx264 and aac.
"""
import argparse, glob, os, subprocess, sys

THEMES = {"classic": "0x0F2F1A", "midnight": "0x0A100C", "gold": "0xBF8448"}
FPS, W, H, FADE = 30, 1080, 1920, 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slides_dir")
    ap.add_argument("out")
    ap.add_argument("--music")
    ap.add_argument("--secs", type=float, default=3.0)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--theme", default="classic")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.slides_dir, "*.png")),
                   key=lambda p: int(os.path.splitext(os.path.basename(p))[0]) if os.path.splitext(os.path.basename(p))[0].isdigit() else 999)
    if not files:
        sys.exit("no slides found")
    secs = max(1.5, min(a.secs, 8.0))
    if len(files) == 1:
        secs = max(secs, 6.0)  # a single image still needs a few seconds to read
    n = len(files)
    total = n * secs - (n - 1) * FADE
    bg = THEMES.get(a.theme, THEMES["classic"])
    frames = int(round(secs * FPS))

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for f in files:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{secs:.3f}", "-i", f]
    if a.music:
        cmd += ["-ss", f"{max(0.0, a.start):.2f}", "-i", a.music]
    else:
        # Instagram handles Reels without an audio track badly: use silence
        cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]

    parts = []
    for i in range(n):
        # slide 1080x1350 centred on a 1080x1920 canvas, gentle zoom from 1.00 to 1.05
        parts.append(
            f"[{i}:v]scale={W}:-2,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={bg},"
            f"scale={W*2}:{H*2},zoompan=z='1+0.05*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
            f"trim=duration={secs:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    last = "v0"
    for i in range(1, n):
        off = i * (secs - FADE)
        parts.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={off:.3f}[x{i}]")
        last = f"x{i}"
    parts.append(f"[{last}]trim=duration={total:.3f},setpts=PTS-STARTPTS[vout]")
    fo = max(0.0, total - 1.2)
    parts.append(f"[{n}:a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.6,afade=t=out:st={fo:.3f}:d=1.2,aresample=44100[aout]")

    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", "[aout]",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2",
            "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high", "-level", "4.1",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-b:v", "4M", "-maxrate", "5M", "-bufsize", "8M",
            "-movflags", "+faststart", "-t", f"{total:.3f}", a.out]
    subprocess.run(cmd, check=True)
    print(f"ok {n} slides, {total:.1f}s -> {a.out}")


if __name__ == "__main__":
    main()
