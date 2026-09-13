import sys
sys.path.insert(0, '.')

from src import upload
from src import script_gen
import json
from pathlib import Path

# Check if there's a pending upload
workdirs = list(Path(r'E:\ai-horror-channel\work').glob('*'))
for wd in workdirs:
    plan_file = wd / 'plan.json'
    if plan_file.exists():
        with open(plan_file) as f:
            plan = json.load(f)
            print('Pending: ' + plan['topic'] + ' in ' + wd.name)
            break
else:
    print('No pending work directories')