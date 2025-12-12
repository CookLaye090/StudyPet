"""
Emotion Detection Demo
This script demonstrates the emotion detection functionality using
emotion_detection_model.keras.

It is modeled after drowsiness_demo.py but loads the emotion model and
runs a simple webcam loop that overlays the predicted emotion label.
"""

import os
import sys
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def _load_emotion_model():
    """Load the emotion detection model from common locations.

    Returns:
        keras.Model or None: Loaded model instance, or None if not found.
    """
    # Primary expected location
    model_path = os.path.join(project_root, "models", "emotion_detection_model.keras")

    # Fallback: directly in project root
    if not os.path.exists(model_path):
        alt_path = os.path.join(project_root, "emotion_detection_model.keras")
        if os.path.exists(alt_path):
            model_path = alt_path

    if not os.path.exists(model_path):
        print("Error: Could not find emotion_detection_model.keras")
        print("Checked paths:")
        print(" -", os.path.join(project_root, "models", "emotion_detection_model.keras"))
        print(" -", os.path.join(project_root, "emotion_detection_model.keras"))
        return None

    print(f"Loading emotion model from: {model_path}")
    try:
        model = load_model(model_path)
    except Exception as e:
        print(f"Error loading emotion model: {e}")
        return None

    return model


def _prepare_face(frame, face_rect):
    """Crop and preprocess face ROI for emotion model.

    Args:
        frame: BGR image frame from OpenCV.
        face_rect: (x, y, w, h) rectangle.

    Returns:
        np.ndarray or None: Preprocessed batch for model, or None if invalid.
    """
    x, y, w, h = face_rect
    face = frame[y : y + h, x : x + w]
    if face.size == 0:
        return None

    # Convert to grayscale or keep RGB based on model expectation.
    # Here we convert to grayscale and resize to 48x48, which is a
    # common setting for simple emotion CNNs. Adjust if your model
    # expects a different shape.
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (48, 48))
    gray = gray.astype("float32") / 255.0
    gray = np.expand_dims(gray, axis=-1)  # (48, 48, 1)
    gray = np.expand_dims(gray, axis=0)   # (1, 48, 48, 1)
    return gray


# A simple list of labels for this 3-class emotion model.
# You can adjust the names or order once you've confirmed them.
EMOTION_LABELS = [
    "Positive",
    "Negative",
    "Neutral",
]


def main():
    """Run the emotion detection demo using the webcam."""
    print("Starting Emotion Detection Demo...")
    print("Press 'q' to quit the demo.")

    model = _load_emotion_model()
    if model is None:
        return 1

    # Simple OpenCV face detector (Haar cascade) for demo purposes
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("Error: Could not load Haar cascade for face detection.")
        return 1

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return 1

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame from camera.")
                break

            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_full, scaleFactor=1.3, minNeighbors=5)

            display_frame = frame.copy()

            for (x, y, w, h) in faces:
                batch = _prepare_face(frame, (x, y, w, h))
                if batch is None:
                    continue

                try:
                    preds = model.predict(batch, verbose=0)[0]
                    emotion_idx = int(np.argmax(preds))
                    confidence = float(preds[emotion_idx])
                except Exception as e:
                    print(f"Prediction error: {e}")
                    continue

                label = EMOTION_LABELS[emotion_idx] if 0 <= emotion_idx < len(EMOTION_LABELS) else str(emotion_idx)
                text = f"{label} ({confidence*100:.1f}%)"

                # Draw bounding box and label
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    display_frame,
                    text,
                    (x, y - 10 if y - 10 > 10 else y + h + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            if len(faces) == 0:
                cv2.putText(
                    display_frame,
                    "No face detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )

            cv2.imshow("Emotion Detection", display_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or cv2.getWindowProperty("Emotion Detection", cv2.WND_PROP_VISIBLE) < 1:
                break

    except KeyboardInterrupt:
        print("\nDemo stopped by user.")
    except Exception as e:
        print(f"An error occurred in the emotion demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if cap is not None and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Emotion demo finished.")

    return 0


if __name__ == "__main__":
    main()
