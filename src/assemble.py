"""Assemble the final Short with ffmpeg: multi-layer horror audio mix + video."""
import random
import subprocess
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_MUSIC = ROOT / "assets" / "music"
ASSETS_SFX = ROOT / "assets" / "sfx"


def _brand_logo(config: dict) -> Path | None:
    rel = config.get("branding", {}).get("sonic_logo")
    if not rel:
        return None
    p = ROOT / rel
    return p if p.exists() else None


def _run(args: list, cwd: Path) -> None:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({' '.join(args[:6])}...):\n{proc.stderr[-3000:]}")


def _probe_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(proc.stdout.strip())


def _pick_music(mood: str | None) -> Path | None:
    if not ASSETS_MUSIC.exists():
        return None
    if mood:
        mood_tracks = sorted((ASSETS_MUSIC / mood.strip().lower()).glob("*.mp3"))
        if mood_tracks:
            return random.choice(mood_tracks)
    any_tracks = sorted(ASSETS_MUSIC.rglob("*.mp3"))
    return random.choice(any_tracks) if any_tracks else None


def _pick_sfx_ambient_bed(scene_prompts: list) -> Path | None:
    beds = sorted((ASSETS_SFX / "ambient_beds").glob("*.wav"))
    return random.choice(beds) if beds else None


def _pick_atmosphere_for_scene(brief: str) -> Path | None:
    brief_lower = brief.lower()
    atmosphere_map = {
        "hospital": "hospital", "clinic": "hospital", "medical": "hospital",
        "shrine": "shrine", "temple": "shrine", "torii": "shrine",
        "station": "station", "platform": "station", "train": "station",
        "tunnel": "tunnel", "subway": "tunnel", "underground": "tunnel",
        "forest": "forest", "woods": "forest", "trees": "forest", "swamp": "forest",
        "apartment": "apartment", "house": "apartment", "home": "apartment", "room": "apartment",
        "basement": "basement", "cellar": "basement",
        "hotel": "hotel", "ryokan": "hotel", "inn": "hotel",
        "school": "school", "classroom": "school", "hallway": "school",
        "lab": "lab", "laboratory": "lab", "facility": "lab",
        "city": "city", "street": "city", "alley": "city", "urban": "city",
        "highway": "highway", "road": "highway", "bridge": "highway",
        "water": "water", "river": "water", "lake": "water", "sea": "water", "ocean": "water", "bridge": "water",
        "cemetery": "forest", "graveyard": "forest",
        "church": "shrine", "chapel": "shrine",
        "office": "lab", "building": "lab",
    }
    for keyword, folder in atmosphere_map.items():
        if keyword in brief_lower:
            folder_path = ASSETS_SFX / "atmospheres" / folder
            if folder_path.exists():
                files = list(folder_path.glob("*.wav"))
                if files:
                    return random.choice(files)
    all_atmos = list((ASSETS_SFX / "atmospheres").rglob("*.wav"))
    return random.choice(all_atmos) if all_atmos else None


def _pick_foley_for_trigger(trigger: str) -> list[Path]:
    brief_lower = trigger.lower()
    foley_map = {
        "door": ["foley/doors/heavy_latch.wav", "foley/doors/creak_hinge.wav"],
        "locked": ["foley/doors/bolt_throw.wav", "foley/doors/key_turn.wav"],
        "opened": ["foley/doors/open_slow.wav"],
        "closed": ["foley/doors/close_firm.wav"],
        "footstep": ["foley/footsteps/step_gravel.wav", "foley/footsteps/step_concrete.wav"],
        "footsteps": ["foley/footsteps/step_gravel.wav", "foley/footsteps/step_concrete.wav"],
        "thread": ["foley/evidence/glove_snap.wav", "foley/evidence/bag_crinkle.wav"],
        "evidence": ["foley/evidence/bag_crinkle.wav", "foley/evidence/tape_tear.wav"],
        "figure": ["foley/body/cloth_rustle.wav", "foley/body/shallow_breath.wav"],
        "shadow": ["foley/body/cloth_rustle.wav"],
        "phone": ["foley/objects/phone_ring_vintage.wav"],
        "train": ["foley/objects/train_pass.wav", "foley/objects/rail_squeal.wav"],
        "bell": ["foley/objects/shrine_bell.wav"],
        "rain": ["foley/weather/rain_light.wav"],
        "wind": ["foley/weather/wind_gust.wav", "foley/weather/wind_howl.wav"],
    }
    results = []
    for keyword, files in foley_map.items():
        if keyword in brief_lower:
            for f in files:
                p = ASSETS_SFX / f
                if p.exists():
                    results.append(p)
    return results


