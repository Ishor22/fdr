#!/usr/bin/env python3
"""HamroTask promotional intro: five 1920x1080 / 30 fps scenes, 75 seconds.

Visuals: procedural cinematic gradients, on-screen titles, fade transitions,
vignette and film grain, burned-in subtitles.
Audio: synthesized music bed with transition whooshes; optional narration with
automatic ducking (used once narration is available).

Usage:
  python3 build.py <out_dir>                 # silent narration, subtitles timed to the scene plan
  python3 build.py <out_dir> <voice.mp3>     # adds narration with music ducking

The subtitles are timed to the planned scene timeline, not to speech.
Timings are reported as estimates in the QC report.
"""
import os
import subprocess
import sys

W, H, FPS = 1920, 1080, 30
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
HERE = os.path.dirname(os.path.abspath(__file__))

OUT = sys.argv[1]
VOICE = sys.argv[2] if len(sys.argv) > 2 else None
WORK = os.path.join(OUT, "_work")
os.makedirs(WORK, exist_ok=True)


def run(args):
    subprocess.run(args, check=True)


def esc(text):
    # drawtext text value, single-quoted in the graph
    return text.replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def fade_alpha(start, end, fin=0.5, fout=0.5):
    a, b = start, end
    return (
        f"if(lt(t,{a}),0,if(lt(t,{a + fin}),(t-{a})/{fin},"
        f"if(lt(t,{b - fout}),1,if(lt(t,{b}),({b}-t)/{fout},0))))"
    )


def text_filter(item):
    t, start, end, y, size, font, color = item
    f = FONT_B if font == "b" else FONT_R
    return (
        f"drawtext=fontfile={f}:text='{esc(t)}':fontcolor={color}:fontsize={size}"
        f":x=(w-text_w)/2:y={y}:alpha='{fade_alpha(start, end)}'"
    )


# ---------------------------------------------------------------- scene plan
# Each scene: duration (s), background gradient, speed, on-screen titles.
# Titles: (text, start, end, y, size, font, colour) with scene-relative times.
SCENES = [
    dict(name="s1_open", dur=8, c0="0x07131f", c1="0x0f4c5c", speed=0.04, texts=[
        ("HamroTask", 0.3, 7.7, 400, 150, "b", "white"),
        ("Your Time. Your Skills. Your Rewards.", 2.4, 7.7, 600, 46, "r", "0xbfe9e0"),
    ]),
    dict(name="s2_intro", dur=10, c0="0x0b1a2e", c1="0x1d5c7a", speed=0.03, texts=[
        ("An online platform to earn rewards by completing tasks", 0.5, 9.6, 380, 52, "b", "white"),
        ("Create an account and explore what is available", 3.0, 9.6, 500, 36, "r", "0xbfe9e0"),
        ("hamrotask.com", 5.0, 9.6, 640, 40, "b", "0x7fc4ae"),
    ]),
    dict(name="s3_features", dur=24, c0="0x101c2c", c1="0x2b4f6e", speed=0.05, texts=[
        ("Available Tasks", 0.2, 3.2, 480, 86, "b", "white"),
        ("Login Bonus", 3.6, 6.6, 480, 86, "b", "white"),
        ("My Workers", 7.0, 10.0, 480, 86, "b", "white"),
        ("Worker Commission", 10.4, 13.4, 480, 86, "b", "white"),
        ("Lucky Draw", 13.8, 16.8, 480, 86, "b", "white"),
        ("Reward Points", 17.2, 20.2, 480, 86, "b", "white"),
        ("Live Activity", 20.6, 23.6, 480, 86, "b", "white"),
    ]),
    dict(name="s4_how", dur=18, c0="0x0c1f1b", c1="0x1f5a4c", speed=0.035, texts=[
        ("1  Register an account", 0.3, 3.5, 420, 70, "b", "white"),
        ("2  Explore available tasks", 3.8, 7.0, 420, 70, "b", "white"),
        ("3  Complete eligible activities", 7.3, 10.5, 420, 70, "b", "white"),
        ("4  Earn rewards per platform rules", 10.8, 14.0, 420, 70, "b", "white"),
        ("5  Explore more platform features", 14.3, 17.6, 420, 70, "b", "white"),
    ]),
    dict(name="s5_cta", dur=15, c0="0x07131f", c1="0x164e63", speed=0.04, texts=[
        ("Start Your Journey Today", 0.4, 14.6, 380, 96, "b", "white"),
        ("Visit: hamrotask.com", 3.0, 14.6, 540, 56, "b", "0x7fc4ae"),
        ("Support: HamroTask@gmail.com", 5.6, 14.6, 640, 44, "r", "0xbfe9e0"),
    ]),
]
TOTAL = sum(s["dur"] for s in SCENES)
STARTS = [sum(s["dur"] for s in SCENES[:i]) for i in range(len(SCENES))]

