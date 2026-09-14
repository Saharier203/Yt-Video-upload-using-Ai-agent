"""Daily topic selection + script/metadata generation for horror storytelling."""
import json
import re
from datetime import date
from pathlib import Path

from . import llm
from . import humanizer

HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "topics_history.json"

EDITORIAL_DEFAULTS = {
    "cta": "",
    "item_noun": "story",
    "banned_topics": "generic jump-scare lists, overdone creepypasta without documentation, clickbait 'real footage' claims, gore for shock value",
    "banned_kinds": "dry encyclopedia entries, lists without narrative stakes, anything that breaks immersion, forced humor, jokes at victims' expense, invented dialogue or thoughts",
    "stakes": "the gap between official accounts and lived experience; what these stories reveal about what we choose not to explain",
    "prefer": "global myths with specific locations, famous unsolved mysteries with documented investigations, speculative scenarios grounded in science, true crime with narrative depth, unexplained phenomena with witness testimony",
    "strongest_angles": "myths that persist across cultures, mysteries where the official explanation creates more questions, scenarios grounded in real science, encounters with witnesses who have nothing to gain",
    "hook_examples": "Bad: 'Japan has many scary legends.' Good: 'In March 1994, a woman vanished from a locked bathroom in Kyoto. The only evidence: a single red thread wrapped around the toilet handle.' Better: 'The last train clears Platform 3 at 12:17 AM. The motion sensor triggers at 12:23. The platform is empty. The sensor doesn't lie.'",
    "visual_direction": "Prioritize: actual location exteriors (shrines, stations, hospitals, forests, cities), archival document aesthetics (police reports, newspaper clippings, evidence bags), night streets in specific cities, foggy forests, abandoned corridors, sealed rooms, redacted documents. Avoid: bright daylight, cartoonish monsters, blood/gore, jump-scare imagery. Style: 1990s analog horror aesthetic — VHS static, CRT scanlines, muted teal/orange grading, deep shadows, film grain 35mm, slightly desaturated, high contrast, photorealistic.",
    "extra_rules": "Never reveal the entity fully. Suggestion > exposition. Every story must have a specific location (real city, station, forest, building). Include one sensory detail: a smell, a sound, a temperature drop. Dry gallows humor at the expense of official explanations only. No CTA. No 'subscribe'. The story is the hook. Write sentences that flow naturally when spoken — each sentence must end with a clear pause.",
    "structure_detail": "hook → setup → escalation → climax → twist → linger",
    "narrative_beats": [
      "HOOK: specific, visual, immediate curiosity gap",
      "SETUP: world-building, normal routine, stakes",
      "ESCALATION: things go wrong, tension builds, cause->effect",
      "CLIMAX: the moment of horror/revelation",
      "TWIST: the detail that changes everything / institutional failure",
      "LINGER: final image/question that haunts"
    ],
    "humor_rules": "dry, gallows, at the expense of official explanations only. never at victims.",
    "forbidden": "jumpscares, gore, explained monsters, happy endings, 'subscribe', 'comment below', 'like and subscribe', dramatic music stings, vague 'studies show' language, invented dialogue, invented thoughts, invented timing, invented reactions",
    "required_per_video": [
      "specific grounding detail (place/time/source)",
      "normal baseline before disruption",
      "escalation with cause->effect",
      "one institutional absurdity or logical gap",
      "one sensory detail (smell/sound/temperature/texture)",
      "one unanswered question or lingering image"
    ]
}

def editorial(config: dict) -> dict:
    return {**EDITORIAL_DEFAULTS, **(config.get("editorial") or {})}

