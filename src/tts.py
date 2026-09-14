"""
Horror Voiceover Engine
-----------------------

Microsoft Edge Neural TTS voiceover generator designed for
automated horror YouTube content.

Features:
- Sentence-by-sentence synthesis
- Horror-oriented pacing
- Hook / body / tension / reveal / aftermath / final delivery
- Controlled rate and pitch
- Natural punctuation-aware pauses
- Explicit silence between sentences
- Accurate word-level timestamps
- Delivery annotations: [pause], [slower], [whisper], [emphasis]
- Retry handling for temporary Edge TTS failures
- Temporary-file cleanup
- Pipeline-friendly interface

Main function:

    make_voiceover(text, config, out_mp3)

Returns:

    [
        {
            "word": "word",
            "start": 0.52,
            "end": 0.81
        },
        ...
    ]

All timestamps are relative to the FINAL generated MP3.
"""

import asyncio
import re
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple

import edge_tts


# ============================================================
# DELIVERY ANNOTATIONS
# ============================================================

ANNOTATION_PATTERN = re.compile(r'\[(pause|slower|whisper|emphasis)\]')


def _parse_annotations(text: str) -> Tuple[str, List[Dict]]:
    """Parse delivery annotations from script text.

    Returns (cleaned_text, per_sentence_annotations).
    Each entry in per_sentence_annotations is a dict of annotation flags.
    """
    sentences = _split_sentences(text)
    annotations = []

    for sent in sentences:
        flags = {"pause": False, "slower": False, "whisper": False, "emphasis": False}
        for m in ANNOTATION_PATTERN.findall(sent):
            if m in flags:
                flags[m] = True
        cleaned = ANNOTATION_PATTERN.sub('', sent).strip()
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        annotations.append((cleaned, flags))

    return annotations


def _strip_annotations(text: str) -> str:
    """Strip all delivery annotations from text."""
    cleaned = ANNOTATION_PATTERN.sub('', text)
    return re.sub(r'\s{2,}', ' ', cleaned).strip()


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_RATE = "-2%"
DEFAULT_PITCH = "-2Hz"

MIN_PAUSE = 0.08
MAX_PAUSE = 2.50


# ============================================================
# TEXT CLEANING
# ============================================================

