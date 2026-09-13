import subprocess
from pathlib import Path

workdir = Path(r'E:\ai-horror-channel\work\test_ffmpeg3')
workdir.mkdir(exist_ok=True)

# Create test clips
for i in range(6):
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
    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=20',
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
"""
for i in range(10):
    start = i * 2.0
    end = start + 1.5
    ass_content += f"Dialogue: 0,{start//60:02.0f}:{start%60:05.2f},{end//60:02.0f}:{end%60:05.2f},Default,,0,0,0,,Caption {i+1}\n"
ass_file.write_text(ass_content, encoding='utf-8-sig')

# Create music
music_mp3 = workdir / 'music.mp3'
subprocess.run([
    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=30',
    '-af', 'volume=-20dB', '-c:a', 'libmp3lame', '-b:a', '96k', str(music_mp3)
], check=True, capture_output=True)

# Create SFX files
sfx_dir = Path(r'E:\ai-horror-channel\assets\sfx')
ambient_bed = sfx_dir / 'ambient_beds' / 'dread_rumble.wav'
atmosphere = sfx_dir / 'atmospheres' / 'hospital' / 'fluo_buzz.wav'
foley = sfx_dir / 'foley' / 'doors' / 'heavy_latch.wav'
tension = sfx_dir / 'tension' / 'sub_rumble_8s.wav'
stinger = sfx_dir / 'stingers' / 'piano_cluster_reverb.wav'

# Copy to workdir if they exist
for src, name in [(ambient_bed, 'ambient_bed.wav'), (atmosphere, 'atmosphere.wav'), 
                  (foley, 'foley.wav'), (tension, 'tension.wav'), (stinger, 'stinger.wav')]:
    if src.exists():
        subprocess.run(['cp', str(src), str(workdir / name)], check=True)

# Build the FULL filter complex similar to assemble.py
w, h, fps = 1080, 1920, 30
td = 0.35
per_clip = 3.5
audio_len = 20.0
total = audio_len + 0.6
n = 6

# Normalize clips
norm_paths = []
for i in range(n):
    norm = workdir / f'norm_{i}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-i', str(workdir / f'clip_{i}.mp4'), '-t', f'{per_clip:.3f}',
        '-vf', f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1',
        '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p', str(norm)
    ], check=True, capture_output=True, cwd=workdir)

# Build filter complex - VIDEO
filters = []
if n == 1:
    filters.append(f"[0:v]ass=subs.ass[v]")
else:
    prev = "[0:v]"
    for i in range(1, n):
        offset = i * (per_clip - 0.35)
        label = f"[x{i}]" if i < n - 1 else "[xv]"
        filters.append(f"{prev}[{i}:v]xfade=transition=fade:duration=0.350:offset={offset:.3f}{label}")
        prev = label
    filters.append(f"[xv]ass=subs.ass[v]")

# AUDIO - Build all the layers
voice_idx = n
args = ['ffmpeg', '-y']
for p in [workdir / f'norm_{i}.mp4' for i in range(n)]:
    args += ['-i', p.name]
args += ['-i', 'voice.mp3']
next_idx = n + 1

mix_sources = [f"[{voice_idx}:a]"]
audio_filters = []

# Ambient bed
if (workdir / 'ambient_bed.wav').exists():
    args += ['-stream_loop', '-1', '-i', 'ambient_bed.wav']
    audio_filters.append(f"[{next_idx}:a]volume=0.08,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[bed_ducked]")
    mix_sources.append("[bed_ducked]")
    next_idx += 1

# Atmosphere
if (workdir / 'atmosphere.wav').exists():
    args += ['-stream_loop', '-1', '-i', 'atmosphere.wav']
    audio_filters.append(f"[{next_idx}:a]volume=0.12,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[atmos_ducked]")
    mix_sources.append("[atmos_ducked]")
    next_idx += 1

# Foley
if (workdir / 'foley.wav').exists():
    args += ['-i', 'foley.wav']
    audio_filters.append(f"[{next_idx}:a]volume=0.10[foley_mixed]")
    mix_sources.append("[foley_mixed]")
    next_idx += 1

# Tension
if (workdir / 'tension.wav').exists():
    args += ['-stream_loop', '-1', '-i', 'tension.wav']
    audio_filters.append(f"[{next_idx}:a]volume=0.08,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[tension_ducked]")
    mix_sources.append("[tension_ducked]")
    next_idx += 1

# Stinger
if (workdir / 'stinger.wav').exists():
    args += ['-i', 'stinger.wav']
    audio_filters.append(f"[{next_idx}:a]volume=0.25[stinger_mixed]")
    mix_sources.append("[stinger_mixed]")
    next_idx += 1

# Music
args += ['-stream_loop', '-1', '-i', 'music.mp3']
audio_filters.append(f"[{next_idx}:a]volume=0.03,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[music_ducked]")
mix_sources.append("[music_ducked]")
next_idx += 1

# Final mix
filters.append(';'.join(audio_filters))
filters.append(f"{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=0:normalize=0[a]")

# Video filters
if n == 1:
    filters.insert(0, f"[0:v]ass=subs.ass[v]")
else:
    prev = "[0:v]"
    for i in range(1, n):
        offset = i * (per_clip - 0.35)
        label = f"[x{i}]" if i < n - 1 else "[xv]"
        filters.insert(i, f"{prev}[{i}:v]xfade=transition=fade:duration=0.350:offset={offset:.3f}{label}")
        prev = label
    filters.insert(n, f"[xv]ass=subs.ass[v]")

# Build final command
out_file = workdir / 'final_test.mp4'
cmd = ['ffmpeg', '-y']
for p in [workdir / f'norm_{i}.mp4' for i in range(n)]:
    cmd += ['-i', p.name]
cmd += ['-i', 'voice.mp3']
# Add audio inputs in the same order they were added above
if (workdir / 'ambient_bed.wav').exists(): cmd += ['-stream_loop', '-1', '-i', 'ambient_bed.wav']
if (workdir / 'atmosphere.wav').exists(): cmd += ['-stream_loop', '-1', '-i', 'atmosphere.wav']
if (workdir / 'foley.wav').exists(): cmd += ['-i', 'foley.wav']
if (workdir / 'tension.wav').exists(): cmd += ['-stream_loop', '-1', '-i', 'tension.wav']
if (workdir / 'stinger.wav').exists(): cmd += ['-i', 'stinger.wav']
cmd += ['-stream_loop', '-1', '-i', 'music.mp3']

cmd += ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-t', f'{20.6:.3f}', 'final_test.mp4']

print('Running ffmpeg with full audio stack...')
result = subprocess.run(['ffmpeg', '-y'] + 
    [str(workdir / f'norm_{i}.mp4') for _ in range(6)] +  # This is wrong, need to rebuild
    ['-i', 'voice.mp3'] +
    (['-stream_loop', '-1', '-i', 'ambient_bed.wav'] if (workdir/'ambient_bed.wav').exists() else []) +
    (['-stream_loop', '-1', '-i', 'atmosphere.wav'] if (workdir/'atmosphere.wav').exists() else []) +
    (['-i', 'foley.wav'] if (workdir/'foley.wav').exists() else []) +
    (['-stream_loop', '-1', '-i', 'tension.wav'] if (workdir/'tension.wav').exists() else []) +
    (['-i', 'stinger.wav'] if (workdir/'stinger.wav').exists() else []) +
    ['-stream_loop', '-1', '-i', 'music.mp3'] +
    ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
     '-c:a', 'aac', '-b:a', '192k', '-t', f'{20.6:.3f}', 'final_test.mp4'],
    cwd=workdir, capture_output=True, text=True, timeout=300)

print('Return code:', result.returncode)
if result.returncode != 0:
    print('STDERR:', result.stderr[-5000:])
else:
    print('Success!')
    out_file = workdir / 'final_test.mp4'
    print('Output exists:', out_file.exists())
    if out_file.exists():
        print('Size:', out_file.stat().st_size)