RESEARCH_TEMPLATE = """You are the research lead for a horror storytelling channel: "Dark Archives."

Niche: {niche}
Persona: {persona}
Today's date: {today}

Topics already covered (NEVER repeat or closely paraphrase these):
{history}

Live audience data from this channel's past uploads:
{performance}
Steer toward the emotional angle and sub-theme flavor of the overperformers and away from the underperformers — but NEVER repeat or paraphrase a covered topic.

Task: Silently consider several candidate horror stories from DIFFERENT categories (avoiding categories of the most recent topics above), then pick the ONE best story with strong documented basis and extract its concrete details.

ABSOLUTE rule — real basis only:
- The story must come from actual folklore, documented events, witness testimony, news archives, or scientific speculation. NEVER invent a story, a name, a detail, or a specific claim. If you are not confident every detail below is grounded in something real, pick a different story you are sure of.
- The value of the video IS the specifics: the exact location, the exact time period, the exact source type, and the exact detail that makes it unsettling.

CRITICAL selection rules:
- Obscurity is the product: most viewers must NEVER have heard this specific version. BANNED: anything a casual viewer knows from TikTok or common creepypasta (e.g. {banned_topics}). A famous legend is allowed ONLY via a buried documented detail that flips it.
- Prefer: {prefer}.
- Direct stakes: {stakes}. The viewer should feel the weight of the gap between what's told and what happened.
- Strongest angles: {strongest_angles}.

Return ONLY valid JSON, no markdown, exactly this shape:
{{
  "topic": "short internal label for the story",
  "story": "the story in one plain sentence a 15-year-old instantly understands",
  "category": "myth / unsolved_mystery / speculative_scenario / true_crime / phenomenon / cryptid / historical_anomaly / urban_legend",
  "date": "exact date (YYYY-MM-DD or Month YYYY) or time period",
  "location": "exact location: Country, Region, Specific Place",
  "source_type": "folklore / witness_testimony / news_archive / historical_record / scientific_speculation / police_record / court_record",
  "source_reference": "specific reference: collection name, witness name/role, newspaper name/date, archive reference",
  
  // THE STORY ELEMENTS - only what is documented or genuinely speculated
  "place_description": "what this place was like normally - grounded, specific, atmospheric",
  "normal_routine": "what was happening normally before the disruption - the calm before",
  "what_changed": "the moment things shifted - the inciting incident",
  "what_happened": "the core horror event - what actually occurred",
  "witness_account": "what witnesses said they experienced (name/role if available, or 'anonymous [role]') - ONLY if documented",
  "official_account": "what authorities/experts officially said - ONLY if documented",
  "the_contradiction": "the specific detail that makes the official/simple explanation impossible",
  "sensory_detail": "one sensory detail from the record: smell, sound, temperature, texture",
  "institutional_absurdity": "one dry observation about the absurdity of the official/simple explanation",
  "unresolved_thread": "one specific unanswered question that haunts"
}}"""

SCRIPT_TEMPLATE = """You are the head writer for "Dark Archives" — a horror storytelling channel.

Niche: {niche}
Persona: {persona}
Today's date: {today}

Your research lead already picked today's story and verified the facts. This is the ONLY source material; write strictly from it and never invent or embellish beyond it:
{research}

RULES FOR THE SCRIPT — READ CAREFULLY:

1. NO INVENTED DETAILS. Every sentence must be grounded in the research JSON above.
   - If the research doesn't say who was there, don't write "a passenger noticed."
   - If the research doesn't give a time, don't write "it was late evening."
   - If the research doesn't describe a reaction, don't write "they froze."

2. NARRATIVE PROGRESSION — follow this sequence using ONLY documented facts:
   
   BEAT 1 — HOOK: Open with a specific, visual detail that creates immediate curiosity.
   "The last train clears Platform 3 at 12:17 AM. The motion sensor triggers at 12:23. The platform is empty."
   "In 1994, a woman vanished from a locked bathroom in Kyoto. The only evidence: a red thread on the toilet handle."
   
   BEAT 2 — SETUP: Establish the normal world. Ground the viewer in routine.
   "The last train on the Chuo Line usually clears the station by 12:17 AM."
   "The village of Iino was quiet, a mountain town where the biggest event was the summer festival."
   
   BEAT 3 — ESCALATION: What shifts. Cause -> effect. Tension builds.
   "Then the motion sensor on Platform 3 triggered at 12:23 AM. The platform was empty."
   "Then the televisions and radios in the village died. All at once."
   
   BEAT 4 — CLIMAX: The horror moment. The revelation.
   "The sensor doesn't lie. Something was standing on Platform 3."
   "A massive triangular craft hovered over Mount Senganmori. Silent. Absorbing light."
   
   BEAT 5 — TWIST: The detail that breaks the simple explanation.
   "The police report called it a weather balloon. But a balloon doesn't navigate against gale-force winds."
   "The official report called it a weather balloon. But a balloon doesn't hover stationary against gale-force winds."
   
   BEAT 6 — LINGER: The final image/question that haunts.
   "The red thread is still in locker 447. Want to know what DNA was on it? So do I."
   "The town of Iino now markets itself as a 'UFO Capital.' The police file still says there was nothing there."

3. SENTENCE STYLE — simple, clear, spoken English:
   - Short sentences. Period. Not commas. One idea per sentence.
   - Example: "The train left. The platform was empty. Then the sensor beeped."
   - No fancy words. No "utilize", "consequently", "furthermore". Use "use", "so", "also".
   - Talk like a person. "I heard..." "They saw..." "It happened..."
   - Short punchy for scary parts: "The door opened. Nothing there."
   - Longer only for setting scene: "The village was quiet. Just a mountain town with one road in."
   - Transitions: "But here is the thing." "That is not the weird part."
   - Cause then effect: "The power cut. The lights died."
   - Uncertainty okay: "The report says unknown. Not human. Unknown."
   - End with image or question: "The thread is still in the locker. What was on it?"

4. BANNED: "Studies show," "legend has it," "folklore tells us," invented dialogue, invented thoughts, invented timing, invented reactions, "suddenly" unless documented, "little did they know," "chilling," "spine-tingling," "bone-chilling," "Police Report #", "Case #", "Report #", "Incident #", "File #", "Log #", "official log states", "official record states", "according to the report", "according to police", "according to authorities".

5. TONE: Someone telling a scary story to a friend. Simple words. Short sentences. Like you're talking to someone at 3 AM. No fancy words. Just the story.

6. NO CTA. No "subscribe." No "like." No "comment below." The story is the hook.

7. Total length {target_words} words (~{target_seconds} seconds spoken).

Return ONLY valid JSON, no markdown, exactly this shape:
{{
  "topic": "short internal label for the topic",
  "title": "YouTube title under 90 chars, curiosity-driven, ends with #Shorts",
  "description": "2-3 sentence description with a hook and 3-5 hashtags on the last line",
  "tags": ["8-12", "seo", "tags"],
  "script": "the full spoken script as one string",
  "beats": [
    {{"beat": "hook", "text": "the hook sentence(s)", "intensity": "high"}},
    {{"beat": "setup", "text": "the setup sentence(s)", "intensity": "low"}},
    {{"beat": "escalation", "text": "the escalation sentence(s)", "intensity": "medium"}},
    {{"beat": "climax", "text": "the climax sentence(s)", "intensity": "high"}},
    {{"beat": "twist", "text": "the twist sentence(s)", "intensity": "medium"}},
    {{"beat": "linger", "text": "the linger sentence(s)", "intensity": "low"}}
  ],
  "music_mood": "suspense",
  "comment": "a short question (under 20 words) to post as the channel's own comment, written to provoke replies and personal stories",
  "playlist": "exactly one of: {playlists}",
  "search_terms": ["5 stock-video search phrases (2-3 words each), IN CHRONOLOGICAL ORDER matching the script's narrative from hook to ending. Each must be a concrete filmable subject that exists in stock libraries (places, objects, actions) — never abstract concepts. e.g. 'Kyoto shrine torii gate fog', 'police evidence bag closeup', 'abandoned hotel hallway night'"],
  "scene_prompts": ["5 illustration briefs, one per search term, SAME ORDER. Each describes the single picture that TEACHES what the script is saying during that scene: the subject, what they are doing, and the one visual detail that carries the point. Turn abstract ideas into physical metaphors. 15-25 words, present tense, no text or lettering in the picture. e.g. 'a red thread lies on a white tile bathroom floor next to a toilet, the only thing in an otherwise empty room'"]
}}"""