# Narration script blocks, by scene: (scene index, scene-relative start, end, text).
# Subtitles are spread across each block by character count. This is an estimate,
# because there is no speech audio to time against yet.
SUB_BLOCKS = [
    (0, 0.4, 7.6, "HamroTask. Your time. Your skills. Your rewards."),
    (1, 0.6, 9.4, "HamroTask is an online platform where you can earn rewards by completing tasks. "
                  "Create an account at hamrotask.com and explore what is available."),
    (2, 0.6, 23.4, "Inside, you will find available tasks, a daily login bonus and a Lucky Draw. "
                   "Build your team with My Workers and earn Worker Commission. "
                   "Collect Reward Points and follow Live Activity across the platform."),
    (3, 0.6, 17.4, "Here is how it works. First, register your account. Second, explore the available tasks. "
                   "Third, complete the activities you are eligible for. Fourth, earn rewards according to the "
                   "platform rules. Rewards depend on your activity and the rules in place, so there are no "
                   "guaranteed earnings."),
    (4, 0.6, 14.4, "Start your journey today. Visit hamrotask.com. "
                   "For support, email HamroTask@gmail.com."),
]


def srt_time(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_sentences(text):
    # Split only where punctuation is followed by a space or the end, so "gmail.com" stays whole.
    parts, cur = [], ""
    for i, ch in enumerate(text):
        cur += ch
        at_end = i + 1 == len(text)
        if ch in ".?!" and (at_end or text[i + 1] == " ") and len(cur.strip()) > 1:
            parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    return parts


def write_srt(path):
    cues = []
    for scene_i, a, b, text in SUB_BLOCKS:
        base = STARTS[scene_i]
        sents = split_sentences(text)
        total_chars = sum(len(x) for x in sents)
        t = base + a
        span = (base + b) - t
        for s in sents:
            d = span * len(s) / total_chars
            cues.append((t, t + d, s))
            t += d
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, s) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    return path


# ---------------------------------------------------------------- video build
def build_scene(s):
    out = os.path.join(WORK, s["name"] + ".mp4")
    vf = [f"fade=t=in:st=0:d=0.6", f"fade=t=out:st={s['dur'] - 0.6}:d=0.6"]
    vf += [text_filter(t) for t in s["texts"]]
    graph = (
        f"gradients=s={W}x{H}:c0={s['c0']}:c1={s['c1']}:speed={s['speed']}"
        f":duration={s['dur']}:rate={FPS},format=yuv420p,"
        + ",".join(vf)
    )
    run(["ffmpeg", "-y", "-loglevel", "error", "-filter_complex", graph,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", str(FPS), out])
    return out


def concat_video(paths):
    lst = os.path.join(WORK, "scenes.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    out = os.path.join(WORK, "video_base.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", out])
    return out


def srt_to_ass(srt_path, ass_path):
    """Convert SRT cues to ASS on a 1920x1080 canvas so the font size is literal."""
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {W}\nPlayResY: {H}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Sub,DejaVu Sans,40,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "0,0,0,0,100,100,0,0,1,3,0,2,120,120,60,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    def ass_time(sec):
        cs = int(round(sec * 100))
        h, cs = divmod(cs, 360000)
        m, cs = divmod(cs, 6000)
        s, cs = divmod(cs, 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    blocks = open(srt_path, encoding="utf-8").read().strip().split("\n\n")
    lines = []
    for blk in blocks:
        parts = blk.split("\n")
        start, end = parts[1].split(" --> ")
        text = " ".join(parts[2:])
        def to_sec(ts):
            hms, ms = ts.replace(".", ",").split(",")
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        lines.append(f"Dialogue: 0,{ass_time(to_sec(start))},{ass_time(to_sec(end))},Sub,,0,0,0,,{text}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")
    return ass_path


def grade_and_subtitle(video_in, srt, out):
    """Cinematic grade (vignette, film grain, slight contrast) and burned-in subtitles."""
    ass = srt_to_ass(srt, os.path.join(WORK, "subtitles.ass"))
    vf = (
        "vignette=PI/5,"
        "noise=alls=3:allf=t,"
        "eq=contrast=1.04:saturation=1.05,"
        f"subtitles={ass}"
    )
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video_in, "-vf", vf,
         "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-an", out])
    return out


# ---------------------------------------------------------------- audio build
def music_bed(dur):
    # Synthesized pad, not licensed music: C - Am - F - G, one chord per quarter of the runtime.
    out = os.path.join(WORK, "music.wav")
    chords = [
        [130.81, 164.81, 196.00],
        [110.00, 130.81, 164.81],
        [87.31, 110.00, 130.81],
        [98.00, 123.47, 146.83],
    ]
    seg = dur / 4.0

    def chord_expr(detune):
        e = "0"
        for i in reversed(range(4)):
            body = "+".join(f"sin(2*PI*{f * detune}*t)" for f in chords[i])
            e = f"if(lt(t,{seg * (i + 1)}),{body},{e})"
        env = f"min(1,t/2)*min(1,({dur}-t)/3)*(0.7+0.3*sin(2*PI*0.5*t))"
        return f"0.04*({e})*{env}"

    left, right = chord_expr(1.0), chord_expr(1.002)
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", f"aevalsrc='{left}|{right}':s=44100:d={dur}",
         "-c:a", "pcm_s16le", out])
    return out


