"""Frame-loop harness shared by observable-video scripts.

    from harness import main
    def frame(t, path): ...      # draw one frame at time t (s) and save PNG to path
    if __name__ == "__main__":
        main(frame, T_END, FPS)

CLI:  script.py OUTDIR [lo:hi] [--preview t1,t2,...] [--jobs N] [--encode OUT.mp4]
  - frames go to OUTDIR/f%04d.png  (keep OUTDIR outside Dropbox: thousands of PNGs)
  - --preview renders only those times to OUTDIR/preview_<t>.png
  - --encode runs ffmpeg (libx264 crf 16, yuv420p, faststart) after rendering
ffmpeg: $FFMPEG, else `ffmpeg` on PATH, else the imageio-ffmpeg binary.
"""
import os, sys, shutil, subprocess


def ffmpeg_exe():
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def encode(framedir, out, fps):
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(framedir, "f%04d.png"),
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("wrote", out)


_FRAME = None


def _init(frame):
    global _FRAME
    _FRAME = frame


def _work(args):
    i, t, path = args
    if not os.path.exists(path):
        _FRAME(t, path)
    return i


def main(frame, t_end, fps, argv=None):
    global _FRAME
    _FRAME = frame
    argv = list(sys.argv[1:] if argv is None else argv)
    out = argv[0]
    os.makedirs(out, exist_ok=True)
    if "--preview" in argv:
        ts = [float(x) for x in argv[argv.index("--preview") + 1].split(",")]
        for t in ts:
            p = os.path.join(out, f"preview_{t:05.1f}.png")
            frame(t, p); print(p)
        return
    n = int(round(t_end * fps))
    lo, hi = 0, n
    for a in argv[1:]:
        if ":" in a and a.replace(":", "").isdigit():
            lo, hi = map(int, a.split(":"))
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 1
    tasks = [(i, i / fps, os.path.join(out, f"f{i:04d}.png")) for i in range(lo, hi)]
    if jobs > 1:
        from multiprocessing import Pool
        # macOS uses 'spawn': globals are not inherited, so hand the frame function to each worker explicitly
        with Pool(jobs, initializer=_init, initargs=(frame,)) as pool:
            for k, _ in enumerate(pool.imap_unordered(_work, tasks, chunksize=4)):
                if k % 200 == 0:
                    print(f"{k}/{len(tasks)}", flush=True)
    else:
        for task in tasks:
            _work(task)
    if "--encode" in argv:
        encode(out, argv[argv.index("--encode") + 1], fps)


# ---------- pauses and music (added 2026-11-08 for the tt̄ v2 video) ----------
def make_warp(holds):
    """holds = [(t_original, seconds), ...] -> (warp(t_out) -> t_original, total_added_seconds).
    Inside a hold the picture is frozen at t_original; draw frames with frame(warp(t_out))."""
    holds = sorted(holds)

    def warp(t):
        shift = 0.0
        for at, d in holds:
            if t - shift <= at:
                break
            if t - shift <= at + d:
                return at
            shift += d
        return t - shift
    return warp, sum(d for _, d in holds)


def add_music(video, music, out=None, fade_in=1.0, fade_out=3.0):
    """mux a music file under the video (cut to the video length, fades), video stream copied."""
    out = out or video.replace(".mp4", "_music.mp4")
    probe = subprocess.run([ffmpeg_exe(), "-i", video], capture_output=True, text=True).stderr
    import re
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe).groups()
    T = int(h) * 3600 + int(m) * 60 + float(s)
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", video, "-i", music, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", f"afade=t=in:d={fade_in},afade=t=out:st={max(T - fade_out, 0):.2f}:d={fade_out}",
                    "-t", f"{T:.2f}", "-movflags", "+faststart", out], check=True)
    print("wrote", out)
    return out
