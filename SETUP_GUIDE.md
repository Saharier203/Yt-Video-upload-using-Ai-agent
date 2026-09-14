# AI Horror/Anime/Thriller YouTube Channel - Complete Setup Guide

This guide walks you through setting up your fully automated AI horror channel on **E:\ai-horror-channel**.

> **Pipeline v2**: Now includes a Humanizer (strips AI-isms, adds delivery annotations), Scene Director (timed visual segments), and multi-layer SFX system (atmosphere, foley, tension, stingers). See DOCUMENTATION.md for full details.

---

## 📋 Prerequisites Checklist

- [ ] Windows 10/11
- [ ] Python 3.11+ installed (`python --version`)
- [ ] FFmpeg installed and in PATH (`ffmpeg -version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Git installed (`git --version`)

### Install Prerequisites (if missing)

```powershell
# Python 3.11
winget install Python.Python.3.11

# FFmpeg
winget install Gyan.FFmpeg

# Node.js LTS
winget install OpenJS.NodeJS.LTS

# Git (if needed)
winget install Git.Git
```

**Restart PowerShell after installations** for PATH updates.

---

## 🔑 Step 1: Get Free API Keys

### 1.1 Gemini API Key (Required)
1. Go to: https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

### 1.2 Pexels API Key (Required)
1. Go to: https://www.pexels.com/api/
2. Create free account
3. Generate API key
4. Copy the key

### 1.3 YouTube API Key (Optional - for analytics)
1. Go to: https://console.cloud.google.com/
2. Create project or select existing
3. Enable "YouTube Data API v3" and "YouTube Analytics API"
4. Create credentials → API Key
5. Copy the key

---

## 🔐 Step 2: Google Cloud OAuth Setup (Required for Upload)

### 2.1 Create OAuth Client
1. Go to: https://console.cloud.google.com/
2. Select your project
3. APIs & Services → Credentials
4. **OAuth Consent Screen** → External → Add your Google account as test user → Save
5. **Credentials** → Create Credentials → OAuth Client ID → **Desktop App**
6. Name it "AI Horror Channel"
7. Download JSON → Save as `E:\ai-horror-channel\client_secret.json`

### 2.2 Authorize the Channel
```powershell
cd E:\ai-horror-channel
python authorize.py
```
- Browser opens → Sign in as **your YouTube channel** (not personal account)
- Allow access (app is unverified - click Advanced → Go to app → Allow)
- Creates `token.json` in project root

---

## ⚙️ Step 3: Configure Environment

### 3.1 Create .env file
```powershell
copy E:\ai-horror-channel\.env.example E:\ai-horror-channel\.env
notepad E:\ai-horror-channel\.env
```
Edit with your actual API keys:
```env
GEMINI_API_KEY=AIzaSy...your_actual_key
PEXELS_API_KEY=563492ad...your_actual_key
YOUTUBE_API_KEY=AIzaSy...your_actual_key
```

### 3.2 Add Background Music (Required)
Place a royalty-free horror ambient track:
- Source: YouTube Audio Library, Pixabay Music, Freesound.org
- File: `E:\ai-horror-channel\assets\background_music.mp3`
- Duration: 1-2 hours (loops automatically)
- Style: Dark ambient, drone, horror atmosphere

### 3.3 Add Font (Required)
Copy a bold font for thumbnails:
```powershell
# Option A: Use system Arial Black (if available)
copy C:\Windows\Fonts\ariblk.ttf E:\ai-horror-channel\assets\font.ttf

# Option B: Download Anton from Google Fonts
# https://fonts.google.com/specimen/Anton
```

---

## 🧪 Step 4: Test the Pipeline

### 4.1 Dry Run (No Upload)
```powershell
cd E:\ai-horror-channel
python run_daily.py --no-upload
```
- Check `E:\ai-horror-channel\output\` for generated video
- Check `E:\ai-horror-channel\logs\` for any errors

### 4.2 Full Test Upload (Private)
```powershell
python run_daily.py
```
- Video uploads to YouTube as **Private**
- Check YouTube Studio → Content → Private videos
- Verify title, description, tags, captions, thumbnail

### 4.3 Test Weekly Long-form
```powershell
python run_weekly.py --no-upload
```
- Generates 8-10 minute horizontal video in `output/`

---

## ⏰ Step 5: Install Windows Task Scheduler (Automation)

Run as **Administrator**:
```powershell
powershell -ExecutionPolicy Bypass -File E:\ai-horror-channel\setup_scheduler.ps1
```

This creates two tasks:
- **AIHorrorChannel_Daily** - Runs daily at 8:55 AM
- **AIHorrorChannel_Weekly** - Runs Sundays at 12:55 PM

### Verify Tasks
1. Open Task Scheduler (`taskschd.msc`)
2. Task Scheduler Library → AIHorrorChannel_Daily / Weekly
3. Verify triggers, actions, conditions

### Manual Test Run
Right-click task → Run → Check logs in `E:\ai-horror-channel\logs\`

---

## 📊 Step 6: Post-Launch Configuration

### 6.1 YouTube Channel Settings
- Channel name: Update in YouTube Studio
- Banner/Logo: Create horror/anime themed
- About section: Describe your niche
- Featured channels: Link related horror channels

### 6.2 Monetization Setup (When Eligible)
| Requirement | Threshold | Where |
|-------------|-----------|-------|
| Shorts Fund | 10M views/90 days | Auto-invite |
| AdSense (Long) | 1K subs + 4K hrs | YouTube Studio → Earn |
| Patreon | Any time | patreon.com |
| Affiliates | Any time | Amazon Associates, etc. |

### 6.3 Add Monetization Links
Edit `config.json` → `upload.extra_tags` and descriptions to include:
- Patreon link in pinned comment
- Affiliate links in description
- Merch store link (when ready)

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Fix |
|-------|-----|
| `ffmpeg not found` | Add FFmpeg to PATH, restart terminal |
| `Gemini quota exceeded` | Wait for daily reset (midnight PST) or upgrade |
| `Pexels rate limit` | Built-in fallback to AI images only |
| `Upload fails` | Re-run `python authorize.py` |
| `Remotion render fails` | Falls back to FFmpeg automatically |
| `No video in output` | Check logs for error details |

### Log Locations
- Daily runs: `E:\ai-horror-channel\logs\daily_YYYYMMDD.log`
- Weekly runs: Check console output

### Reset Channel Config
```powershell
# Delete generated data (keeps config)
Remove-Item E:\ai-horror-channel\data -Recurse -Force
Remove-Item E:\ai-horror-channel\output -Recurse -Force
Remove-Item E:\ai-horror-channel\logs -Recurse -Force
```

---

## 📈 Optimization Tips

### Improve Performance
1. **Better scripts**: Edit `config.json` → `editorial` section with your specific preferences
2. **Visual style**: Tweak `video.ai_style` for unique look
3. **Voice**: Try different Edge TTS voices (`edge-tts --list-voices`)
4. **Posting time**: Adjust `schedule_time` based on analytics

### Scale Up
- Multiple channels: Copy entire folder, new `config.json`, new `client_secret.json`
- Different niches: Change `niche`, `channel_persona`, `editorial` in config
- Cross-post: Add TikTok/Instagram upload (coming in pipeline updates)

---

## 💰 Cost Breakdown (All Free)

| Service | Free Tier | Your Usage |
|---------|-----------|------------|
| Gemini API | 1,500 req/day | ~4 req/video = 375 videos/day |
| Edge TTS | Unlimited | Unlimited |
| Pollinations.ai | Unlimited | Unlimited |
| Pexels | 200/hr = 4,800/day | ~6 req/video = 800 videos/day |
| YouTube API | 10,000 units/day | ~1,600 units/video = 6 videos/day |

**Total: $0/month** for daily + weekly uploads

---

## 🆘 Support

- Repository: https://github.com/Mystery-CLI/faceless-video-engine
- Issues: GitHub Issues tab
- Logs: Always check `logs/` first before reporting issues

---

## ✅ Launch Checklist

- [ ] Prerequisites installed
- [ ] API keys in `.env`
- [ ] `client_secret.json` in place
- [ ] `python authorize.py` completed
- [ ] `background_music.mp3` in assets
- [ ] `font.ttf` in assets
- [ ] Dry run successful
- [ ] Test upload successful
- [ ] Task Scheduler installed
- [ ] Channel branded in YouTube Studio

**You're live!** The channel will now post daily horror/anime/thriller Shorts at 9 AM and weekly long-form on Sundays at 1 PM.