def whoosh():
    # Synthesized transition whoosh: filtered pink noise with a rising band-pass.
    out = os.path.join(WORK, "whoosh.wav")
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "anoisesrc=d=1.0:c=pink:r=44100:a=0.5",
         "-af", "afade=t=in:st=0:d=0.45,afade=t=out:st=0.45:d=0.55,"
                "highpass=f=250,lowpass=f=5000,volume=0.6,"
                "aformat=channel_layouts=stereo",
         "-c:a", "pcm_s16le", out])
    return out


def final_mix(video, out, voice=None):
    music = music_bed(TOTAL)
    wh = whoosh()
    # Transition points: start of scenes 2..5 (the first scene starts silently).
    hits = STARTS[1:]
    inputs = ["-i", video, "-i", music]
    graph = []
    mu_chain = "[1:a]volume=0.45[mu];"
    graph.append("[1:a]volume=1.6[mu];")  # synthesized pad is quiet; raised to a listenable bed
    n = len(hits)
    graph.append(f"[2:a]asplit={n}" + "".join(f"[w{i}]" for i in range(n)) + ";")
    inputs += ["-i", wh]
    sfx_labels = []
    for i, t in enumerate(hits):
        ms = int(round(t * 1000))
        graph.append(f"[w{i}]adelay={ms}|{ms},volume=0.8[s{i}];")
        sfx_labels.append(f"[s{i}]")
    if voice:
        inputs += ["-i", voice]
        vi = len(inputs) // 2 - 1
        graph.append(f"[{vi}:a]apad=whole_dur={TOTAL},asplit=2[vo1][vo2];")
        graph.append("[mu][vo1]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];")
        mix_inputs = "[vo2][duck]" + "".join(sfx_labels)
        graph.append(f"{mix_inputs}amix=inputs={2 + len(sfx_labels)}:duration=first:normalize=0,"
                     "alimiter=limit=0.89[a]")
    else:
        graph.append("[mu]" + "".join(sfx_labels)
                     + f"amix=inputs={1 + len(sfx_labels)}:duration=first:normalize=0,"
                       "alimiter=limit=0.89[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
         "-filter_complex", "".join(graph),
         "-map", "0:v:0", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
         "-t", str(TOTAL), "-movflags", "+faststart", out])
    return out


def main():
    scene_paths = [build_scene(s) for s in SCENES]
    base = concat_video(scene_paths)
    srt_path = write_srt(os.path.join(OUT, "hamrotask-subtitles.srt"))
    graded = grade_and_subtitle(base, srt_path, os.path.join(WORK, "video_graded.mp4"))
    final = os.path.join(OUT, "hamrotask-youtube-intro.mp4")
    final_mix(graded, final, voice=VOICE)
    print("wrote", final, "and", srt_path)


if __name__ == "__main__":
    main()
