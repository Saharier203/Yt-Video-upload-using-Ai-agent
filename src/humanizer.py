"""Light-touch humanizer pass: strip AI-isms, inject delivery annotations.

Sits between the Story Writer and the Critic. Does NOT rewrite the story --
only cleans up robotic phrasing and adds inline delivery markers that the
TTS engine (tts.py) will parse into rate/pitch/pause adjustments.

Delivery annotations:
    [pause]      -- extra silence after this sentence
    [slower]     -- reduce speech rate for this sentence
    [whisper]    -- lower pitch + slower for intimacy
    [emphasis]   -- slight rate increase + pitch bump for impact
"""
import json
import re

HUMANIZER_TEMPLATE = """You are a script humanizer for a horror storytelling channel. Your job is LIGHT-TOUCH cleanup -- you preserve the writer's voice and rhythm, you do NOT rewrite the story.

INPUT SCRIPT:
{script}

YOUR TASK -- do these 4 things, nothing else:

1. STRIP AI PHRASES. Replace these with direct, concrete language:
   - "However, things were about to take an unexpected turn." -> cut it, use the next specific detail instead
   - "It was a dark and stormy night" -> cut it
   - "Little did they know" -> cut it
   - "In a world where..." -> cut it
   - "This is the story of..." -> cut it
   - "Legend has it" / "Folklore tells us" / "According to the report" -> cut it or rephrase as direct observation
   - "Chilling" / "Spine-tingling" / "Bone-chilling" -> cut it
   - "However" / "Nevertheless" / "Subsequently" / "Consequently" -> use "But" / "So" / "Then"
   - "Utilize" -> "use", "Commence" -> "start", "Investigate" -> "look into"
   - "An air of unease settled over..." -> cut it
   - Any sentence that EXPLAINS the emotion instead of CREATING it

2. FIX REPETITIVE STRUCTURE. If 3+ sentences start the same way (e.g., "The... The... The..." or "And... And... And..."), vary the openings. Short punchy fragments are fine.

3. REMOVE UNNECESSARY EXPLANATIONS. If the story shows something scary, don't also tell the listener it's scary. Trust them. Cut sentences like "This was deeply unsettling" or "The implications were disturbing."

4. INJECT DELIVERY ANNOTATIONS. Add these markers to help the voice actor:
   - [pause] -- after a sentence that needs a beat of silence to land (before a reveal, after a disturbing detail, before the final line)
   - [slower] -- on sentences that should be delivered slowly (creeping tension, describing something wrong)
   - [whisper] -- on intimate, quiet moments (someone speaking softly, a secret, something barely audible)
   - [emphasis] -- on the ONE sentence in each section that carries the most impact (the twist, the punchline, the key detail)

RULES:
- Keep the script essentially the same. You are a COPY EDITOR, not a rewriter.
- Do NOT add new sentences, new details, or new words that weren't in the original.
- Do NOT change the story, the facts, or the order of events.
- Do NOT add more than 2-3 delivery markers per 5 sentences. Over-marking kills the effect.
- The output must be the cleaned script as plain text, with delivery markers inline.
- Do NOT output JSON. Just the script text with markers."""

TITLE_TEMPLATE = """Clean up this YouTube Short title. Rules:
- Under 90 characters
- Must end with #Shorts
- Curiosity-driven, not clickbait
- No AI phrases (" chilling", " spine-tingling", etc.)
- If it already follows these rules, return it unchanged

Title: {title}

Return ONLY the cleaned title, nothing else."""


def humanize_script(script: str, config: dict) -> str:
    """Run the humanizer pass on a script. Returns cleaned script with delivery annotations."""
    from . import llm

    prompt = HUMANIZER_TEMPLATE.format(script=script)
    try:
        result = llm.generate(prompt, config)
        result = result.strip()
        if not result:
            return script
        return result
    except Exception as exc:
        print(f"    humanizer failed: {exc}")
        return script


def clean_title(title: str, config: dict) -> str:
    """Light cleanup on the YouTube title."""
    from . import llm

    prompt = TITLE_TEMPLATE.format(title=title)
    try:
        result = llm.generate(prompt, config)
        result = result.strip().strip('"').strip("'")
        if "#shorts" not in result.lower():
            result = result.rstrip() + " #Shorts"
        return result[:100]
    except Exception:
        if "#shorts" not in title.lower():
            return title.rstrip() + " #Shorts"
        return title[:100]


def parse_delivery_annotations(text: str) -> list[dict]:
    """Parse delivery annotations from script text.

    Returns list of (cleaned_sentence, annotations) tuples.
    annotations is a dict like {"pause": True, "slower": True, ...}
    Also returns the cleaned text with markers stripped.
    """
    annotations = {"pause": False, "slower": False, "whisper": False, "emphasis": False}

    marker_pattern = re.compile(r'\[(pause|slower|whisper|emphasis)\]')

    found = marker_pattern.findall(text)
    for m in found:
        annotations[m] = True

    cleaned = marker_pattern.sub('', text).strip()
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)

    return cleaned, annotations


def strip_all_annotations(text: str) -> str:
    """Strip all delivery annotations from text, returning clean text for TTS."""
    cleaned = re.sub(r'\[(pause|slower|whisper|emphasis)\]', '', text)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned
