"""Background clips: Stock-first with AI accents for supernatural elements.
Entity caching: first AI-generated image per legend is reused across videos.
Visual anchors: recurring objects (notebook, lamp, coffee) appear as transitions.
Image relevance: strict matching between script content and visual search terms."""
import os
import random
import shutil
import subprocess
import time
from pathlib import Path

import requests

PEXELS_SEARCH = "https://api.pexels.com/videos/search"
BROLL_CACHE = Path(__file__).resolve().parent.parent / "assets" / "broll"
ENTITY_CACHE = Path(__file__).resolve().parent.parent / "assets" / "entities"

# Horror-specific sound effects for atmosphere
HORROR_SFX = [
    "distant_dog_bark", "floor_creak", "wind_howl", "rain_on_window",
    "distant_siren", "clock_tick", "paper_rustle", "chair_scrape",
    "door_creak", "footsteps_gravel", "breath_cold", "static_burst"
]

def _pexels_clip(query: str, api_key: str, out_path: Path, min_seconds: float,
                 used_ids: set, orientation: str = "portrait",
                 target_height: int = 1920) -> bool:
    resp = None
    for attempt in range(3):
        try:
            resp = requests.get(
                PEXELS_SEARCH,
                headers={"Authorization": api_key},
                params={"query": query, "orientation": orientation, "per_page": 20},
                timeout=60,
            )
            break
        except requests.exceptions.ConnectionError:
            if attempt == 2:
                raise
            time.sleep(8)
    resp.raise_for_status()
    videos = resp.json().get("videos", [])
    random.shuffle(videos)
    for video in videos:
        if video.get("id") in used_ids:
            continue
        if video.get("duration", 0) < min_seconds:
            continue
        files = [f for f in video.get("video_files", []) if f.get("height") and f["height"] >= 1080]
        if not files:
            continue
        files.sort(key=lambda f: abs(f["height"] - target_height))
        url = files[0]["link"]
        used_ids.add(video.get("id"))
        with requests.get(url, stream=True, timeout=180) as dl:
            dl.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in dl.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        try:
            BROLL_CACHE.mkdir(parents=True, exist_ok=True)
            cached = BROLL_CACHE / f"pexels_{video.get('id')}.mp4"
            if not cached.exists():
                shutil.copyfile(out_path, cached)
        except OSError:
            pass
        return True
    return False

def _cache_clip(out_path: Path, used_cache: set) -> bool:
    clips = [p for p in sorted(BROLL_CACHE.glob("*.mp4")) if p.name not in used_cache]
    if not clips:
        return False
    pick = random.choice(clips)
    used_cache.add(pick.name)
    shutil.copyfile(pick, out_path)
    return True

def _gradient_clip(seconds: float, index: int, out_path: Path, width: int, height: int, fps: int) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"gradients=s={width}x{height}:d={seconds:.2f}:speed=0.05:seed={index * 7 + 1}",
            "-r", str(fps), "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            str(out_path),
        ],
        check=True, capture_output=True,
    )

def _entity_cache_key(research: dict) -> str:
    """Generate a stable cache key for the entity based on the legend/incident."""
    topic = research.get("topic", "").lower()
    location = research.get("location", "").lower()
    key = f"{topic}_{location}".replace(" ", "_").replace(",", "").replace("/", "_")
    return key[:80]

def _get_cached_entity_image(entity_key: str, width: int, height: int, style: str) -> Path | None:
    """Check if we have a cached entity image for this legend."""
    ENTITY_CACHE.mkdir(parents=True, exist_ok=True)
    cached_files = list(ENTITY_CACHE.glob(f"{entity_key}_*.jpg"))
    if cached_files:
        return cached_files[0]
    return None

def _save_entity_image(entity_key: str, src_path: Path, width: int, height: int) -> Path:
    """Save the generated entity image to cache."""
    ENTITY_CACHE.mkdir(parents=True, exist_ok=True)
    dst = ENTITY_CACHE / f"{entity_key}_{width}x{height}.jpg"
    shutil.copyfile(src_path, dst)
    return dst

