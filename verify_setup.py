import os
import subprocess
import sys

print("===========================================")
print("  AI HORROR CHANNEL - SETUP VERIFICATION")
print("===========================================")
print()

# Check prerequisites
checks = {
    "Python": "python --version",
    "FFmpeg": "ffmpeg -version",
    "Node": "node --version",
    "Git": "git --version"
}

for name, cmd in checks.items():
    try:
        result = subprocess.run(cmd.split(), capture_output=True, timeout=5)
        if result.returncode == 0:
            print("  [OK] {} found".format(name))
        else:
            print("  [MISSING] {} MISSING".format(name))
    except:
        print("  [MISSING] {} MISSING".format(name))

print()

# Check .env
if os.path.exists(".env"):
    with open(".env") as f:
        content = f.read()
    gemini_ok = "GEMINI_API_KEY=AIza" in content
    pexels_ok = "PEXELS_API_KEY=" in content and "YOUR_PEXELS" not in content
    print("  [{}] GEMINI_API_KEY configured".format("OK" if gemini_ok else "MISSING"))
    print("  [{}] PEXELS_API_KEY configured".format("OK" if pexels_ok else "MISSING"))
else:
    print("  [MISSING] .env file not found")

print()

# Check OAuth
print("  [{}] client_secret.json".format("OK" if os.path.exists("client_secret.json") else "MISSING"))
print("  [{}] token.json (run authorize.py if missing)".format("OK" if os.path.exists("token.json") else "WARNING"))

print()

# Check assets
music_size = os.path.getsize("assets/background_music.mp3") if os.path.exists("assets/background_music.mp3") else 0
print("  [{}] background_music.mp3 ({:.1f} MB)".format("OK" if music_size > 1000000 else "MISSING", music_size/1024/1024))
print("  [{}] font.ttf".format("OK" if os.path.exists("assets/font.ttf") else "MISSING"))

print()

# Check Python packages
try:
    import edge_tts
    import requests
    import google.api_core
    import google.auth
    import googleapiclient.discovery
    print("  [OK] All Python packages installed")
except Exception as e:
    print("  [MISSING] Missing packages: {}".format(e))

print()

# Check Remotion
print("  [{}] Remotion installed".format("OK" if os.path.exists("remotion/node_modules") else "MISSING"))

print()
print("===========================================")
print("  VERIFICATION COMPLETE")
print("===========================================")