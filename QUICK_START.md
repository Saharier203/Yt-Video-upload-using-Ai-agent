# 🎬 CASE FILE JAPAN - QUICK START CARD

## Project Location
```
E:\ai-horror-channel\
```

---

## ⚡ 3 THINGS YOU MUST DO (5 minutes)

### 1. Add API Keys to `.env`
```powershell
notepad E:\ai-horror-channel\.env
```
Replace with YOUR keys:
```env
GEMINI_API_KEY=AIzaSyC...your_key_from_https://aistudio.google.com/apikey
PEXELS_API_KEY=563492ad...your_key_from_https://www.pexels.com/api/
```

### 2. Google Cloud OAuth Setup
1. https://console.cloud.google.com/ → New Project "AI Horror Channel"
2. Enable: **YouTube Data API v3** + **YouTube Analytics API**
3. OAuth Consent → External → Add your email
4. Credentials → Create → OAuth Client ID → **Desktop App**
5. Download JSON → Save as `E:\ai-horror-channel\client_secret.json`

### 3. Authorize Your Channel
```powershell
cd E:\ai-horror-channel
python authorize.py
```
- Browser opens → Sign in as **your YouTube CHANNEL** (brand account)
- Click **Advanced** → **Go to app** → **Allow**
- Creates `token.json`

---

## 🧪 TEST COMMANDS

```powershell
cd E:\ai-horror-channel

# 1. Verify setup (all green = ready)
python verify_setup.py

# 2. Dry run (no upload) - RUN AFTER ADDING KEYS
python test_dry_run.py

# 3. Full test upload (private)
python run_daily.py

# 4. Test weekly long-form
python run_weekly.py --no-upload
```

---

## ⏰ INSTALL AUTO-SCHEDULER (Run as Administrator)

```powershell
# Right-click PowerShell > "Run as Administrator"
powershell -ExecutionPolicy Bypass -File E:\ai-horror-channel\setup_scheduler.ps1
```

Creates:
- **Daily** at 8:55 AM → Posts 9:00 AM
- **Weekly** Sunday 12:55 PM → Posts 1:00 PM

---

## 📊 CHECK STATUS

```powershell
# View logs
type E:\ai-horror-channel\logs\daily_*.log

# Check Task Scheduler
taskschd.msc
# Look for: AIHorrorChannel_Daily, AIHorrorChannel_Weekly

# Check YouTube uploads
# YouTube Studio > Content > Private/Public videos
```

---

## 🎨 CONTENT FORMAT: "CASE FILE" (6 Beats)

```
1. HOOK:     "In March 1994, Kyoto Police Report #447 describes a woman 
              who vanished from a locked bathroom. The only evidence: 
              a single red thread wrapped around the toilet handle."

2. RECORD:   "The report states: 'Victim: female, 20s. Location: 
              Yasaka Shrine public bathroom, 3rd stall. Time: 22:47. 
              Door locked from inside. No signs of forced entry.'"

3. WITNESS:  "Night guard Sato Hiroshi, 58, logged: 'Heard footsteps 
              in sealed west wing. No one there. Again.' His logbook 
              entry, March 3rd, 1994."

4. LOCATION: "The bathroom was renovated in 2003. Staff still refuse 
              to clean it after 6 PM. The stall door doesn't lock anymore."

5. GAP:      "Police ruled it 'runaway.' Sure. She ran away without 
              her shoes, her bag, or her left hand. Very athletic for a ghost."

6. THREAD:   "The red thread? Still in evidence locker #447. Want to 
              know what DNA was on it? So do I."
```

**NO CTA. NO "SUBSCRIBE." THE STORY IS THE HOOK.**

---

## 🎯 VISUAL STRATEGY

| Component | Ratio | Source |
|-----------|-------|--------|
| Location footage | 85% | Pexels stock (real places) |
| Supernatural entities | 15% | AI (cached per legend) |
| Visual anchors | Transitions | Notebook / Lamp / Coffee |

- **Entity consistency**: First AI image per legend → cached → reused
- **Stock search**: Actual locations (shrines, stations, hotels, tunnels)
- **Style**: 1990s analog horror, VHS static, CRT scanlines, teal/orange grading

---

## 💰 MONETIZATION (Auto at Thresholds)

| Program | Requirement | Action |
|---------|-------------|--------|
| Shorts Fund | 10M views/90d | Auto-invite |
| AdSense Long | 1K subs + 4K hrs | YouTube Studio > Earn |
| Patreon | Anytime | Add link in descriptions |
| Affiliates | Anytime | Amazon Associates, etc. |

---

## 🆘 TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| `GEMINI_API_KEY` error | Check `.env` has real key (starts with AIzaSy) |
| `ffmpeg not found` | `winget install Gyan.FFmpeg`, restart terminal |
| `Pollinations 402` | Gemini key invalid - check `.env` |
| Upload fails | Re-run `python authorize.py` |
| `access_denied` OAuth | Cloud Console → OAuth Consent → Test Users → Add your email |
| No video output | Check `logs/` for details |

---

## 📁 KEY FILES

| File | Purpose |
|------|---------|
| `config.json` | Channel niche, style, schedule, editorial rules |
| `.env` | API keys (gitignored) |
| `client_secret.json` | YouTube OAuth (gitignored) |
| `token.json` | Auth token (gitignored) |
| `assets/background_music.mp3` | 2hr looped horror ambient |
| `assets/font.ttf` | Anton bold font |
| `run_daily.bat` | Windows daily runner |
| `setup_scheduler.ps1` | Task Scheduler installer |
| `DOCUMENTATION.md` | Complete guide |
| `verify_setup.py` | Pre-flight check |
| `test_dry_run.py` | End-to-end test |

---

## 🔗 USEFUL LINKS

- **Gemini API**: https://aistudio.google.com/apikey
- **Pexels API**: https://www.pexels.com/api/
- **Google Cloud**: https://console.cloud.google.com/
- **YouTube Audio Library**: https://www.youtube.com/audiolibrary/music
- **Repo**: https://github.com/Mystery-CLI/faceless-video-engine