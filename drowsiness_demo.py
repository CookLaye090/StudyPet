"""
Drowsiness Detection Demo
This script demonstrates the drowsiness detection functionality.
"""
import os
import sys
import cv2

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Now import the module using the full path
from src.utils.drowsiness_detector import DrowsinessDetector

def process_frame(frame, detector):
    """Process a single frame for drowsiness detection.
    
    Args:
        frame: The input frame (numpy array)
        detector: The DrowsinessDetector instance
        
    Returns:
        tuple: (processed_frame, drowsy, confidence)
    """
    # Create a copy of the frame for display
    display_frame = frame.copy()
    
    # Detect faces in the frame
    faces = detector.detect_face(frame)
    drowsy = False
    confidence = 0.0
    
    if len(faces) > 0:
        # For simplicity, use the first face found
        x, y, w, h = faces[0]
        face_roi = frame[y:y+h, x:x+w]
        
        # Get drowsiness prediction
        is_drowsy, drowsy_confidence, awake_confidence = detector.predict_drowsiness(face_roi)
        drowsy = is_drowsy
        confidence = drowsy_confidence if drowsy else awake_confidence
        
        # Draw detection results
        detector.draw_detection(display_frame, (x, y, w, h), drowsy, drowsy_confidence, awake_confidence)
    else:
        # No face detected
        cv2.putText(display_frame, "No face detected", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Add FPS display (will be updated in the main loop)
    cv2.putText(display_frame, f'FPS: 0.0', 
               (display_frame.shape[1] - 120, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Add red border if drowsy
    if drowsy:
        cv2.rectangle(display_frame, (0, 0), 
                     (display_frame.shape[1]-1, display_frame.shape[0]-1),
                     (0, 0, 255), 3)
    
    return display_frame, drowsy, confidence

def main():
    """Run the drowsiness detection demo with a simplified display loop."""
    import time
    
    print("Starting Drowsiness Detection Demo...")
    print("Press 'q' to quit the demo.")
    
    # Get the absolute path to the model
    model_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'models', 'drowsiness_model.keras'
    ))
    print(f"Looking for model at: {model_path}")
    
    # Alternative path if running from src/demos
    if not os.path.exists(model_path):
        model_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'models', 'drowsiness_model.keras'
        ))
    
    if not os.path.exists(model_path):
        print(f"Error: Could not find drowsiness_model.keras")
        print("Please make sure the model file exists in one of these locations:")
        print(f"1. {os.path.join(os.path.dirname(__file__), 'models', 'drowsiness_model.keras')}")
        print(f"2. {os.path.join(os.path.dirname(__file__), '..', 'models', 'drowsiness_model.keras')}")
        return 1
    
    try:
        # Initialize detector
        print("Initializing drowsiness detector...")
        detector = DrowsinessDetector(model_path)
        
        # Initialize camera
        print("Initializing camera...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return 1
        
        # Set desired frame size (adjust based on your camera's capabilities)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # FPS calculation variables
        frame_count = 0
        fps = 0
        last_time = time.time()
        
        print("Drowsiness detection started. Press 'q' to quit.")
        
        while True:
            # Read frame from camera
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame from camera.")
                break
            
            # Process frame
            display_frame, drowsy, confidence = process_frame(frame, detector)
            
            # Calculate FPS
            frame_count += 1
            current_time = time.time()
            time_diff = current_time - last_time
            
            if time_diff >= 1.0:  # Update FPS every second
                fps = frame_count / time_diff
                frame_count = 0
                last_time = current_time
            
            # Update FPS on the frame
            cv2.putText(display_frame, f'FPS: {fps:.1f}', 
                       (display_frame.shape[1] - 120, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Display the frame
            cv2.imshow('Drowsiness Detection', display_frame)
            
            # Check for 'q' key to quit or window close button
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty('Drowsiness Detection', cv2.WND_PROP_VISIBLE) < 1:
                break
                
    except KeyboardInterrupt:
        print("\nDemo stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Demo finished.")
    
    return 0

if __name__ == "__main__":
    main()
