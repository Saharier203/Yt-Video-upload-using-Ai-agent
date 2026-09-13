import os
import subprocess
import sys

print("===========================================")
print("  AI HORROR CHANNEL - DRY RUN TEST")
print("===========================================")
print()

# Verify .env has real keys
if not os.path.exists(".env"):
    print("ERROR: .env not found")
    sys.exit(1)

with open(".env") as f:
    env = f.read()

if "YOUR_GEMINI_API_KEY_HERE" in env:
    print("ERROR: .env still has placeholder Gemini key")
    print("Edit .env and add your real key from https://aistudio.google.com/apikey")
    sys.exit(1)

if "YOUR_PEXELS_API_KEY_HERE" in env:
    print("ERROR: .env still has placeholder Pexels key")
    print("Edit .env and add your real key from https://www.pexels.com/api/")
    sys.exit(1)

if not os.path.exists("client_secret.json"):
    print("ERROR: client_secret.json not found")
    print("Download from Google Cloud Console > Credentials > OAuth Client ID > Desktop App")
    sys.exit(1)

if not os.path.exists("token.json"):
    print("WARNING: token.json not found - you need to authorize first")
    print("Run: python authorize.py")
    print("Then re-run this test")
    sys.exit(1)

print("All credentials verified. Starting dry run...")
print()

# Run dry run
result = subprocess.run([sys.executable, "run_daily.py", "--no-upload"], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

if result.returncode == 0:
    print()
    print("===========================================")
    print("  DRY RUN SUCCESSFUL!")
    print("===========================================")
    
    # Check output
    if os.path.exists("output"):
        videos = [f for f in os.listdir("output") if f.endswith(".mp4")]
        print("Generated videos in output/:")
        for v in videos:
            size = os.path.getsize(os.path.join("output", v)) / 1024 / 1024
            print("  - {} ({:.1f} MB)".format(v, size))
    
    print()
    print("NEXT STEPS:")
    print("1. Full test upload (private): python run_daily.py")
    print("2. Install scheduler (Admin): powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1")
else:
    print()
    print("===========================================")
    print("  DRY RUN FAILED")
    print("===========================================")
    print("Check logs/ for details")