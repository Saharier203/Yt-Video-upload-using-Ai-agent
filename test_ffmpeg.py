import subprocess
from pathlib import Path

# Simple test: try to concat two videos with ffmpeg
workdir = Path(r'E:\ai-horror-channel\work\test_ffmpeg')
workdir.mkdir(exist_ok=True)

# Create two simple test videos
for i in range(2):
    out = workdir / f'test_{i}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', f'testsrc=duration=2:size=1080x1920:rate=30',
        '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
        str(out)
    ], check=True, capture_output=True)

# Try to concat them
out_file = workdir / 'concat_test.mp4'
concat_list = workdir / 'concat.txt'
with open(concat_list, 'w') as f:
    f.write("file 'test_0.mp4'\nfile 'test_1.mp4'\n")

result = subprocess.run([
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_list),
    '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
    str(out_file)
], capture_output=True, text=True, cwd=workdir)

print('Return code:', result.returncode)
if result.returncode != 0:
    print('STDERR:', result.stderr[-2000:])
else:
    print('Success! Output:', out_file.exists(), out_file.stat().st_size if out_file.exists() else 'N/A')