CRITIC_TEMPLATE = """You are a ruthless editor for a horror storytelling channel. A viewer gives this script 1.5 seconds to earn attention and 45 seconds to show them a story they'll remember for weeks. Judge it coldly.

Script:
{script}

Return ONLY valid JSON, no markdown, exactly this shape:
{{
  "learned": "the one concrete fact a viewer walks away with, stated plainly — empty string if there isn't one",
  "has_specifics": true or false — does it contain at least one real date, location, source reference, or documented detail (not vague claims)",
  "surprise": 1-10 — would a jaded viewer genuinely go "wait, WHAT?" at the documented gap",
  "clarity": 1-10 — zero jargon, every sentence instantly understandable",
  "craving": 1-10 — does the ending make them want the next story and to comment",
  "interactive": 1-10 — does it speak TO the viewer and hand them something to DO (visit, search, check) or something to SAY (a question they would actually answer)",
  "flow": 1-10 — do sentences end cleanly with natural pauses? No words running together. No run-on sentences.",
  "horror_atmosphere": 1-10 — does the delivery feel like a horror story told at 3 AM? Not a podcast, not a report. A story.",
  "no_invention": 1-10 — zero invented details, dialogue, thoughts, timing, or reactions not in source",
  "humor_quality": 1-10 — is humor dry, gallows, at expense of official explanations only? Zero victim jokes, zero puns.",
  "format_compliance": true or false — does it follow the 6-beat structure: hook → setup → escalation → climax → twist → linger?",
  "verdict": "pass" or "fail" — fail if has_specifics is false, or surprise < 7, or clarity < 7, or interactive < 7, or flow < 7, or horror_atmosphere < 7, or no_invention < 7, or humor_quality < 7, or format_compliance is false",
  "critique": "if fail: the 2-3 concrete changes that would fix it, referencing exact sentences"
}}"""

def load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8-sig"))
    return []


