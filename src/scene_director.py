"""Scene Director pass: breaks script into timed visual segments with shot direction.

Takes the structured beats + script from the Writer and produces a scene list
that the visuals and assembly layers can consume directly.

Each scene has:
    - beat type (hook/setup/escalation/climax/twist/linger)
    - narration text for that segment
    - duration in seconds
    - search terms for stock footage
    - AI image prompt for generated visuals
    - shot type (wide/medium/close-up/detail)
    - transition type (cut/fade/dissolve)
"""
import json
import re

SCENE_DIRECTOR_TEMPLATE = """You are the scene director for a horror storytelling YouTube Short. Your job is to break a finished script into visual segments, each with a specific shot and timing.

SCRIPT:
{script}

TARGET DURATION: {target_seconds} seconds (~{target_words} words spoken)
NUMBER OF VISUAL SHOTS: {n_shots}

BEAT STRUCTURE:
The script follows this arc: hook -> setup -> escalation -> climax -> twist -> linger.
You MUST map each sentence to its beat and create scenes that respect this arc.

TASK: Break the script into exactly {n_shots} visual scenes. Each scene covers one or more sentences.

RULES:
1. Each scene gets a duration proportional to its word count relative to the total script.
   - A 10-word scene in a 130-word script (~45s) gets about 3.5 seconds.
   - Hook scenes should be slightly longer (they earn attention).
   - Climax scenes should be slightly shorter (fast cuts = tension).
2. Search terms must be CONCRETE and FILMABLE. Stock libraries have:
   - Places: "abandoned hospital corridor", "shinto shrine torii gate fog", "train platform night"
   - Objects: "old photograph scattered on floor", "single light bulb swinging", "red thread on tile"
   - Actions: "person walking down hallway", "hand reaching for door handle", "camera static surveillance"
   - NEVER abstract: "mystery", "fear", "unknown", "darkness" (too vague)
3. AI image prompts describe a SINGLE STATIC FRAME that illustrates what the narration says during that scene. Include:
   - Subject (what is in the frame)
   - Action (what it is doing, if anything)
   - Lighting (cold fluorescent, warm candlelight, harsh red, etc.)
   - Mood (uneasy, isolated, claustrophobic, etc.)
   - Camera angle (wide shot, close-up, overhead, etc.)
4. Shot types: wide (establishing), medium (scene), close-up (detail/emotion), detail (object)
5. Transitions: cut (default, fast), fade (slow, dreamy), dissolve (time passing)

Return ONLY valid JSON, no markdown, exactly this shape:
{{
  "scenes": [
    {{
      "beat": "hook",
      "text": "the exact narration text for this scene",
      "duration_sec": 5.0,
      "search_terms": ["term1", "term2"],
      "scene_prompt": "detailed image prompt for AI generation",
      "shot_type": "wide",
      "transition": "cut"
    }},
    ...
  ]
}}"""


def direct_scenes(script: str, config: dict, target_seconds: int | None = None) -> list[dict]:
    """Break a script into timed visual scenes.

    Returns list of scene dicts with: beat, text, duration_sec, search_terms,
    scene_prompt, shot_type, transition.
    """
    from . import llm

    if target_seconds is None:
        target_seconds = config.get("video", {}).get("target_seconds", 45)

    target_words = int(target_seconds * 2.6)
    n_shots = config.get("video", {}).get("clips_count", 5)

    prompt = SCENE_DIRECTOR_TEMPLATE.format(
        script=script,
        target_seconds=target_seconds,
        target_words=target_words,
        n_shots=n_shots,
    )

    try:
        result = llm.generate_json(prompt, config)
        scenes = result.get("scenes", [])
        if not scenes:
            return _fallback_scenes(script, n_shots, target_seconds)

        total_dur = sum(s.get("duration_sec", 0) for s in scenes)
        if total_dur > 0 and abs(total_dur - target_seconds) > 5:
            scale = target_seconds / total_dur
            for s in scenes:
                s["duration_sec"] = round(s.get("duration_sec", 3) * scale, 1)

        for i, s in enumerate(scenes):
            s.setdefault("beat", "body")
            s.setdefault("shot_type", "medium")
            s.setdefault("transition", "cut")
            s.setdefault("search_terms", [])
            s.setdefault("scene_prompt", "")
            if isinstance(s.get("search_terms"), str):
                s["search_terms"] = [s["search_terms"]]

        return scenes
    except Exception as exc:
        print(f"    scene director failed: {exc}")
        return _fallback_scenes(script, n_shots, target_seconds)


def _fallback_scenes(script: str, n_shots: int, target_seconds: int) -> list[dict]:
    """Fallback: split script evenly into scenes without LLM."""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', script.strip())
    sentences = [s.strip() for s in sentences if s.strip() and re.search(r'[A-Za-z0-9]', s)]

    if not sentences:
        return []

    per_scene = max(1, len(sentences) // n_shots)
    scenes = []
    for i in range(0, len(sentences), per_scene):
        chunk = sentences[i:i + per_scene]
        text = " ".join(chunk)
        words = len(text.split())
        dur = max(2.0, (words / max(1, len(script.split()))) * target_seconds)

        if i == 0:
            beat = "hook"
        elif i >= len(sentences) - per_scene:
            beat = "linger"
        elif i >= len(sentences) * 0.6:
            beat = "climax"
        else:
            beat = "setup"

        scenes.append({
            "beat": beat,
            "text": text,
            "duration_sec": round(dur, 1),
            "search_terms": [],
            "scene_prompt": "",
            "shot_type": "medium",
            "transition": "cut",
        })

    return scenes


def scenes_to_search_terms(scenes: list[dict]) -> list[str]:
    """Extract flat search terms list from scene list for backwards compatibility."""
    terms = []
    for s in scenes:
        for t in s.get("search_terms", []):
            if t not in terms:
                terms.append(t)
    return terms


def scenes_to_scene_prompts(scenes: list[dict]) -> list[str]:
    """Extract flat scene prompts list for backwards compatibility."""
    return [s.get("scene_prompt", "") for s in scenes]