def _clean_text(text: str) -> str:
    """
    Clean the input script while preserving punctuation.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# SENTENCE SPLITTER
# ============================================================

def _split_sentences(text: str) -> List[str]:
    """
    Split narration into individual sentence units.

    Handles:
        .
        !
        ?
        ...
        quotes
        dialogue

    Does not depend on the next character being uppercase.
    """

    text = _clean_text(text)

    if not text:
        return []

    # Protect common abbreviations
    abbreviations = [
        "Mr.",
        "Mrs.",
        "Ms.",
        "Dr.",
        "Prof.",
        "St.",
        "Jr.",
        "Sr.",
        "e.g.",
        "i.e.",
    ]

    protected = text

    for i, abbreviation in enumerate(abbreviations):
        protected = protected.replace(
            abbreviation,
            f"__ABBR_{i}__"
        )

    # Split after sentence-ending punctuation.
    #
    # Examples:
    #
    # "I heard something. Then I ran."
    #
    # "Who's there?" I asked.
    #
    # "It stopped..." Then silence.
    #
    parts = re.split(
        r'(?<=[.!?])(?:["\'\)]*)\s+',
        protected
    )

    sentences = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        # Restore abbreviations
        for i, abbreviation in enumerate(abbreviations):
            part = part.replace(
                f"__ABBR_{i}__",
                abbreviation
            )

        # Ignore empty/non-text pieces
        if re.search(r"[A-Za-z0-9]", part):
            sentences.append(part)

    return sentences


# ============================================================
# RATE / PITCH HELPERS
# ============================================================

def _fmt_rate(base: str, delta: int) -> str:
    """
    Modify Edge TTS rate.

    Example:

        "+5%" + (-5)
        -> "+0%"
    """

    value = int(
        base
        .replace("%", "")
        .replace("+", "")
        .strip()
    )

    value += delta

    return f"{value:+d}%"


def _fmt_pitch(base: str, delta: int) -> str:
    """
    Modify Edge TTS pitch.

    Example:

        "-2Hz" + (-3)
        -> "-5Hz"
    """

    value = int(
        base
        .replace("Hz", "")
        .replace("+", "")
        .strip()
    )

    value += delta

    return f"{value:+d}Hz"


def _clamp_pause(seconds: float) -> float:
    """
    Prevent extremely short or extremely long pauses.
    """

    return max(
        MIN_PAUSE,
        min(MAX_PAUSE, seconds)
    )


# ============================================================
# SENTENCE ROLE DETECTION
# ============================================================

def _sentence_type(
    index: int,
    total: int,
    sentence: str
) -> str:
    """
    Determine the role of a sentence in the horror story.

    Possible roles:

        hook
        body
        tension
        reveal
        aftermath
        final
    """

    text = sentence.strip().lower()

    # --------------------------------------------------------
    # FIRST SENTENCE = HOOK
    # --------------------------------------------------------

    if index == 0:
        return "hook"

    # --------------------------------------------------------
    # LAST SENTENCE = FINAL
    # --------------------------------------------------------

    if index == total - 1:
        return "final"

    # --------------------------------------------------------
    # SECOND LAST = AFTERMATH
    # --------------------------------------------------------

    if index == total - 2:
        return "aftermath"

    # --------------------------------------------------------
    # VERY SHORT SENTENCES = TENSION
    # --------------------------------------------------------

    word_count = len(text.split())

    if word_count <= 5:
        return "tension"

    # --------------------------------------------------------
    # REVEAL DETECTION
    # --------------------------------------------------------

    reveal_starters = [
        "but",
        "then",
        "suddenly",
        "until",
        "when",
        "behind",
        "inside",
        "that night",
        "the door",
        "the voice",
        "someone",
        "something",
        "i saw",
        "we saw",
        "he saw",
        "she saw",
        "there was",
        "there were",
    ]

    for phrase in reveal_starters:

        if text.startswith(phrase):
            return "reveal"

    # --------------------------------------------------------
    # NORMAL BODY
    # --------------------------------------------------------

    return "body"


# ============================================================
# PUNCTUATION PAUSE
# ============================================================

def _punctuation_pause(sentence: str) -> float:
    """
    Add additional pause based on punctuation.

    Horror scripts often use:

        ...
        —
        :
        ;

    to create dramatic timing.
    """

    pause = 0.0

    # Ellipsis
    if "..." in sentence:
        pause += 0.35

    # Em dash
    if "—" in sentence:
        pause += 0.20

    # Double dash
    if "--" in sentence:
        pause += 0.20

    # Colon
    if ":" in sentence:
        pause += 0.12

    # Semicolon
    if ";" in sentence:
        pause += 0.08

    return _clamp_pause(pause)


# ============================================================
# HORROR PROSODY PLANNER
# ============================================================

def _plan_prosody(
    sentences: List[str],
    base_rate: str,
    base_pitch: str,
    annotations: List[Dict] | None = None,
) -> List[Tuple[str, str, float, float]]:
    """
    Create horror-oriented prosody for every sentence.

    Returns:

        (
            rate,
            pitch,
            pre_pause,
            post_pause
        )

    Strategy:

        HOOK
          ↓
        BODY
          ↓
        TENSION
          ↓
        REVEAL
          ↓
        AFTERMATH
          ↓
        FINAL

    If annotations are provided, they override the base prosody:
        [pause]      -> extra 0.6s post_pause
        [slower]     -> rate reduced by additional 8%
        [whisper]    -> pitch dropped by additional 6Hz, rate -5%
        [emphasis]   -> rate +3%, pitch +2Hz
    """

    total = len(sentences)

    plan = []

    for i, sentence in enumerate(sentences):

        role = _sentence_type(
            i,
            total,
            sentence
        )

        punctuation_pause = _punctuation_pause(
            sentence
        )

        ann = (annotations or [{}] * total)[min(i, len(annotations or []) - 1)] if annotations else {}

        # ====================================================
        # HOOK
        # ====================================================

        if role == "hook":

            rate = _fmt_rate(
                base_rate,
                -5
            )

            pitch = _fmt_pitch(
                base_pitch,
                -1
            )

            pre_pause = 0.0

            post_pause = (
                0.55
                + punctuation_pause
            )

        # ====================================================
        # BODY
        # ====================================================

        elif role == "body":

            rate = _fmt_rate(
                base_rate,
                0
            )

            pitch = _fmt_pitch(
                base_pitch,
                0
            )

            pre_pause = 0.15

            post_pause = (
                0.22
                + punctuation_pause
            )

        # ====================================================
        # TENSION
        # ====================================================

        elif role == "tension":

            rate = _fmt_rate(
                base_rate,
                -8
            )

            pitch = _fmt_pitch(
                base_pitch,
                -2
            )

            pre_pause = 0.35

            post_pause = (
                0.40
                + punctuation_pause
            )

        # ====================================================
        # REVEAL
        # ====================================================

        elif role == "reveal":

            rate = _fmt_rate(
                base_rate,
                -10
            )

            pitch = _fmt_pitch(
                base_pitch,
                -3
            )

            # Large silence BEFORE reveal
            pre_pause = 0.70

            post_pause = (
                0.65
                + punctuation_pause
            )

        # ====================================================
        # AFTERMATH
        # ====================================================

        elif role == "aftermath":

            rate = _fmt_rate(
                base_rate,
                -6
            )

            pitch = _fmt_pitch(
                base_pitch,
                -2
            )

            pre_pause = 0.55

            post_pause = (
                0.45
                + punctuation_pause
            )

        # ====================================================
        # FINAL
        # ====================================================

        else:

            rate = _fmt_rate(
                base_rate,
                -12
            )

            pitch = _fmt_pitch(
                base_pitch,
                -4
            )

            pre_pause = 0.80

            post_pause = 0.0

        # ====================================================
        # APPLY DELIVERY ANNOTATIONS
        # ====================================================

        if ann.get("pause"):
            post_pause += 0.6

        if ann.get("slower"):
            rate = _fmt_rate(rate, -8)

        if ann.get("whisper"):
            pitch = _fmt_pitch(pitch, -6)
            rate = _fmt_rate(rate, -5)

        if ann.get("emphasis"):
            rate = _fmt_rate(rate, 3)
            pitch = _fmt_pitch(pitch, 2)

        plan.append(
            (
                rate,
                pitch,
                _clamp_pause(pre_pause),
                _clamp_pause(post_pause),
            )
        )

    return plan


# ============================================================
# EDGE TTS SYNTHESIS
# ============================================================

async def _synth(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_path: Path
) -> List[Dict]:
    """
    Synthesize one sentence using Microsoft Edge TTS.

    Also collects word-level timing information.
    """

    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        boundary="WordBoundary",
    )

    words = []

    with open(out_path, "wb") as audio_file:

        async for chunk in communicate.stream():

            # ------------------------------------------------
            # AUDIO
            # ------------------------------------------------

            if chunk["type"] == "audio":

                audio_file.write(
                    chunk["data"]
                )

            # ------------------------------------------------
            # WORD TIMING
            # ------------------------------------------------

            elif chunk["type"] == "WordBoundary":

                start = (
                    chunk["offset"]
                    / 10_000_000
                )

                duration = (
                    chunk["duration"]
                    / 10_000_000
                )

                words.append(
                    {
                        "word": chunk["text"],
                        "start": start,
                        "end": start + duration,
                    }
                )

    if not words:

        raise RuntimeError(
            "Edge TTS returned no word timings "
            f"for: {text[:100]}"
        )

    return words


# ============================================================
# RETRY WRAPPER
# ============================================================

def _synth_with_retry(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_path: Path,
    attempts: int = 4
) -> List[Dict]:
    """
    Retry TTS when Edge temporarily fails.

    Wait time:

        attempt 1 -> 4 sec
        attempt 2 -> 8 sec
        attempt 3 -> 12 sec
        attempt 4 -> final failure
    """

    last_error = None

    for attempt in range(attempts):

        try:

            return asyncio.run(
                _synth(
                    text,
                    voice,
                    rate,
                    pitch,
                    out_path
                )
            )

        except Exception as error:

            last_error = error

            if attempt < attempts - 1:

                wait_time = (
                    4 * (attempt + 1)
                )

                print(
                    f"[TTS] Failed. "
                    f"Retry {attempt + 1}/"
                    f"{attempts - 1} "
                    f"in {wait_time}s..."
                )

                time.sleep(wait_time)

    raise last_error


# ============================================================
# AUDIO DURATION
# ============================================================

def _duration(path: Path) -> float:
    """
    Get exact audio duration using FFprobe.
    """

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(
        result.stdout.strip()
    )


# ============================================================
# SILENCE GENERATOR
# ============================================================

def _silence(
    seconds: float,
    out_path: Path
) -> None:
    """
    Generate silent MP3 audio.
    """

    seconds = _clamp_pause(
        seconds
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            f"{seconds:.3f}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "48k",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )


# ============================================================
# CONCATENATE AUDIO
# ============================================================

def _concat_audio(
    entries: List[Path],
    output: Path,
    workdir: Path
) -> None:
    """
    Concatenate all sentence and silence files.
    """

    concat_list = (
        workdir / "_voice_concat.txt"
    )

    with open(
        concat_list,
        "w",
        encoding="utf-8"
    ) as file:

        for path in entries:

            # Escape single quotes for FFmpeg
            safe_name = path.name.replace(
                "'",
                "'\\''"
            )

            file.write(
                f"file '{safe_name}'\n"
            )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(output),
        ],
        check=True,
        capture_output=True,
        cwd=workdir,
    )


# ============================================================
# CLEANUP
# ============================================================

def _cleanup_files(
    files: List[Path]
) -> None:
    """
    Safely remove temporary files.
    """

    for path in files:

        try:

            if path.exists():
                path.unlink()

        except Exception as error:

            print(
                f"[TTS] Warning: "
                f"could not remove {path}: "
                f"{error}"
            )


# ============================================================
# MAIN FUNCTION
# ============================================================

def make_voiceover(
    text: str,
    config: dict,
    out_mp3: Path
) -> List[Dict]:
    """
    Generate the final horror voiceover.

    Parameters
    ----------
    text:
        Complete narration script.

    config:
        TTS configuration.

    Example:

        config = {
            "tts": {
                "voice": "en-US-ChristopherNeural",
                "rate": "-2%",
                "pitch": "-2Hz",
                "dynamic": True
            }
        }

    out_mp3:
        Path for final MP3.

    Returns
    -------
    List[Dict]

        [
            {
                "word": "I",
                "start": 0.420,
                "end": 0.610
            },
            ...
        ]

    IMPORTANT:

    Timings are already shifted according to:

        sentence audio
        +
        pre silence
        +
        post silence

    Therefore they correspond to the FINAL MP3 timeline.
    """

    # ========================================================
    # PREPARE
    # ========================================================

    out_mp3 = Path(out_mp3)

    out_mp3.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # CONFIG
    # ========================================================

    tts_cfg = config.get(
        "tts",
        {}
    )

    voice = tts_cfg.get(
        "voice",
        DEFAULT_VOICE
    )

    base_rate = tts_cfg.get(
        "rate",
        DEFAULT_RATE
    )

    base_pitch = tts_cfg.get(
        "pitch",
        DEFAULT_PITCH
    )

    dynamic = tts_cfg.get(
        "dynamic",
        True
    )

    # ========================================================
    # SPLIT SCRIPT (with delivery annotation parsing)
    # ========================================================

    annotated = _parse_annotations(text)
    sentences = [cleaned for cleaned, _ in annotated]
    per_sentence_ann = [flags for _, flags in annotated]

    if not sentences:

        raise ValueError(
            "No valid sentences found in script."
        )

    print()
    print("=" * 60)
    print("HORROR TTS")
    print("=" * 60)
    print(
        f"Voice      : {voice}"
    )
    print(
        f"Base rate  : {base_rate}"
    )
    print(
        f"Base pitch : {base_pitch}"
    )
    print(
        f"Sentences  : {len(sentences)}"
    )
    print("=" * 60)
    print()

    # ========================================================
    # SIMPLE MODE
    # ========================================================

    if (
        not dynamic
        or len(sentences) < 3
    ):

        print(
            "[TTS] Dynamic mode disabled."
        )

        words = _synth_with_retry(
            text,
            voice,
            base_rate,
            base_pitch,
            out_mp3
        )

        print(
            f"[TTS] Finished: {out_mp3}"
        )

        return words

    # ========================================================
    # CREATE PROSODY PLAN
    # ========================================================

    prosody = _plan_prosody(
        sentences,
        base_rate,
        base_pitch,
        annotations=per_sentence_ann,
    )

    all_words = []

    concat_entries = []

    temporary_files = []

    cursor = 0.0

    # ========================================================
    # PROCESS SENTENCES
    # ========================================================

    for i, (
        sentence,
        (
            rate,
            pitch,
            pre_pause,
            post_pause
        )
    ) in enumerate(
        zip(sentences, prosody)
    ):

        role = _sentence_type(
            i,
            len(sentences),
            sentence
        )

        ann = per_sentence_ann[i] if i < len(per_sentence_ann) else {}
        ann_tags = " ".join(f"[{k}]" for k, v in ann.items() if v)
        print(
            f"[TTS] "
            f"{i + 1:02d}/"
            f"{len(sentences):02d} "
            f"[{role.upper():9}] "
            f"rate={rate} "
            f"pitch={pitch}"
            f" {ann_tags}" if ann_tags else
            f"[TTS] "
            f"{i + 1:02d}/"
            f"{len(sentences):02d} "
            f"[{role.upper():9}] "
            f"rate={rate} "
            f"pitch={pitch}"
        )

        # ====================================================
        # PRE-SILENCE
        # ====================================================

        if pre_pause > 0:

            silence_path = (
                out_mp3.parent
                / f"_tts_pre_{i}.mp3"
            )

            _silence(
                pre_pause,
                silence_path
            )

            concat_entries.append(
                silence_path
            )

            temporary_files.append(
                silence_path
            )

            cursor += pre_pause

        # ====================================================
        # SENTENCE AUDIO
        # ====================================================

        segment_path = (
            out_mp3.parent
            / f"_tts_segment_{i}.mp3"
        )

        segment_words = _synth_with_retry(
            sentence,
            voice,
            rate,
            pitch,
            segment_path
        )

        segment_duration = _duration(
            segment_path
        )

        # ====================================================
        # SHIFT WORD TIMINGS
        # ====================================================

        for word in segment_words:

            all_words.append(
                {
                    "word": word["word"],

                    "start": round(
                        word["start"]
                        + cursor,
                        3
                    ),

                    "end": round(
                        word["end"]
                        + cursor,
                        3
                    )
                }
            )

        concat_entries.append(
            segment_path
        )

        temporary_files.append(
            segment_path
        )

        cursor += segment_duration

        # ====================================================
        # POST-SILENCE
        # ====================================================

        if (
            post_pause > 0
            and i < len(sentences) - 1
        ):

            silence_path = (
                out_mp3.parent
                / f"_tts_post_{i}.mp3"
            )

            _silence(
                post_pause,
                silence_path
            )

            concat_entries.append(
                silence_path
            )

            temporary_files.append(
                silence_path
            )

            cursor += post_pause

    # ========================================================
    # CONCATENATE
    # ========================================================

    print()
    print("[TTS] Rendering final voiceover...")

    _concat_audio(
        concat_entries,
        out_mp3,
        out_mp3.parent
    )

    # ========================================================
    # CLEAN TEMPORARY FILES
    # ========================================================

    _cleanup_files(
        temporary_files
    )

    concat_file = (
        out_mp3.parent
        / "_voice_concat.txt"
    )

    _cleanup_files(
        [concat_file]
    )

    # ========================================================
    # FINAL INFO
    # ========================================================

    final_duration = _duration(
        out_mp3
    )

    print()
    print("=" * 60)
    print("TTS COMPLETE")
    print("=" * 60)
    print(
        f"Output   : {out_mp3}"
    )
    print(
        f"Duration : {final_duration:.2f}s"
    )
    print(
        f"Words    : {len(all_words)}"
    )
    print("=" * 60)
    print()

    return all_words


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    """
    Run this file directly to test the TTS engine.

    Example:

        python tts.py

    The generated file will be:

        test_horror_voice.mp3
    """

    test_script = """
    I thought the house was empty.

    But then I heard something upstairs.

    Three slow footsteps.

    Then another.

    And that's when I realized...

    they weren't coming from upstairs.

    They were coming from inside my room.
    """

    test_config = {
        "tts": {
            "voice": "en-US-ChristopherNeural",
            "rate": "-2%",
            "pitch": "-2Hz",
            "dynamic": True
        }
    }

    output = Path(
        "test_horror_voice.mp3"
    )

    timings = make_voiceover(
        test_script,
        test_config,
        output
    )

    print("First 10 word timings:")

    for timing in timings[:10]:

        print(
            timing
        )