import subprocess
from pathlib import Path

workdir = Path(r'E:\ai-horror-channel\work\test_ffmpeg2')
workdir.mkdir(exist_ok=True)

# Create test clips
for i in range(3):
    out = workdir / f'clip_{i}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', f'testsrc=duration=3:size=1080x1920:rate=30',
        '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
        str(out)
    ], check=True, capture_output=True)

# Create test audio
voice_mp3 = workdir / 'voice.mp3'
subprocess.run([
    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=10',
    '-c:a', 'libmp3lame', '-b:a', '96k', str(voice_mp3)
], check=True, capture_output=True)

# Create ASS file
ass_file = workdir / 'subs.ass'
ass_content = """[Script Info]
Title: Test
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,92,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,Test caption
Dialogue: 0,0:00:02.00,0:00:04.00,Default,,0,0,0,,Another caption
Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,Final caption
"""
ass_file.write_text(ass_content, encoding='utf-8-sig')

# Create music
music_mp3 = workdir / 'music.mp3'
subprocess.run([
    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=15',
    '-af', 'volume=-20dB', '-c:a', 'libmp3lame', '-b:a', '96k', str(music_mp3)
], check=True, capture_output=True)

# Build the complex ffmpeg command similar to assemble.py
w, h, fps = 1080, 1920, 30
td = 0.35
per_clip = 3.5
total = 10.6

norm_paths = []
for i in range(3):
    norm = workdir / f'norm_{i}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-i', str(workdir / f'clip_{i}.mp4'), '-t', f'{per_clip:.3f}',
        '-vf', f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1',
        '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p', str(norm)
    ], check=True, capture_output=True, cwd=workdir)
    norm_paths.append(norm)

# Build filter complex
n = 3
filters = []
prev = "[0:v]"
for i in range(1, n):
    offset = i * (per_clip - td)
    label = f"[x{i}]" if i < n - 1 else "[xv]"
    filters.append(f"{prev}[{i}:v]xfade=transition=fade:duration={td:.3f}:offset={offset:.3f}{label}")
    prev = label
filters.append(f"[xv]ass={Path('subs.ass').name}[v]")

# Audio mix
voice_idx = n
music_idx = n + 1
mix_sources = [f"[{voice_idx}:a]"]
filters.append(f"[{music_idx}:a]volume=0.03,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[music_ducked]")
mix_sources.append("[music_ducked]")
filters.append(f"{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=0:normalize=0[a]")

out_file = workdir / 'final_test.mp4'
args = ['ffmpeg', '-y']
for p in norm_paths:
    args += ['-i', p.name]
args += ['-i', 'voice.mp3']
args += ['-stream_loop', '-1', '-i', 'music.mp3']
args += ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-t', f'{total:.3f}', 'final_test.mp4']

print('Running ffmpeg...')
result = subprocess.run(args, cwd=workdir, capture_output=True, text=True, timeout=120)
print('Return code:', result.returncode)
if result.returncode != 0:
    print('STDERR:', result.stderr[-3000:])
else:
    print('Success!')
    out_file = workdir / 'final_test.mp4'
    print('Output exists:', out_file.exists())
    if out_file.exists():
        print('Size:', out_file.stat().st_size)