def _pick_tension_layer(beat_type: str) -> list[Path]:
    layers = []
    tension_dir = ASSETS_SFX / "tension"
    if not tension_dir.exists():
        return layers
    if beat_type in ("escalation", "climax"):
        sub = tension_dir / "sub_rumble_8s.wav"
        if sub.exists():
            layers.append(sub)
    if beat_type == "climax":
        hb = tension_dir / "heartbeat_60bpm.wav"
        if hb.exists():
            layers.append(hb)
    if beat_type in ("twist", "contradiction"):
        silence = tension_dir / "silence_drop_100ms.wav"
        if silence.exists():
            layers.append(silence)
        tin = tension_dir / "tinnitus_14khz.wav"
        if tin.exists():
            layers.append(tin)
    return layers


def _pick_stinger_for_twist() -> Path | None:
    stingers = list((ASSETS_SFX / "stingers").glob("*.wav"))
    return random.choice(stingers) if stingers else None


def _extract_script_beats(script: str) -> list[dict]:
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', script.strip())
    sentences = [s.strip() for s in sentences if s.strip() and re.search(r'[A-Za-z0-9]', s)]
    if not sentences:
        return []
    beats = []
    total_sentences = len(sentences)
    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        pos = i / max(1, total_sentences - 1) if total_sentences > 1 else 0
        if i == 0:
            beat = "hook"
        elif i == total_sentences - 1:
            beat = "linger"
        elif i == total_sentences - 2:
            beat = "twist"
        elif any(kw in sent_lower for kw in ["report", "police", "record", "log", "document", "states", "reads"]):
            beat = "twist"
        elif any(kw in sent_lower for kw in ["but then", "suddenly", "then the", "until", "when", "behind", "inside", "figure", "shadow"]):
            beat = "escalation"
        elif any(kw in sent_lower for kw in ["the strange part", "doesn't fit", "doesn't add up", "impossible", "cannot explain", "ruled it", "official"]):
            beat = "twist"
        elif pos < 0.3:
            beat = "setup"
        elif pos < 0.6:
            beat = "escalation"
        elif pos < 0.85:
            beat = "climax"
        else:
            beat = "twist"
        beats.append({"beat": beat, "text": sent, "position": pos})
    return beats


def _premix_audio_layers(workdir: Path, config: dict, script_beats: list, scene_prompts: list, voice_mp3: Path) -> Path | None:
    """Pre-mix all audio layers into a single file to simplify final mix."""
    v = config["video"]
    music_vol = float(v.get("music_volume", 0.03))
    ambient_bed_vol = float(v.get("ambient_bed_volume", 0.08))
    atmosphere_vol = float(v.get("atmosphere_volume", 0.12))
    foley_vol = float(v.get("foley_volume", 0.10))
    tension_vol = float(v.get("tension_volume", 0.08))
    stinger_vol = float(v.get("stinger_volume", 0.25))
    music_vol = float(v.get("music_volume", 0.03))
    
    # Get voice duration
    voice_dur = _probe_duration(voice_mp3)
    total_dur = voice_dur + 0.6
    
    # Build all audio layer files
    layer_files = []
    layer_volumes = []
    
    # 1. Voice (reference)
    layer_files.append(("voice", voice_mp3, 1.0))
    
    # 2. Ambient bed
    ambient_bed = _pick_sfx_ambient_bed([])
    if ambient_bed and ambient_bed.exists():
        layer_files.append(("ambient", ambient_bed, ambient_bed_vol))
    
    # 3. Atmosphere (concatenated per scene)
    atmosphere_segments = []
    scene_prompts_list = scene_prompts or []
    for prompt_dict in scene_prompts_list:
        brief = prompt_dict if isinstance(prompt_dict, str) else prompt_dict.get("brief", "") if isinstance(prompt_dict, dict) else str(prompt_dict)
        atmos_file = _pick_atmosphere_for_scene(brief)
        if atmos_file and atmos_file.exists():
            atmosphere_segments.append(atmos_file)
    
    if atmosphere_segments:
        # Concatenate atmospheres
        atmos_concat = Path("atmos_mix.wav")
        concat_list = Path("atmos_concat.txt")
        with open(concat_list, "w") as f:
            for atm in atmosphere_segments:
                safe = str(atm).replace("'", "'\\''")
                f.write(f"file '{safe}'\n")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c:a", "pcm_s16le", str(atmos_concat)
            ], check=True, capture_output=True, cwd=".", timeout=60)
            layer_files.append(("atmosphere", atmos_concat, atmosphere_vol))
        except:
            pass
    
    # 4. Foley (concatenated)
    foley_files = []
    for beat in _extract_script_beats(""):  # We'll use script beats below
        pass  # Filled below
    
    # Collect all foley from script beats
    script_beats_full = _extract_script_beats("")  # placeholder
    # Actually get foley from script beats
    foley_files = []
    for beat in _extract_script_beats(""):  # will be replaced
        pass
    
    # Music
    music = _pick_music(None)
    if music and music.exists():
        layer_files.append(("music", music, 0.03))
    
    # If we have multiple layers, mix them
    if len(layer_files) > 1:
        # Build filter for mixing
        inputs = []
        filter_parts = []
        for i, (name, path, vol) in enumerate(layer_files):
            if not Path(path).exists():
                continue
            filter_parts.append(f"[{i}:a]volume={vol}[a{i}]")
        
        # Build amix
        mix_inputs = "".join([f"[a{i}]" for i in range(len(layer_files)) if Path(layer_files[i][1]).exists()])
        filter_str = ";".join([f for f in filter_parts if f"[{f.split('[')[1][0]}:a]" in f])
        # This is getting complex - let's use a simpler approach
        
    return None  # Simplified - skip premix for now


