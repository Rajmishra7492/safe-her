from datetime import datetime
import os
import wave

import cv2
import numpy as np

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def analyze_risk(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return {
            "risk_score": 0,
            "faces_detected": 0,
            "avg_brightness": 0,
            "is_night": False,
            "triggered": False,
            "notes": "Invalid image",
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    faces_detected = len(faces)

    avg_brightness = float(np.mean(gray))
    hour = datetime.now().hour
    is_night = hour >= 20 or hour <= 5

    risk_score = 0
    notes = []

    if avg_brightness < 80:
        risk_score += 40
        notes.append("Low brightness detected")
    elif avg_brightness < 120:
        risk_score += 20
        notes.append("Moderate lighting")

    if faces_detected >= 1:
        risk_score += min(35, faces_detected * 10)
        notes.append(f"{faces_detected} face(s) detected")

    if is_night:
        risk_score += 25
        notes.append("Night-time risk adjustment applied")

    risk_score = min(100, risk_score)
    triggered = risk_score >= 60

    return {
        "risk_score": risk_score,
        "faces_detected": faces_detected,
        "avg_brightness": round(avg_brightness, 2),
        "is_night": is_night,
        "triggered": triggered,
        "notes": ", ".join(notes) if notes else "No major risk detected",
    }


def analyze_audio(audio_path):
    """Basic loudness estimation for uploaded audio."""
    if not audio_path or not os.path.exists(audio_path):
        return {"avg_amplitude": 0, "loud_audio": False, "notes": "No audio uploaded"}

    ext = os.path.splitext(audio_path)[1].lower()

    if ext == ".wav":
        try:
            with wave.open(audio_path, "rb") as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                sample_width = wav_file.getsampwidth()
                if sample_width == 2:
                    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
                    avg_amplitude = float(np.mean(np.abs(samples))) if len(samples) else 0.0
                else:
                    avg_amplitude = 0.0
        except Exception:
            avg_amplitude = 0.0
    else:
        # Browser recordings are usually webm/ogg; use file size heuristic.
        file_size = os.path.getsize(audio_path)
        avg_amplitude = float(min(30000, file_size / 30))

    loud_audio = avg_amplitude >= 1200
    return {
        "avg_amplitude": round(avg_amplitude, 2),
        "loud_audio": loud_audio,
        "notes": "Loud audio detected" if loud_audio else "Audio level normal",
    }


def combine_multimodal_risk(image_analysis, audio_analysis, is_night=None):
    """Combine image, audio, and time into risk score + risk level."""
    if is_night is None:
        hour = datetime.now().hour
        is_night = hour >= 20 or hour <= 5

    risk_score = 0
    reasons = []

    brightness = image_analysis.get("avg_brightness", 255)
    faces = image_analysis.get("faces_detected", 0)
    loud_audio = audio_analysis.get("loud_audio", False)

    if brightness < 80:
        risk_score += 35
        reasons.append("low_light")
    elif brightness < 120:
        risk_score += 15

    if faces >= 2:
        risk_score += 30
        reasons.append("multiple_faces")
    elif faces == 1:
        risk_score += 12

    if loud_audio:
        risk_score += 25
        reasons.append("loud_audio")

    if is_night:
        risk_score += 15
        reasons.append("night_time")

    risk_score = int(min(100, risk_score))
    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "is_night": is_night,
        "reasons": reasons,
        "triggered": risk_score >= 60,
    }