def _enhance_search_term(term: str, script_context: str, research: dict) -> str:
    """Enhance search term with context for better relevance."""
    term_lower = term.lower()
    
    # Add location context if missing
    location = research.get("location", "") if research else ""
    prefecture = ""
    if location:
        parts = location.split(",")
        if len(parts) >= 1:
            prefecture = parts[0].strip()
    
    # Map vague terms to specific visuals
    enhancements = {
        "kids": "children playing",
        "children": "children walking to school",
        "people": "pedestrians walking",
        "person": "figure walking alone",
        "figure": "silhouette in distance",
        "shadow": "shadow on wall",
        "entity": "pale figure in darkness",
        "ghost": "translucent figure in hallway",
        "creature": "unnatural shape in shadows",
        "monster": "distorted humanoid in dark",
        "police": "police car night japan",
        "evidence": "evidence bag police",
        "document": "police report document",
        "shrine": "shinto shrine torii gate",
        "temple": "buddhist temple gate",
        "school": "japanese school building",
        "hospital": "abandoned hospital corridor",
        "hotel": "ryokan hallway paper doors",
        "station": "train platform night empty",
        "tunnel": "dark tunnel entrance",
        "well": "stone well cover moss",
        "bathroom": "public bathroom stall door",
        "thread": "red thread on tile floor",
        "locker": "coin locker station",
        "taxi": "taxi night rain japan",
        "train": "train interior night",
    }
    
    for vague, specific in enhancements.items():
        if vague in term_lower:
            return specific + (" " + prefecture if prefecture else "")
    
    # Add prefecture context for location terms
    if prefecture and prefecture.lower() not in term_lower:
        return f"{term} {prefecture}"
    
    return term

def scene_prompt_list(terms: list, prompts) -> list | None:
    if isinstance(prompts, list) and len(prompts) == len(terms) \
            and all(isinstance(p, str) and p.strip() for p in prompts):
        return [p.strip() for p in prompts]
    return None

