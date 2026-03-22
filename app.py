import tempfile
from pathlib import Path

import streamlit as st
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)

from utils.audio_tools import analyze_audio
from utils.media_tools import save_uploaded_files, build_media_plan, build_clips_from_plan,
)
from utils.lyrics_tools import parse_manual_lyrics, auto_transcribe_if_available,
)

st.set_page_config(page_title="AI Lyric Video Maker", layout="wide")

OUTPUT_DIR = Path("outputs")
TEMP_DIR = Path("temp")
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

st.title("AI Lyric Video Maker")
st.caption(
    "Version 1 MVP: upload music + photos/videos, then auto-generate a beat-aware montage with lyric overlays."
)


def get_video_size(aspect_ratio: str):
    if aspect_ratio == "9:16":
        return (720, 1280)
    if aspect_ratio == "16:9":
        return (1280, 720)
    return (1080, 1080)


with st.sidebar:
    st.header("Settings")
    target_aspect = st.selectbox("Aspect ratio", ["9:16", "16:9", "1:1"], index=0)
    target_duration = st.slider("Target duration (seconds)", 15, 120, 45, 5)
    image_min = st.slider("Minimum image duration", 1.0, 5.0, 2.0, 0.5)
    image_max = st.slider("Maximum image duration", 1.0, 8.0, 3.5, 0.5)
    use_transcription = st.checkbox(
        "Try automatic transcription (if Whisper is installed)", value=False
    )
    subtitle_on = st.checkbox("Overlay lyrics / captions", value=True)
    randomize_media = st.checkbox("Shuffle media automatically", value=True)

    st.markdown("---")
    st.subheader("Export")
    fps = st.selectbox("FPS", [24, 30], index=1)

left, right = st.columns([1, 1])

with left:
    st.subheader("1) Upload media")
    audio_file = st.file_uploader("Upload audio", type=["mp3", "wav", "m4a"])
    image_files = st.file_uploader(
        "Upload images",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    video_files = st.file_uploader(
        "Upload videos (optional)",
        type=["mp4", "mov", "m4v", "avi"],
        accept_multiple_files=True,
    )

with right:
    st.subheader("2) Lyrics")
    lyrics_mode = st.radio(
        "Lyric source",
        ["Plain lyrics text", "Timed lyrics (one per line as mm:ss | text)"],
        horizontal=True,
    )
    lyric_placeholder = (
        "Example:\nWe were young and free\nUnder the city lights\n..."
        if lyrics_mode == "Plain lyrics text"
        else "Example:\n00:00 | We were young and free\n00:07 | Under the city lights"
    )
    lyrics_text = st.text_area(
        "Paste lyrics (optional)",
        height=220,
        placeholder=lyric_placeholder,
    )

if audio_file is not None:
    st.audio(audio_file)

if st.button("Generate video", type="primary", use_container_width=True):
    if audio_file is None:
        st.error("Please upload an audio file first.")
        st.stop()

    has_images = bool(image_files) and len(image_files) > 0
    has_videos = bool(video_files) and len(video_files) > 0

    if not has_images and not has_videos:
        st.error("Please upload at least one image or video.")
        st.stop()

    with st.spinner("Saving uploads..."):
        work_dir = Path(tempfile.mkdtemp(dir=TEMP_DIR))
        saved = save_uploaded_files(work_dir, audio_file, image_files, video_files)

    with st.spinner("Analyzing audio..."):
        audio_info = analyze_audio(saved["audio_path"], target_duration=target_duration)

    with st.expander("Audio analysis details", expanded=False):
        st.write(
            {
                "duration_sec": round(audio_info["duration"], 2),
                "tempo_bpm": round(audio_info["tempo"], 2),
                "beat_count": len(audio_info["beat_times"]),
                "target_duration_sec": round(audio_info["target_duration"], 2),
            }
        )

    subtitles = []
    if subtitle_on:
        if lyrics_text.strip():
            subtitles = parse_manual_lyrics(
                lyrics_text,
                audio_info["target_duration"],
                timed=(lyrics_mode == "Timed lyrics (one per line as mm:ss | text)"),
            )
        elif use_transcription:
            with st.spinner("Trying automatic transcription..."):
                subtitles = auto_transcribe_if_available(saved["audio_path"])
                if not subtitles:
                    st.warning(
                        "Automatic transcription was not available. The video will be generated without subtitles unless you paste lyrics."
                    )
        else:
            st.info("No lyrics provided. The video will be generated without subtitle overlays.")

    with st.spinner("Planning montage..."):
        plan = build_media_plan(
            image_paths=saved["image_paths"],
            video_paths=saved["video_paths"],
            beat_times=audio_info["beat_times"],
            target_duration=audio_info["target_duration"],
            image_min=image_min,
            image_max=image_max,
            randomize=randomize_media,
        )

    if plan is None or plan.empty:
        st.error("Could not build a media plan. Try uploading more files.")
        st.stop()

    st.subheader("3) Planned sequence")
    st.dataframe(plan, use_container_width=True)

    with st.spinner("Building clips..."):
        out_w, out_h = get_video_size(target_aspect)
        clips = build_clips_from_plan(plan, out_w, out_h)

        if not clips:
            st.error("No valid clips were created from your uploaded media.")
            st.stop()

        final_video = concatenate_videoclips(clips, method="compose")

        audio_clip = AudioFileClip(str(saved["audio_path"]))
        final_duration = min(
            final_video.duration,
            audio_info["target_duration"],
            audio_clip.duration,
        )
        final_video = final_video.subclip(0, final_duration).set_audio(
            audio_clip.subclip(0, final_duration)
        )

        layers = [final_video]

        if subtitles:
            for seg in subtitles:
                start = max(0.0, float(seg["start"]))
                end = min(final_duration, float(seg["end"]))
                if end <= start:
                    continue

                try:
                    txt = (
                        TextClip(
                            seg["text"],
                            fontsize=42 if out_w < 1000 else 54,
                            color="white",
                            method="caption",
                            size=(int(out_w * 0.84), None),
                            align="center",
                            stroke_color="black",
                            stroke_width=2,
                        )
                        .set_start(start)
                        .set_end(end)
                        .set_position(("center", int(out_h * 0.82)))
                    )
                    layers.append(txt)
                except Exception:
                    pass

        composite = CompositeVideoClip(layers, size=(out_w, out_h)).set_duration(
            final_duration
        )
        output_path = OUTPUT_DIR / "ai_lyric_video_output.mp4"

        composite.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(OUTPUT_DIR / "temp-audio.m4a"),
            remove_temp=True,
            threads=2,
            verbose=False,
            logger=None,
        )

    st.success("Video generated.")
    st.video(str(output_path))

    with open(output_path, "rb") as f:
        st.download_button(
            "Download generated video",
            data=f,
            file_name=output_path.name,
            mime="video/mp4",
            use_container_width=True,
        )

    with st.expander("Tips for better results"):
        st.markdown(
            """
- Upload at least 10 to 20 photos for smoother montage variety.
- For cleaner captions, paste your own lyrics instead of relying only on transcription.
- Shorter target duration usually gives a stronger result for reels.
- If rendering is slow on Streamlit Cloud, test first with images only.
            """
        )
