import sys
sys.path.insert(0, r'E:\ai-horror-channel')

import json
from src import assemble
from pathlib import Path

# Load config
with open(r'E:\ai-horror-channel\config.json', 'r') as f:
    cfg = json.load(f)

# Find latest work directory
workdirs = list(Path(r'E:\ai-horror-channel\work').glob('20260911_18*'))
latest = max(workdirs, key=lambda p: p.stat().st_mtime)
workdir = latest

print(f"Using workdir: {workdir}")

raw_clips = sorted(workdir.glob('raw_*.mp4'))
voice_mp3 = workdir / 'voice.mp3'
ass_file = workdir / 'subs.ass'

print(f"Raw clips: {len(raw_clips)}")
print(f"Voice: {voice_mp3.exists()}")
print(f"ASS: {ass_file.exists()}")

with open(workdir / 'plan.json', 'r') as f:
    plan = json.load(f)

print(f"Plan topic: {plan['topic']}")
print(f"Music mood: {plan.get('music_mood')}")

OUT_DIR = Path(r'E:\ai-horror-channel\output')
out_file = OUT_DIR / "short_debug_test.mp4"

print("\nCalling assemble.build_video...")
try:
    result = assemble.build_video(
        raw_clips=raw_clips,
        voice_mp3=workdir / 'voice.mp3',
        ass_file=ass_file,
        config=cfg,
        workdir=workdir,
        out_file=out_file,
        music_mood=plan.get("music_mood"),
        words=None,
        hook=None,
        script=plan.get("script"),
        scene_prompts=plan.get("scene_prompts")
    )
    print(f"Result: {result}")
    print(f"Output exists: {out_file.exists()}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()