def fetch_clips(search_terms: list, seconds_each: float, config: dict, workdir: Path,
                ai_prompts: list | None = None, research: dict | None = None) -> list:
    """Return a list of raw clip paths, one per search term (order preserved).
    
    Stock-first approach: 85% Pexels stock footage, 15% AI accents for supernatural elements.
    Entity caching: first AI image per legend cached and reused.
    Visual anchors: recurring objects (notebook, lamp, coffee) inserted as transitions.
    Enhanced relevance: search terms enriched with location/entity context.
    """
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    video_cfg = config["video"]
    orientation = "portrait" if video_cfg["height"] > video_cfg["width"] else "landscape"
    fallback_terms = list(video_cfg.get("fallback_search_terms", []))
    random.shuffle(fallback_terms)
    
    stock_primary = video_cfg.get("stock_primary", True)
    ai_ratio = float(video_cfg.get("ai_image_ratio", 0.15))
    entity_cache_enabled = video_cfg.get("entity_cache", True)
    visual_anchors = video_cfg.get("visual_anchors", [])
    
    paths = []
    used_ids: set = set()
    used_cache: set = set()
    
    # Determine entity key for caching
    entity_key = _entity_cache_key(research) if research and entity_cache_enabled else None
    entity_image_path = None
    if entity_key:
        entity_image_path = _get_cached_entity_image(entity_key, video_cfg["width"], video_cfg["height"], video_cfg.get("ai_style", ""))
        if entity_image_path:
            print(f"  Using cached entity image for: {entity_key}")

    for i, term in enumerate(search_terms):
        out = workdir / f"raw_{i}.mp4"
        got = False
        
        # Enhance search term with context
        enhanced_term = _enhance_search_term(term, "", research)
        
        # Determine if this slot should be AI (supernatural element) or stock
        is_ai_slot = (not stock_primary) or (ai_ratio > 0 and i % max(1, round(1 / ai_ratio)) == 0)
        
        # Check if this scene prompt describes a supernatural entity
        brief = ai_prompts[i] if ai_prompts and i < len(ai_prompts) else term
        is_entity_scene = any(keyword in brief.lower() for keyword in 
            ["entity", "ghost", "figure", "shadow", "eyes", "mask", "hand", "creature", "apparition", "presence", "supernatural", "pale", "distorted", "unnatural"])
        
        if is_ai_slot and is_entity_scene and entity_key and entity_cache_enabled:
            # Try to use cached entity image
            if entity_image_path:
                try:
                    from . import ai_images
                    ai_images.ken_burns(entity_image_path, seconds_each, video_cfg["width"],
                                        video_cfg["height"], video_cfg["fps"], out)
                    print(f"  Using cached entity visual: {entity_key}")
                    got = True
                except Exception as e:
                    print(f"  Cached entity render failed: {e}")
            else:
                # Generate new entity image and cache it
                try:
                    from . import ai_images
                    img = workdir / f"entity_{i}.jpg"
                    # Enhanced entity prompt
                    entity_brief = brief
                    if "figure" in brief.lower() or "entity" in brief.lower():
                        entity_brief = f"pale humanoid figure, elongated proportions, standing in darkness, only eyes visible, analog horror aesthetic, VHS grain"
                    if ai_images.generate_scene_image(entity_brief, video_cfg["width"],
                                                      video_cfg["height"], img,
                                                      style=video_cfg.get("ai_style")):
                        _save_entity_image(entity_key, img, video_cfg["width"], video_cfg["height"])
                        ai_images.ken_burns(img, seconds_each, video_cfg["width"],
                                            video_cfg["height"], video_cfg["fps"], out)
                        print(f"  Generated and cached new entity visual: {entity_key}")
                        got = True
                    img.unlink(missing_ok=True)
                except Exception as e:
                    print(f"  Entity generation failed: {e}")
        
        if not got and is_ai_slot and not is_entity_scene:
            # Non-entity AI slot (atmospheric, environmental)
            try:
                from . import ai_images
                img = workdir / f"ai_{i}.jpg"
                if ai_images.generate_scene_image(brief, video_cfg["width"],
                                                  video_cfg["height"], img,
                                                  style=video_cfg.get("ai_style")):
                    ai_images.ken_burns(img, seconds_each, video_cfg["width"],
                                        video_cfg["height"], video_cfg["fps"], out)
                    print(f"  AI-generated atmospheric visual: '{brief}'")
                    got = True
                img.unlink(missing_ok=True)
            except Exception as e:
                print(f"  AI visual failed for '{term}', using stock: {e}")
        
        # Stock footage (primary) - use enhanced search term
        if not got and api_key:
            queries = [enhanced_term, enhanced_term.split()[0]] + fallback_terms
            for query in queries:
                try:
                    got = _pexels_clip(query, api_key, out, seconds_each, used_ids,
                                       orientation, video_cfg["height"])
                except Exception as e:
                    print(f"  Pexels failed for '{query}': {e}")
                if got:
                    print(f"  Stock footage: '{query}'")
                    break
        
        if not got and _cache_clip(out, used_cache):
            print(f"  Using cached b-roll for '{term}'")
            got = True
        
        if not got:
            print(f"  Using generated background for '{term}' (last resort)")
            _gradient_clip(seconds_each, i, out, video_cfg["width"], video_cfg["height"], video_cfg["fps"])
        
        paths.append(out)
    
    # Insert visual anchors between clips (notebook, lamp, coffee)
    if visual_anchors and len(paths) > 1:
        anchor_paths = []
        for i, clip in enumerate(paths):
            anchor_paths.append(clip)
            if i < len(paths) - 1 and i % 2 == 1:
                anchor_idx = (i // 2) % len(visual_anchors)
                anchor_desc = visual_anchors[anchor_idx]
                anchor_out = workdir / f"anchor_{i}.mp4"
                try:
                    from . import ai_images
                    img = workdir / f"anchor_{i}.jpg"
                    if ai_images.generate_scene_image(anchor_desc, video_cfg["width"],
                                                      video_cfg["height"], img,
                                                      style=video_cfg.get("ai_style")):
                        ai_images.ken_burns(img, seconds_each * 0.5, video_cfg["width"],
                                            video_cfg["height"], video_cfg["fps"], anchor_out)
                        anchor_paths.append(anchor_out)
                        img.unlink(missing_ok=True)
                except Exception as e:
                    print(f"  Visual anchor failed: {e}")
        paths = anchor_paths
    
    return paths