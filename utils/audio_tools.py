
from pathlib import Path

import librosa
import numpy as np


def analyze_audio(audio_path, target_duration=45):
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))

    # Beat tracking
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr).tolist()

    # Energy envelope
    rms = librosa.feature.rms(y=y)[0]
    energy_times = librosa.times_like(rms, sr=sr).tolist()
    energy_values = rms.tolist()

    final_target = min(float(target_duration), duration)

    return {
        "duration": duration,
        "tempo": float(tempo if np.isscalar(tempo) else tempo[0]),
        "beat_times": [float(t) for t in beat_times if t <= final_target],
        "energy_times": [float(t) for t in energy_times],
        "energy_values": [float(v) for v in energy_values],
        "target_duration": final_target,
        "sample_rate": int(sr),
    }
