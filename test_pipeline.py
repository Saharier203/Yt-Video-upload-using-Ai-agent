import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

from src import script_gen, tts, captions, visuals, assemble
import json
from pathlib import Path

# Load config
with open('config.json') as f:
    cfg = json.load(f)

# Quick test: generate a script
print('Testing script generation...')
plan = script_gen.generate_video_plan(cfg, forced_topic='Test UFO sighting 1993')
print('Topic:', plan['topic'])
print('Title:', plan['title'])
print('Script length:', len(plan['script']), 'chars')
print('Script preview:', plan['script'][:200])