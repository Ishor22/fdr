#!/usr/bin/env python3
"""Build the HamroTask YouTube intro from procedural backgrounds, on-screen text,
a synthesized music bed and an ElevenLabs narration file.

Usage: python3 build.py <voice.mp3> <out_dir>
Requires ffmpeg with drawtext, gradients, sidechaincompress and alimiter.
"""
import os
import subprocess
import sys

W, H, FPS = 1920, 1080, 30
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

VOICE, OUT = sys.argv[1], sys.argv[2]
WORK = os.path.join(OUT, "_work")
os.makedirs(WORK, exist_ok=True)


def run(args):
    subprocess.run(args, check=True)


def esc(text):
    # drawtext text= value; the value is single-quoted in the graph, so only ':' and "'" need care
    return text.replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def fade_alpha(start, end, fin=0.5, fout=0.5):
    # alpha expression, single-quoted in the graph so its commas are safe
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


# Scene table: duration, gradient colours (c0, c1), speed, texts
# text tuple: (string, start, end, y, size, font, colour) — times are scene-relative.
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
        ("No guaranteed earnings. Rewards depend on activity and platform rules.",
         0.5, 17.6, 900, 30, "r", "0xbfe9e0"),
    ]),
    dict(name="s5_cta", dur=15, c0="0x07131f", c1="0x164e63", speed=0.04, texts=[
        ("Start Your Journey Today", 0.4, 14.6, 380, 96, "b", "white"),
        ("Visit: hamrotask.com", 3.0, 14.6, 540, 56, "b", "0x7fc4ae"),
        ("Support: HamroTask@gmail.com", 5.6, 14.6, 640, 44, "r", "0xbfe9e0"),
    ]),
]
TOTAL = sum(s["dur"] for s in SCENES)


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
    out = os.path.join(WORK, "video_silent.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", out])
    return out


def music_bed(dur):
    # Synthesized pad (not licensed music): C - Am - F - G, one chord per quarter of the runtime,
    # soft tremolo, fade in and out. Stereo with a slight detune between channels.
    out = os.path.join(WORK, "music.wav")
    chords = [
        [130.81, 164.81, 196.00],   # C major
        [110.00, 130.81, 164.81],   # A minor
        [87.31, 110.00, 130.81],    # F major
        [98.00, 123.47, 146.83],    # G major
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


def main():
    total = TOTAL
    scene_paths = [build_scene(s) for s in SCENES]
    video = concat_video(scene_paths)
    music = music_bed(total)

    # Voice: pad/trim to scene length; add 0.6 s lead-in; loudness-normalize narration.
    voice_proc = os.path.join(WORK, "voice_norm.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", VOICE,
         "-af", "adelay=600|600,aformat=sample_rates=44100:channel_layouts=stereo,"
                "loudnorm=I=-16:TP=-1.5:LRA=11,apad",
         "-t", str(total), voice_proc])

    # Mix: music ducked under voice (sidechain), then limiter and stereo AAC.
    final = os.path.join(OUT, "hamrotask-youtube-intro.mp4")
    mix = (
        "[1:a]volume=0.9,asplit=2[vo1][vo2];"
        "[2:a]volume=0.35[mu];"
        "[mu][vo1]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];"
        "[vo2][duck]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.89[a]"
    )
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-i", video, "-i", voice_proc, "-i", music,
         "-filter_complex", mix,
         "-map", "0:v:0", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "-shortest", final])
    print("wrote", final)


if __name__ == "__main__":
    main()
