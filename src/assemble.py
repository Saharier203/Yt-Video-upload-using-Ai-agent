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
    # Search both assets/music/ and assets/ root for MP3 files
    search_dirs = []
    if ASSETS_MUSIC.exists():
        search_dirs.append(ASSETS_MUSIC)
    assets_root = ROOT / "assets"
    search_dirs.append(assets_root)

    all_tracks = []
    for d in search_dirs:
        if mood:
            mood_tracks = sorted((d / mood.strip().lower()).glob("*.mp3"))
            all_tracks.extend(mood_tracks)
        all_tracks.extend(sorted(d.rglob("*.mp3")))

    # Filter: only music files (exclude sfx, tts, voice, old background_music)
    skip_dirs = {"sfx", "foley", "stingers", "tension", "atmospheres", "ambient_beds"}
    skip_names = {"tts", "voice", "background_music", "chair_scrape", "distant_dog_bark",
                  "distant_siren", "door_creak", "floor_creak", "footsteps_gravel",
                  "paper_rustle", "rain_on_window", "wind_howl"}
    music_tracks = []
    for t in all_tracks:
        if any(part.lower() in skip_dirs for part in t.parts):
            continue
        if t.stem.lower() in skip_names or "sfx" in str(t).lower():
            continue
        music_tracks.append(t)

    return random.choice(music_tracks) if music_tracks else None


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


TRANSITIONS = ["fade", "fade", "smoothleft", "smoothright", "smoothup", "circleopen"]


def _build_sfx_layers(workdir: Path, voice_dur: float, beats: list, scenes: list,
                       config: dict) -> list[tuple[Path, float, str]]:
    """Build SFX audio layers based on beats and scenes.

    Returns list of (file_path, volume, label) tuples for mixing.
    """
    v = config["video"]
    atmosphere_vol = float(v.get("atmosphere_volume", 0.12))
    foley_vol = float(v.get("foley_volume", 0.10))
    tension_vol = float(v.get("tension_volume", 0.08))
    stinger_vol = float(v.get("stinger_volume", 0.25))
    ambient_bed_vol = float(v.get("ambient_bed_volume", 0.08))

    layers = []

    # 1. Ambient bed (continuous, looped) — prefer dread_rumble for horror
    beds = sorted((ASSETS_SFX / "ambient_beds").glob("*.wav"))
    if beds:
        horror_bed = ASSETS_SFX / "ambient_beds" / "dread_rumble.wav"
        if horror_bed.exists():
            layers.append((horror_bed, ambient_bed_vol, "ambient_bed"))
        else:
            layers.append((random.choice(beds), ambient_bed_vol, "ambient_bed"))

    # 2. Atmosphere per scene
    if scenes:
        for i, scene in enumerate(scenes):
            prompt = scene.get("scene_prompt", "") or scene.get("text", "")
            dur = scene.get("duration_sec", voice_dur / max(1, len(scenes)))
            atmos = _pick_atmosphere_for_scene(prompt)
            if atmos and atmos.exists():
                layers.append((atmos, atmosphere_vol, f"atmos_{i}"))
    elif beats:
        per_beat = voice_dur / max(1, len(beats))
        for i, beat in enumerate(beats):
            text = beat.get("text", "")
            atmos = _pick_atmosphere_for_scene(text)
            if atmos and atmos.exists():
                layers.append((atmos, atmosphere_vol, f"atmos_{i}"))

    # 3. Tension layers — continuous sub-rumble + beat-specific
    sub_rumble = ASSETS_SFX / "tension" / "sub_rumble_8s.wav"
    if sub_rumble.exists():
        layers.append((sub_rumble, tension_vol * 0.7, "tension_sub_rumble"))
    if beats:
        for beat in beats:
            beat_type = beat.get("beat", "body")
            tension_files = _pick_tension_layer(beat_type)
            for tf in tension_files:
                layers.append((tf, tension_vol, f"tension_{beat_type}"))

    # 4. Foley triggers from script text
    full_text = " ".join(b.get("text", "") for b in beats) if beats else ""
    foley_files = _pick_foley_for_trigger(full_text)
    for ff in foley_files:
        layers.append((ff, foley_vol, f"foley_{ff.stem}"))

    # 5. Stingers at twist/climax beats — each gets its own stinger
    if beats:
        for beat in beats:
            if beat.get("beat") in ("twist", "climax"):
                stinger = _pick_stinger_for_twist()
                if stinger and stinger.exists():
                    layers.append((stinger, stinger_vol, f"stinger_{beat.get('beat')}_{beat.get('text', '')[:10]}"))

    return layers


