# Assets Folder

Place the following files in this folder:

## 1. background_music.mp3 (REQUIRED)
- Royalty-free horror/dark ambient track
- Duration: 1-2 hours (loops automatically)
- Sources:
  - YouTube Audio Library (free)
  - Pixabay Music (free)
  - Freesound.org (free, check license)
  - Incompetech (free with attribution)
- Recommended search: "dark ambient horror", "cinematic horror drone", "creepy atmosphere"

## 2. font.ttf (REQUIRED)
- Bold, readable font for thumbnails and captions
- Options:
  - Arial Black (system): copy from C:\Windows\Fonts\ariblk.ttf
  - Anton (Google Fonts): https://fonts.google.com/specimen/Anton
  - Bangers (Google Fonts): https://fonts.google.com/specimen/Bangers
  - Creepster (Google Fonts): https://fonts.google.com/specimen/Creepster (horror-themed)

## Quick Setup Commands:
```powershell
# Copy Arial Black if available
copy C:\Windows\Fonts\ariblk.ttf E:\ai-horror-channel\assets\font.ttf

# Or download Anton (run in PowerShell)
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf" -OutFile "E:\ai-horror-channel\assets\font.ttf"
```

The pipeline will fail without these files!