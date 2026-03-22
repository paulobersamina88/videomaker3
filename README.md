# AI Lyric Video Maker - Streamlit MVP

This is a simple Version 1 Streamlit app that:
- uploads an audio file
- uploads photos and optional video clips
- detects beat / tempo from music
- auto-arranges media into a montage
- overlays pasted lyrics or optional Whisper transcription
- exports an MP4 video

## Features
- Beat-aware sequencing
- Image + optional video support
- Plain lyrics mode
- Timed lyrics mode (`mm:ss | lyric line`)
- Optional automatic transcription using Whisper
- Reel-friendly aspect ratios: 9:16, 16:9, 1:1

## Folder Structure
- `app.py` - Streamlit app
- `utils/audio_tools.py` - audio analysis
- `utils/media_tools.py` - media saving, planning, clip creation
- `utils/lyrics_tools.py` - lyric parsing and optional transcription

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Recommended Workflow
1. Upload one song.
2. Upload 10 to 20 photos for better variety.
3. Add a few short video clips if you want.
4. Paste lyrics manually for the cleanest caption output.
5. Click **Generate video**.

## Notes
- This is an MVP, not a CapCut replacement.
- Whisper transcription is optional and may be heavy in some deployments.
- On Streamlit Cloud, rendering large videos may be slow. Start with a short target duration.
- If text overlay fails because of missing fonts on your machine/server, the app will still generate the video without subtitles.

## Timed Lyrics Format
```text
00:00 | We were young and free
00:06 | Dancing under city lights
00:12 | Holding on to memories
```

## Good next upgrades
- lyric-to-scene matching
- emotion-based media scoring
- smarter chorus detection
- auto zoom / Ken Burns effect
- per-word karaoke highlighting
