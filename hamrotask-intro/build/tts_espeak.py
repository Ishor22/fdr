#!/usr/bin/env python3
"""Free offline narration with espeak-ng (temporary voice, not ElevenLabs).

Each sentence is synthesized separately, its real duration is measured with
ffprobe, and it is placed inside its scene window. Subtitle cues are written
from those measured times, so they follow the actual speech.

Usage: python3 tts_espeak.py <out_dir>
Writes: <out_dir>/_work/voice_espeak.wav and <out_dir>/hamrotask-subtitles.srt
"""
import importlib.util
import json
import os
import subprocess
import sys

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(OUT, "_work")
os.makedirs(WORK, exist_ok=True)

# Load the scene plan and subtitle blocks from build.py without running its main().
sys.argv = ["build.py", OUT]
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "build.py"))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

VOICE = "en-us+f3"
SPEED = os.environ.get("ESPEAK_WPM", "150")   # words per minute


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


clips = []  # (start_sec, path, text)
manifest = []
sentences = []
for scene_i, a, bnd, text in b.SUB_BLOCKS:
    for n, sent in enumerate(b.split_sentences(text)):
        wav = os.path.join(WORK, f"tts_{scene_i}_{n}.wav")
        subprocess.run(["espeak-ng", "-v", VOICE, "-s", SPEED, "-w", wav, sent], check=True)
        sentences.append((scene_i, sent, wav, duration(wav)))

# One continuous sequence from 0.6 s, with a short gap between sentences.
GAP, LEAD = 0.25, 0.6
cursor = LEAD
for scene_i, sent, wav, d in sentences:
    clips.append((cursor, wav, sent))
    manifest.append({"scene": scene_i, "start": round(cursor, 3),
                     "end": round(cursor + d, 3), "text": sent})
    cursor += d + GAP
if cursor - GAP > b.TOTAL - 0.5:
    raise SystemExit(f"Narration runs {cursor - GAP:.1f}s, longer than {b.TOTAL}s. Raise the speed.")
print(f"speech spans 0.6s to {cursor - GAP:.1f}s of {b.TOTAL}s")

# Mix all sentence clips at their start times into one stereo track.
inputs, parts = [], []
for i, (start, wav, _) in enumerate(clips):
    inputs += ["-i", wav]
    ms = int(round(start * 1000))
    parts.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                 f"adelay={ms}|{ms},volume=1.0[c{i}]")
mix_in = "".join(f"[c{i}]" for i in range(len(clips)))
graph = ";".join(parts) + f";{mix_in}amix=inputs={len(clips)}:normalize=0:duration=longest,"\
        f"loudnorm=I=-16:TP=-1.5:LRA=11,atrim=0:{b.TOTAL}[v]"
voice_out = os.path.join(WORK, "voice_espeak.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                "-filter_complex", graph, "-map", "[v]", "-ac", "2", "-ar", "44100",
                voice_out], check=True)

# Subtitles from the measured times.
srt = os.path.join(OUT, "hamrotask-subtitles.srt")
with open(srt, "w", encoding="utf-8") as f:
    for i, m in enumerate(manifest, 1):
        f.write(f"{i}\n{b.srt_time(m['start'])} --> {b.srt_time(m['end'])}\n{m['text']}\n\n")
with open(os.path.join(WORK, "timings.json"), "w") as f:
    json.dump(manifest, f, indent=1)
print("voice:", voice_out, "cues:", len(manifest))
