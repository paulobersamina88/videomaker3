
import math
import mimetypes
import os
import random
from pathlib import Path

import pandas as pd
from PIL import Image, ImageOps
from moviepy.editor import ImageClip, VideoFileClip


def save_uploaded_files(work_dir, audio_file, image_files, video_files):
    work_dir = Path(work_dir)
    audio_path = work_dir / audio_file.name
    audio_path.write_bytes(audio_file.read())

    image_paths = []
    for f in image_files or []:
        p = work_dir / f.name
        p.write_bytes(f.read())
        image_paths.append(p)

    video_paths = []
    for f in video_files or []:
        p = work_dir / f.name
        p.write_bytes(f.read())
        video_paths.append(p)

    return {
        "audio_path": audio_path,
        "image_paths": image_paths,
        "video_paths": video_paths,
    }


def build_media_plan(image_paths, video_paths, beat_times, target_duration, image_min, image_max, randomize=True):
    media = [{"type": "image", "path": str(p)} for p in image_paths] + [{"type": "video", "path": str(p)} for p in video_paths]
    if not media:
        return []

    if randomize:
        random.shuffle(media)

    rows = []
    current = 0.0
    media_index = 0
    beat_index = 0

    while current < target_duration - 0.15:
        item = media[media_index % len(media)]

        if item["type"] == "image":
            # Prefer durations that loosely follow beat intervals
            next_cut = None
            while beat_index < len(beat_times) and beat_times[beat_index] <= current + 0.05:
                beat_index += 1
            if beat_index + 1 < len(beat_times):
                next_cut = beat_times[min(beat_index + 1, len(beat_times) - 1)]
            duration = (next_cut - current) if next_cut else image_min
            duration = max(image_min, min(image_max, duration))
        else:
            duration = min(4.0, target_duration - current)

        if current + duration > target_duration:
            duration = target_duration - current

        rows.append(
            {
                "start": round(current, 2),
                "end": round(current + duration, 2),
                "duration": round(duration, 2),
                "media_type": item["type"],
                "path": item["path"],
            }
        )
        current += duration
        media_index += 1

    return pd.DataFrame(rows)


def _fit_image_to_canvas(image_path, out_w, out_h):
    img = Image.open(image_path).convert("RGB")
    fitted = ImageOps.fit(img, (out_w, out_h), method=Image.Resampling.LANCZOS)
    return fitted


def build_clips_from_plan(plan_df, out_w, out_h):
    clips = []
    for row in plan_df.to_dict(orient="records"):
        path = row["path"]
        duration = float(row["duration"])
        if duration <= 0:
            continue

        try:
            if row["media_type"] == "image":
                fitted = _fit_image_to_canvas(path, out_w, out_h)
                clip = ImageClip(fitted).set_duration(duration)
            else:
                clip = VideoFileClip(path)
                if clip.duration > duration:
                    clip = clip.subclip(0, duration)
                else:
                    clip = clip.loop(duration=duration)
                clip = clip.resize(newsize=(out_w, out_h))
                clip = clip.set_duration(duration)
            clips.append(clip)
        except Exception:
            continue
    return clips
