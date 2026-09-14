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

## 3. sfx/ (PRE-BUILT - Do Not Delete)
The sound effects library is already included:

```
sfx/
├── ambient_beds/       # 4 continuous background ambience files
│   ├── analog_hiss.wav
│   ├── city_distant.wav
│   ├── dread_rumble.wav
│   └── forest_night.wav
├── atmospheres/        # 13 location-specific audio folders
│   ├── apartment/      ├── basement/     ├── city/
│   ├── forest/         ├── highway/      ├── hospital/
│   ├── hotel/          ├── lab/          ├── school/
│   ├── shrine/         ├── station/      ├── tunnel/
│   └── water/
├── foley/              # 7 categories of triggered sound effects
│   ├── body/           ├── cloth/        ├── doors/
│   ├── evidence/       ├── footsteps/    ├── objects/
│   └── weather/
├── tension/            # 6 beat-synced tension layers
│   ├── heartbeat_60bpm.wav    ├── heartbeat_thump.wav
│   ├── silence_drop_50ms.wav  ├── silence_drop_100ms.wav
│   ├── sub_rumble_8s.wav      └── tinnitus_14khz.wav
└── stingers/           # 14 impact sounds for twists/reveals
    ├── cluster_0.wav through cluster_6.wav
    ├── cymbal_swell.wav
    ├── metal_scrape.wav / metal_scrape_sub.wav
    ├── piano_cluster.wav / piano_cluster_reverb.wav
    ├── reverse_swell_cut.wav
    └── sub_hit.wav
```

## Quick Setup Commands:
```powershell
# Copy Arial Black if available
copy C:\Windows\Fonts\ariblk.ttf E:\ai-horror-channel\assets\font.ttf

# Or download Anton (run in PowerShell)
Invoke-WebRequest -Uri "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf" -OutFile "E:\ai-horror-channel\assets\font.ttf"
```

The pipeline will fail without background_music.mp3 and font.ttf!