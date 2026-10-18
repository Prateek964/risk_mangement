"""Mix the narration with the sound-effect cues written by build.py.

Usage: mix.py questions/qNNN.json build/qNNN-sfx.json <out.mp3>
Each SFX file is trimmed of trailing silence and placed at its cue time at the cue gain.
"""
import json, subprocess, sys

Q = json.load(open(sys.argv[1]))
cues = json.load(open(sys.argv[2]))
out = sys.argv[3]
ROOT = __file__.rsplit("/tools/", 1)[0]

inputs = ["-i", Q["audio"]]
names = sorted({c["sfx"] for c in cues})
for n in names:
    inputs += ["-i", f"{ROOT}/sfx/{n}.mp3"]
idx = {n: i + 1 for i, n in enumerate(names)}

parts, labels = [], []
# split each sfx source into as many copies as it has cues
uses = {n: [c for c in cues if c["sfx"] == n] for n in names}
for n in names:
    k = len(uses[n])
    clean = f"[{idx[n]}:a]silenceremove=stop_periods=-1:stop_duration=0.15:stop_threshold=-50dB,afade=t=out:st=1.4:d=0.4,aresample=44100,aformat=channel_layouts=stereo"
    parts.append(f"{clean},asplit={k}" + "".join(f"[{n}{j}]" for j in range(k)) if k > 1 else f"{clean}[{n}0]")
    for j, c in enumerate(uses[n]):
        ms = int(c["t"] * 1000)
        parts.append(f"[{n}{j}]volume={c['gain_db']}dB,adelay={ms}|{ms}[{n}d{j}]")
        labels.append(f"[{n}d{j}]")
parts.append("[0:a]aresample=44100,aformat=channel_layouts=stereo[vo]")
parts.append(f"[vo]{''.join(labels)}amix=inputs={len(labels) + 1}:normalize=0:duration=longest,alimiter=limit=0.95[mix]")
cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts), "-map", "[mix]", "-c:a", "libmp3lame", "-b:a", "192k", out]
subprocess.run(cmd, check=True)
print(f"mixed {len(cues)} cues into {out}")
