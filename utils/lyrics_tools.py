
import math
import re


def parse_manual_lyrics(text, total_duration, timed=False):
    text = (text or "").strip()
    if not text:
        return []

    if timed:
        segments = []
        pattern = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*\|\s*(.+?)\s*$")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        for i, ln in enumerate(lines):
            m = pattern.match(ln)
            if not m:
                continue
            mm, ss, lyric = m.groups()
            start = int(mm) * 60 + int(ss)
            segments.append({"start": float(start), "text": lyric.strip()})

        for i in range(len(segments)):
            end = segments[i + 1]["start"] if i + 1 < len(segments) else total_duration
            segments[i]["end"] = float(end)
        return segments

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    seg_dur = total_duration / max(1, len(lines))
    segments = []
    for i, line in enumerate(lines):
        start = i * seg_dur
        end = min(total_duration, (i + 1) * seg_dur)
        segments.append({"start": float(start), "end": float(end), "text": line})
    return segments


def auto_transcribe_if_available(audio_path):
    try:
        import whisper
    except Exception:
        return []

    try:
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path))
        segments = []
        for seg in result.get("segments", []):
            txt = str(seg.get("text", "")).strip()
            if txt:
                segments.append(
                    {
                        "start": float(seg.get("start", 0.0)),
                        "end": float(seg.get("end", 0.0)),
                        "text": txt,
                    }
                )
        return segments
    except Exception:
        return []