def save_history_entry(entry: dict) -> None:
    history = load_history()
    history.append(entry)
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def generate_video_plan(config: dict, forced_topic: str | None = None) -> dict:
    history = load_history()
    recent = [h["topic"] for h in history[-60:]]
    target_seconds = config["video"]["target_seconds"]
    try:
        from . import analytics
        performance = analytics.performance_block()
    except Exception as exc:
        print(f"    performance signal skipped: {exc}")
        performance = "(no performance data yet — pick purely on the scoring rules)"
    ed = editorial(config)
    qm = llm.quality_model(config)
    common = dict(
        niche=config["niche"],
        persona=config["channel_persona"],
        today=date.today().isoformat(),
    )

    # Pass 1 — research: pick one real story and pin down its specifics.
    research_prompt = RESEARCH_TEMPLATE.format(
        performance=performance,
        history="\n".join(f"- {t}" for t in recent) if recent else "(none yet)",
        **common, **ed,
    )
    if forced_topic:
        research_prompt += f"\n\nOverride: the story MUST be about: {forced_topic}"
    research = llm.generate_json(research_prompt, config, model=qm)
    topic_str = research.get('topic', '')
    loc_str = research.get('location', '')
    src_str = research.get('source_type', '')
    # Handle Unicode for Windows console
    try:
        print(f"    research: {topic_str} | {loc_str} | {src_str}")
    except UnicodeEncodeError:
        print(f"    research: {topic_str.encode('ascii', 'replace').decode()} | {loc_str.encode('ascii', 'replace').decode()} | {src_str}")

    # Pass 2 — write the script strictly from the researched facts.
    write_prompt = SCRIPT_TEMPLATE.format(
        research=json.dumps(research, indent=2, ensure_ascii=False),
        target_words=int(target_seconds * 2.6),
        target_seconds=target_seconds,
        playlists=", ".join(config.get("playlists", ["Global Myths & Legends"])),
        **common, **ed,
    )
    plan = llm.generate_json(write_prompt, config, model=qm)

    # Pass 2.5 — humanizer: strip AI-isms, inject delivery annotations
    raw_script = plan.get("script", "")
    if raw_script and config.get("humanizer", {}).get("enabled", True):
        try:
            print("    humanizer: cleaning script...")
            humanized = humanizer.humanize_script(raw_script, config)
            plan["script"] = humanized
            plan["script_raw"] = raw_script
            print(f"    humanizer: done ({len(raw_script)} -> {len(humanized)} chars)")
        except Exception as exc:
            print(f"    humanizer skipped: {exc}")

    # Pass 2.7 — scene director: break script into timed visual segments
    from . import scene_director
    try:
        print("    scene director: breaking script into scenes...")
        scenes = scene_director.direct_scenes(plan.get("script", ""), config, target_seconds)
        plan["scenes"] = scenes
        if not plan.get("search_terms"):
            plan["search_terms"] = scene_director.scenes_to_search_terms(scenes)
        if not plan.get("scene_prompts"):
            plan["scene_prompts"] = scene_director.scenes_to_scene_prompts(scenes)
        print(f"    scene director: {len(scenes)} scenes created")
    except Exception as exc:
        print(f"    scene director skipped: {exc}")

    # Pass 3 — critic gate: one revision round
    try:
        review = llm.generate_json(
            CRITIC_TEMPLATE.format(script=plan.get("script", "")), config, model=qm)
        if str(review.get("verdict", "pass")).strip().lower() == "pass":
            print(f"    critic: pass | learns: {str(review.get('learned'))[:90]}")
        else:
            print(f"    critic: fail | {str(review.get('critique'))[:180]}")
            retry_prompt = write_prompt + (
                "\n\nYour previous draft FAILED editorial review. The review:\n"
                + json.dumps(review, indent=2, ensure_ascii=False)
                + "\nRewrite the video fixing every point in the critique. "
                  "Same JSON shape, all the same rules.")
            plan = llm.generate_json(retry_prompt, config, model=qm)
    except Exception as exc:
        print(f"    critic gate skipped: {exc}")
    
    for key in ("topic", "title", "description", "tags", "script", "search_terms"):
        if key not in plan:
            raise RuntimeError(f"LLM plan missing key: {key}")

    if "#shorts" not in plan["title"].lower():
        plan["title"] = plan["title"].rstrip() + " #Shorts"

    if "beats" not in plan:
        from . import assemble
        plan["beats"] = assemble._extract_script_beats(plan.get("script", ""))

    if "scenes" not in plan:
        try:
            from . import scene_director
            plan["scenes"] = scene_director.direct_scenes(plan.get("script", ""), config, target_seconds)
        except Exception:
            plan["scenes"] = []

    plan["research"] = research
    return plan