def _build_audio_filter_complex(voice_idx: int, sfx_layers: list[tuple[Path, float, str]],
                                 music_path: Path | None, music_vol: float,
                                 voice_dur: float) -> tuple[list[str], list[str]]:
    """Build ffmpeg filter_complex for multi-layer audio mixing.

    Returns (input_args, filter_complex_list).
    """
    input_args = []
    audio_filters = []
    next_idx = voice_idx + 1

    # Add SFX layers as inputs
    sfx_labels = []
    for sfx_path, vol, label in sfx_layers:
        if not sfx_path.exists():
            continue
        input_args += ["-stream_loop", "-1", "-i", str(sfx_path)]
        safe_label = re.sub(r'[^a-zA-Z0-9]', '_', label)
        audio_filters.append(f"[{next_idx}:a]volume={vol},acompressor=threshold=-24dB:ratio=4:attack=50:release=300[{safe_label}]")
        sfx_labels.append(f"[{safe_label}]")
        next_idx += 1

    # Add music
    if music_path and music_path.exists():
        input_args += ["-stream_loop", "-1", "-i", str(music_path)]
        audio_filters.append(f"[{next_idx}:a]volume={music_vol},acompressor=threshold=-24dB:ratio=4:attack=50:release=300[music_ducked]")
        sfx_labels.append("[music_ducked]")
        next_idx += 1

    return input_args, audio_filters, sfx_labels, next_idx


def build_video(raw_clips: list, voice_mp3: Path, ass_file: Path, config: dict,
                workdir: Path, out_file: Path, music_mood: str | None = None,
                with_music: bool = True, with_logo: bool = True,
                words: list | None = None, hook: str | None = None,
                script: str | None = None, scene_prompts: list | None = None,
                beats: list | None = None, scenes: list | None = None) -> Path:
    v = config["video"]
    w, h, fps = v["width"], v["height"], v["fps"]
    td = float(v.get("transition_seconds", 0.35))

    # Volume levels
    music_vol = float(v.get("music_volume", 0.03))
    logo_vol = float(config.get("branding", {}).get("sonic_logo_volume", 0.5))

    renderer = str(v.get("renderer", "remotion")).strip().lower()
    if renderer != "ffmpeg" and words:
        from . import remotion_render
        if remotion_render.available():
            try:
                return remotion_render.render(
                    raw_clips, voice_mp3, words, hook, config, workdir, out_file,
                    music=_pick_music(music_mood) if with_music else None,
                    logo=_brand_logo(config) if with_logo else None)
            except Exception as e:
                print(f"  Remotion render failed, falling back to ffmpeg: {e}")
        else:
            print("  Remotion project not installed (npm install in remotion/); using ffmpeg")

    audio_len = _probe_duration(voice_mp3)
    total = audio_len + 0.6
    n = len(raw_clips)
    per_clip = (total + (n - 1) * td) / n

    # 1. Normalize every clip to identical codec/size/fps
    norm_paths = []
    for i, raw in enumerate(raw_clips):
        norm = workdir / f"norm_{i}.mp4"
        _run([
            "ffmpeg", "-y", "-i", str(raw), "-t", f"{per_clip:.3f}",
            "-vf",
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},fps={fps},setsar=1",
            "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-pix_fmt", "yuv420p", str(norm),
        ], workdir)
        norm_paths.append(norm)

    # 2. Build SFX layers from beats/scenes
    if not beats and script:
        beats = _extract_script_beats(script)
    sfx_layers = _build_sfx_layers(workdir, audio_len, beats or [], scenes or [], config)

    # 3. Pick music
    music_file = _pick_music(music_mood) if with_music else None

    # 4. Build ffmpeg command
    args = ["ffmpeg", "-y"]
    for p in norm_paths:
        args += ["-stream_loop", "-1", "-i", p.name]
    args += ["-i", str(voice_mp3)]
    next_idx = n + 1

    # 5. Add SFX layers
    audio_filters = []
    mix_labels = [f"[{n}:a]"]  # voice is always index n

    for sfx_path, vol, label in sfx_layers:
        if not sfx_path.exists():
            continue
        args += ["-stream_loop", "-1", "-i", str(sfx_path)]
        safe_label = re.sub(r'[^a-zA-Z0-9]', '_', label)
        audio_filters.append(f"[{next_idx}:a]volume={vol},acompressor=threshold=-24dB:ratio=4:attack=50:release=300[{safe_label}]")
        mix_labels.append(f"[{safe_label}]")
        next_idx += 1

    # 6. Add music
    if music_file and music_file.exists():
        args += ["-stream_loop", "-1", "-i", str(music_file)]
        audio_filters.append(f"[{next_idx}:a]volume={music_vol},acompressor=threshold=-24dB:ratio=4:attack=50:release=300[music_ducked]")
        mix_labels.append("[music_ducked]")
        next_idx += 1

    # 7. Video crossfade filters
    filters = []
    if n == 1:
        filters.append(f"[0:v]ass={ass_file.name}[v]")
    else:
        prev = "[0:v]"
        for i in range(1, n):
            offset = i * (per_clip - td)
            label = f"[x{i}]" if i < n - 1 else "[xv]"
            filters.append(f"{prev}[{i}:v]xfade=transition=fade:duration={td:.3f}:offset={offset:.3f}{label}")
            prev = label
        filters.append(f"[xv]ass={ass_file.name}[v]")

    # 8. Audio mix
    filters.extend(audio_filters)
    if len(mix_labels) > 1:
        mix_inputs = "".join(mix_labels)
        filters.append(f"{mix_inputs}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=0:normalize=0[a]")
        audio_map = "[a]"
    else:
        audio_map = f"{n}:a"

    # 9. Run ffmpeg
    args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", audio_map,
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-t", f"{_probe_duration(voice_mp3) + 0.6:.3f}", str(out_file)]
    _run(args, workdir)
    return out_file