# 🚀 NEXT STEPS - Complete These to Go Live

## ✅ Already Done (Automated)
- [x] Repository cloned to `E:\ai-horror-channel`
- [x] Python dependencies installed
- [x] Remotion (React renderer) installed
- [x] `config.json` created (horror/anime/thriller optimized)
- [x] `run_daily.bat` created
- [x] `setup_scheduler.ps1` created
- [x] `.env` template created
- [x] `assets/font.ttf` downloaded (Anton font)
- [x] `SETUP_GUIDE.md` complete documentation
- [x] `assets/README.md` with music/font instructions

---

## 🔴 REQUIRED: You Must Do These

### 1. Add Your API Keys to `.env`
```powershell
notepad E:\ai-horror-channel\.env
```
Replace the placeholders:
```env
GEMINI_API_KEY=AIzaSyC...your_actual_key_from_aistudio
PEXELS_API_KEY=563492ad...your_actual_key_from_pexels
```

**Get keys here:**
- **Gemini**: https://aistudio.google.com/apikey (free, 1500 req/day)
- **Pexels**: https://www.pexels.com/api/ (free, 200/hr)

---

### 2. Add Background Music
```powershell
# Download a horror ambient track (1-2 hours) to:
# E:\ai-horror-channel\assets\background_music.mp3

# Free sources:
# - YouTube Audio Library: https://www.youtube.com/audiolibrary/music
# - Pixabay Music: https://pixabay.com/music/search/horror%20ambient/
# - Freesound: https://freesound.org/search/?q=dark%20ambient
```

---

### 3. Google Cloud OAuth Setup (for YouTube Upload)
```powershell
# 1. Go to https://console.cloud.google.com/
# 2. Create project "AI Horror Channel"
# 3. Enable APIs: YouTube Data API v3 + YouTube Analytics API
# 4. OAuth Consent Screen → External → Add your email as test user
# 5. Credentials → Create Credentials → OAuth Client ID → Desktop App
# 6. Download JSON → Save as E:\ai-horror-channel\client_secret.json
```

### 4. Authorize Your YouTube Channel
```powershell
cd E:\ai-horror-channel
python authorize.py
```
- Browser opens → Sign in as **your YouTube channel** (brand account)
- Allow access (click Advanced → Go to app → Allow)
- Creates `token.json`

---

## 🧪 Test Before Scheduling

### Test 1: Dry Run (No Upload)
```powershell
cd E:\ai-horror-channel
python run_daily.py --no-upload
```
- Check `output/` for generated video
- Check `logs/` for errors

### Test 2: Full Upload (Private)
```powershell
python run_daily.py
```
- Check YouTube Studio → Content → Private videos
- Verify: title, description, tags, captions, thumbnail

### Test 3: Weekly Long-form
```powershell
python run_weekly.py --no-upload
```
- Generates 8-10 min horizontal video in `output/`

---

## ⏰ Install Auto-Scheduler (Run as Administrator)

```powershell
# Right-click PowerShell → Run as Administrator
powershell -ExecutionPolicy Bypass -File E:\ai-horror-channel\setup_scheduler.ps1
```

Creates:
- **Daily** at 8:55 AM → Posts at 9:00 AM
- **Weekly** Sunday 12:55 PM → Posts at 1:00 PM

---

## 📊 Verify It's Working

1. **Task Scheduler** (`taskschd.msc`) → Task Scheduler Library
   - AIHorrorChannel_Daily
   - AIHorrorChannel_Weekly

2. **Logs**: `E:\ai-horror-channel\logs\daily_YYYYMMDD.log`

3. **YouTube Studio**: Check for new uploads daily

---

## 🎯 Channel Branding (Optional but Recommended)

Edit `config.json` to customize:
```json
"editorial": { "cta": "Subscribe to YOUR_CHANNEL_NAME. The next story finds you." },
"upload": { "extra_tags": ["yourchannelname", "horror", ...] },
"playlists": ["Your Custom Playlist Names"]
```

---

## 💰 Monetization (Auto-Enabled at Thresholds)

| Program | Requirement | Earnings |
|---------|-------------|----------|
| Shorts Fund | 10M views/90 days | $100-$10K/mo |
| AdSense (Long) | 1K subs + 4K hrs | $4-8 RPM |
| Patreon | Anytime | $500-$5K+/mo |
| Affiliates | Anytime | $100-$2K/mo |

Add links in video descriptions + pinned comments.

---

## 🆘 If Tests Fail

### Common Fixes:
| Error | Fix |
|-------|-----|
| `GEMINI_API_KEY not set` | Edit `.env` with real key |
| `ffmpeg not found` | `winget install Gyan.FFmpeg`, restart terminal |
| `Pollinations 402` | Gemini key invalid/missing - check `.env` |
| `Upload failed` | Re-run `python authorize.py` |
| `No video output` | Check `logs/` for details |

### Quick Debug:
```powershell
cd E:\ai-horror-channel
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('GEMINI:', 'SET' if os.getenv('GEMINI_API_KEY') != 'YOUR_GEMINI_API_KEY_HERE' else 'MISSING')
print('PEXELS:', 'SET' if os.getenv('PEXELS_API_KEY') != 'YOUR_PEXELS_API_KEY_HERE' else 'MISSING')
print('client_secret.json:', os.path.exists('client_secret.json'))
print('token.json:', os.path.exists('token.json'))
print('background_music.mp3:', os.path.exists('assets/background_music.mp3'))
print('font.ttf:', os.path.exists('assets/font.ttf'))
"
```

---

## 📞 Support

- **Full Guide**: `SETUP_GUIDE.md`
- **Repo Issues**: https://github.com/Mystery-CLI/faceless-video-engine/issues
- **Logs**: `E:\ai-horror-channel\logs\`

---

**Once API keys are added and OAuth authorized, run the dry run test. If it passes, install the scheduler and you're live!**