import cv2
from exercise_detection import ExerciseDetector

def main():
    # Initialize the ExerciseDetector
    detector = ExerciseDetector()
    
    # Initialize video capture (0 is the default camera)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot access the camera.")
        return
    
    # Set exercise type
    exercise_type = 'bicep_curl'
    print(f"Starting {exercise_type} detection. Press 'q' to quit.")
    
    # Initialize variables
    current_reps = 0
    stage = 'init'
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
        
        # Get frame dimensions
        height, width, _ = frame.shape
        
        # Process the frame
        processed_frame, results, angle, stage, counter = detector.process_frame(
            frame, exercise_type
        )

        print(stage, angle, counter)

        
        # Update the current reps
        if counter > current_reps:
            current_reps = counter
        
        # Render the UI
        processed_frame = detector.render_ui(
            processed_frame, 
            current_reps, 
            stage, 
            angle, 
            width,
            exercise_type
        )
        
        # Display the resulting frame
        cv2.imshow(f'{exercise_type.capitalize()} Detection', processed_frame)
        
        # Exit the loop on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
