#!/usr/bin/env python3
"""
Dark Archives - Interactive Horror Video Generator
Run: python run_interactive.py
"""
import sys
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def run_command(cmd, description):
    """Run a command and show live output."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        # Run with live output
        proc = subprocess.Popen(cmd, cwd=PROJECT_ROOT)
        proc.wait()
        if proc.returncode == 0:
            print(f"\n✓ {description} completed successfully!")
        else:
            print(f"\n✗ {description} failed (exit code: {proc.returncode})")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n✗ Error: {e}")

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("   DARK ARCHIVES - HORROR VIDEO GENERATOR")
        print("=" * 60)
        print()
        print("  [1] Short (45 sec, 9:16 vertical)  → YouTube #Shorts")
        print("  [2] Long-form (8-10 min, 16:9)     → Deep dive")
        print("  [3] Test run (dry run, no upload)")
        print("  [4] Check pending uploads")
        print("  [5] View upload history")
        print("  [0] Exit")
        print()
        
        try:
            choice = input("Enter choice [0-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break
        
        if choice == "1":
            run_command([sys.executable, "run_daily.py"], "Generating SHORT video (45 sec, 9:16)")
        elif choice == "2":
            run_command([sys.executable, "run_weekly.py"], "Generating LONG-FORM video (8-10 min, 16:9)")
        elif choice == "3":
            run_command([sys.executable, "run_daily.py", "--no-upload"], "DRY RUN (no upload)")
        elif choice == "4":
            check_pending()
        elif choice == "5":
            show_history()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            input("\nInvalid choice. Press Enter to continue...")

def check_pending():
    """Check for videos waiting to upload."""
    from pathlib import Path
    import json
    
    work_root = Path("work")
    if not work_root.exists():
        print("\nNo pending work directories.")
        return
    
    pending = []
    for wd in work_root.iterdir():
        plan_file = wd / "plan.json"
        if plan_file.exists():
            try:
                with open(plan_file) as f:
                    plan = json.load(f)
                video_files = list(wd.glob("*.mp4"))
                if video_files:
                    vf = max(video_files, key=lambda f: f.stat().st_size)
                    pending.append((plan['topic'], wd.name, vf.stat().st_size / 1024 / 1024))
            except:
                pass
    
    if pending:
        print(f"\n{'='*60}")
        print(f"  PENDING UPLOADS ({len(pending)})")
        print(f"{'='*60}")
        for topic, stamp, size in pending:
            print(f"  • {topic}")
            print(f"    Work dir: {stamp} | Video: {size:.1f} MB")
    else:
        print("\nNo pending uploads.")
    input("\nPress Enter to continue...")

def show_history():
    """Show upload history."""
    from pathlib import Path
    import json
    
    history_file = Path("data/topics_history.json")
    if not history_file.exists():
        print("\nNo history yet.")
        return
    
    try:
        with open(history_file) as f:
            history = json.load(f)
    except:
        print("\nCould not read history.")
        return
    
    if not history:
        print("\nNo history yet.")
        return
    
    print(f"\n{'='*60}")
    print(f"  UPLOAD HISTORY ({len(history)} videos)")
    print(f"{'='*60}")
    for entry in reversed(history[-20:]):  # Show last 20
        url_status = "✓ Uploaded" if entry.get('url') else "✗ Not uploaded"
        print(f"  {entry['date']} | {entry['topic'][:50]}")
        print(f"    {entry['title'][:60]} | {url_status}")
        if entry.get('url'):
            print(f"    {entry['url']}")
    if len(history) > 20:
        print(f"\n  ... and {len(history) - 20} more")
    input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Ensure we're in project root
    os.chdir(Path(__file__).parent)
    main()