import sys
sys.path.insert(0, '.')

from src import upload, script_gen
import json
from pathlib import Path

with open('config.json') as f:
    cfg = json.load(f)

# Check for video file
wd = Path(r'E:\ai-horror-channel\work\20260911_172731')
video_files = list(wd.glob('*.mp4'))
if video_files:
    video_file = max(video_files, key=lambda f: f.stat().st_size)
    print('Video file:', video_file.name, video_file.stat().st_size / 1024 / 1024, 'MB')
    
    plan_file = wd / 'plan.json'
    with open(plan_file) as f:
        plan = json.load(f)
    
    print('Uploading:', plan['topic'])
    url = upload.upload_video(video_file, plan, cfg)
    print('Upload result:', url)
else:
    print('No video file found')