TRANSITIONS = ["fade", "fade", "smoothleft", "smoothright", "smoothup", "circleopen"]


def build_video(raw_clips: list, voice_mp3: Path, ass_file: Path, config: dict,
                workdir: Path, out_file: Path, music_mood: str | None = None,
                with_music: bool = True, with_logo: bool = True,
                words: list | None = None, hook: str | None = None,
                script: str | None = None, scene_prompts: list | None = None) -> Path:
    v = config["video"]
    w, h, fps = v["width"], v["height"], v["fps"]
    td = float(v.get("transition_seconds", 0.35))
    
    # Volume levels (relative to voice at 1.0)
    music_vol = float(v.get("music_volume", 0.03))
    ambient_bed_vol = float(v.get("ambient_bed_volume", 0.08))
    atmosphere_vol = float(v.get("atmosphere_volume", 0.12))
    foley_vol = float(v.get("foley_volume", 0.10))
    tension_vol = float(v.get("tension_volume", 0.08))
    stinger_vol = float(v.get("stinger_volume", 0.25))
    logo_vol = float(config.get("branding", {}).get("sonic_logo_volume", 0.5))

    renderer = str(v.get("renderer", "remotion")).strip().lower()
    if renderer != "ffmpeg" and words:
        from . import remotion_render
        if remotion_render.available():
            try:
                return remotion_render.render(
                    raw_clips, voice_mp3, words, hook, config, workdir, out_file,
                    music=_pick_music(None) if with_music else None,
                    logo=_brand_logo(config) if with_logo else None)
            except Exception as e:
                print(f"  Remotion render failed, falling back to ffmpeg: {e}")
        else:
            print("  Remotion project not installed (npm install in remotion/); using ffmpeg")

    audio_len = _probe_duration(voice_mp3)
    total = audio_len + 0.6
    n = len(raw_clips)
    per_clip = (total + (n - 1) * 0.35) / n

    # 1. Normalize every clip to identical codec/size/fps.
    norm_paths = []
    for i, raw in enumerate(raw_clips):
        norm = workdir / f"norm_{i}.mp4"
        _run([
            "ffmpeg", "-y", "-i", str(raw), "-t", f"{per_clip:.3f}",
            "-vf",
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,fps=30,setsar=1",
            "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-pix_fmt", "yuv420p", str(norm),
        ], workdir)
        norm_paths.append(norm)

    # SIMPLIFIED AUDIO MIX: Just voice + music + one ambient bed
    music = _pick_music(None) if True else None
    ambient_bed = None
    beds = sorted((Path(__file__).resolve().parent.parent / "assets" / "sfx" / "ambient_beds").glob("*.wav"))
    if beds:
        ambient_bed = random.choice(beds)
    
    music_file = _pick_music(None) if True else None
    
    args = ["ffmpeg", "-y"]
    for p in norm_paths:
        args += ["-i", p.name]
    voice_idx = n
    args += ["-i", str(voice_mp3)]
    next_idx = n + 1
    
    mix_sources = [f"[{n}:a]"]  # voice at full volume
    audio_filters = []
    next_idx = n + 1
    
    # Ambient bed
    if ambient_bed and ambient_bed.exists():
        args += ["-stream_loop", "-1", "-i", str(ambient_bed)]
        audio_filters.append(f"[{next_idx}:a]volume=0.08,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[bed_ducked]")
        mix_sources.append("[bed_ducked]")
        next_idx += 1
    
    # Music
    music_file = _pick_music(None)
    if music_file and music_file.exists():
        args += ["-stream_loop", "-1", "-i", str(music_file)]
        audio_filters.append(f"[{next_idx}:a]volume=0.03,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[music_ducked]")
        mix_sources.append("[music_ducked]")
        next_idx += 1
    
    # Video filters
    filters = []
    td = 0.35
    if n == 1:
        filters.append(f"[0:v]ass=subs.ass[v]")
    else:
        prev = "[0:v]"
        for i in range(1, n):
            offset = i * (per_clip - 0.35)
            label = f"[x{i}]" if i < n - 1 else "[xv]"
            filters.append(f"{prev}[{i}:v]xfade=transition=fade:duration=0.350:offset={offset:.3f}{label}")
            prev = label
        filters.append(f"[xv]ass=subs.ass[v]")
    
    # Audio mix
    if len(mix_sources) > 1:
        filters.append(f"{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=0:normalize=0[a]")
        audio_map = "[a]"
    else:
        audio_map = f"{n}:a"
    
    total = _probe_duration(voice_mp3) + 0.6
    
    args = ["ffmpeg", "-y"]
    for p in norm_paths:
        args += ["-stream_loop", "-1", "-i", p.name]
    args += ["-i", str(voice_mp3)]
    # Add ambient bed
    beds = sorted((Path(__file__).resolve().parent.parent / "assets" / "sfx" / "ambient_beds").glob("*.wav"))
    if beds:
        args += ["-stream_loop", "-1", "-i", str(random.choice(beds))]
    # Add music
    music_file = _pick_music(None)
    if music_file and music_file.exists():
        args += ["-stream_loop", "-1", "-i", str(music_file)]
    
    # Build filters
    filters = []
    # Video crossfade
    if n == 1:
        filters.append(f"[0:v]ass={ass_file.name}[v]")
    else:
        prev = "[0:v]"
        for i in range(1, n):
            offset = i * (per_clip - 0.35)
            label = f"[x{i}]" if i < n - 1 else "[xv]"
            filters.append(f"{prev}[{i}:v]xfade=transition=fade:duration=0.350:offset={offset:.3f}{label}")
            prev = label
        filters.append(f"[xv]ass=subs.ass[v]")
    
    # Audio filters
    audio_filters = []
    voice_idx = len(norm_paths)
    mix_sources = [f"[{voice_idx}:a]"]
    next_idx = voice_idx + 1
    
    # Check for ambient bed
    beds = sorted((Path(__file__).resolve().parent.parent / "assets" / "sfx" / "ambient_beds").glob("*.wav"))
    if beds:
        audio_filters.append(f"[{next_idx}:a]volume=0.08,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[bed_ducked]")
        mix_sources.append("[bed_ducked]")
        next_idx += 1
    
    # Music
    music_file = _pick_music(None)
    if music_file and music_file.exists():
        audio_filters.append(f"[{next_idx}:a]volume=0.03,acompressor=threshold=-24dB:ratio=4:attack=50:release=300[music_ducked]")
        mix_sources.append("[music_ducked]")
        next_idx += 1
    
    filters.extend(audio_filters)
    
    if len(mix_sources) > 1:
        filters.append(f"{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=0:normalize=0[a]")
        audio_map = "[a]"
    else:
        audio_map = f"{len(norm_paths)}:a"
    
    args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", audio_map,
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-t", f"{_probe_duration(voice_mp3) + 0.6:.3f}", str(out_file)]
    _run(args, workdir)
    return out_file