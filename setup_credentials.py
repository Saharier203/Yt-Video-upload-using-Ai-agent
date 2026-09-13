import os
import sys
import subprocess
import webbrowser

def print_header(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def open_url(url):
    print(f"Opening: {url}")
    webbrowser.open(url)

def get_input(prompt, secret=False):
    if secret:
        import getpass
        return getpass.getpass(prompt + " ")
    return input(prompt + " ").strip()

def update_env(key, value):
    env_path = "E:\\ai-horror-channel\\.env"
    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()
    
    found = False
    for i, line in enumerate(lines):
        if line.startswith(key + "="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    
    if not found:
        lines.append(f"{key}={value}\n")
    
    with open(env_path, "w") as f:
        f.writelines(lines)
    print(f"  ✓ Updated {key}")

def main():
    print_header("AI HORROR CHANNEL - CREDENTIAL SETUP WIZARD")
    print("This will help you add the required API keys to .env")
    print("You'll need to get keys from 2 free services.\n")
    
    # Step 1: Gemini
    print_header("STEP 1: GEMINI API KEY (Required)")
    print("Free tier: 1,500 requests/day")
    if input("Open Gemini AI Studio now? (y/n): ").lower() == 'y':
        open_url("https://aistudio.google.com/apikey")
    
    print("\nInstructions:")
    print("1. Sign in with Google")
    print("2. Click 'Create API Key'")
    print("3. Copy the key (starts with AIzaSy...)")
    print("4. Paste it below\n")
    
    gemini_key = get_input("Paste your Gemini API key:", secret=True)
    if gemini_key and gemini_key.startswith("AIza"):
        update_env("GEMINI_API_KEY", gemini_key)
    else:
        print("  ⚠ Key doesn't look valid (should start with AIza). Skipping.")
    
    # Step 2: Pexels
    print_header("STEP 2: PEXELS API KEY (Required)")
    print("Free tier: 200 requests/hour")
    if input("Open Pexels API page now? (y/n): ").lower() == 'y':
        open_url("https://www.pexels.com/api/")
    
    print("\nInstructions:")
    print("1. Create free account / sign in")
    print("2. Generate API key")
    print("3. Copy the key")
    print("4. Paste it below\n")
    
    pexels_key = get_input("Paste your Pexels API key:", secret=True)
    if pexels_key and len(pexels_key) > 10:
        update_env("PEXELS_API_KEY", pexels_key)
    else:
        print("  ⚠ Key seems too short. Skipping.")
    
    # Step 3: Google Cloud
    print_header("STEP 3: GOOGLE CLOUD OAUTH (Required for Upload)")
    print("This enables YouTube uploads")
    if input("Open Google Cloud Console now? (y/n): ").lower() == 'y':
        open_url("https://console.cloud.google.com/")
    
    print("\nInstructions:")
    print("1. Create project 'AI Horror Channel'")
    print("2. APIs & Services > Library > Enable:")
    print("   - YouTube Data API v3")
    print("   - YouTube Analytics API")
    print("3. OAuth Consent Screen > External > Add your email")
    print("4. Credentials > Create > OAuth Client ID > Desktop App")
    print("5. Download JSON > Save as client_secret.json in project folder")
    print("\nFile must be at: E:\\ai-horror-channel\\client_secret.json")
    
    input("\nPress Enter when client_secret.json is in place...")
    
    if os.path.exists("E:\\ai-horror-channel\\client_secret.json"):
        print("  ✓ client_secret.json found")
    else:
        print("  ⚠ File not found at expected location")
    
    # Step 4: Authorize
    print_header("STEP 4: AUTHORIZE YOUTUBE CHANNEL")
    print("This opens a browser to sign in as YOUR CHANNEL")
    if input("Run authorization now? (y/n): ").lower() == 'y':
        print("\nOpening browser... Sign in as your YOUTUBE CHANNEL (brand account)")
        print("Click 'Advanced' > 'Go to app' > 'Allow'")
        result = subprocess.run([sys.executable, "authorize.py"], cwd="E:\\ai-horror-channel")
        if result.returncode == 0 and os.path.exists("E:\\ai-horror-channel\\token.json"):
            print("  ✓ Authorization successful! token.json created")
        else:
            print("  ⚠ Authorization may have failed. Check browser.")
    
    # Final verification
    print_header("VERIFICATION")
    result = subprocess.run([sys.executable, "verify_setup.py"], cwd="E:\\ai-horror-channel", capture_output=True, text=True)
    print(result.stdout)
    
    print_header("NEXT STEPS")
    print("If verification shows all OK:")
    print("  python test_dry_run.py     # Dry run test")
    print("  python run_daily.py        # Full test upload (private)")
    print("  # Then as Admin:")
    print("  powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1")
    print("\nDone!")

if __name__ == "__main__":
    main()