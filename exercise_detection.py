import cv2
import mediapipe as mp
import math
import numpy as np
import time

class ExerciseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # Color definitions
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 200, 0)
        self.RED = (0, 0, 255)
        self.BLUE = (245, 117, 25)

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / math.pi)
        return angle if angle <= 180.0 else 360 - angle

    def process_frame(self, frame, exercise_type, stage, counter):
        """
        Process a single frame for exercise detection
        
        Args:
            frame (numpy.ndarray): Input video frame
            exercise_type (str): Type of exercise to detect
        
        Returns:
            tuple: Processed frame, detected landmarks, exercise metrics
        """

        # Convert frame to RGB for MediaPipe processing
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # Detect pose landmarks
        results = self.pose.process(image)
        
        # Convert back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        angle = 0  # Default angle
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Detect exercise based on type
            if exercise_type == 'bicep_curls':
                angle, stage, counter = self.detect_bicep_curl(landmarks, stage, counter)
            elif exercise_type == 'squat':
                angle, stage, counter = self.detect_squat(landmarks, stage, counter)
            elif exercise_type == 'pushup':
                angle, stage, counter = self.detect_pushup(landmarks, stage, counter)
            
            # Render landmarks and connections
            self.mp_drawing.draw_landmarks(
                image, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
            )
        
        return image, angle, stage, counter
       

    def render_ui(self, image, counter, stage, angle, width, exercise_type):
        """
        Render UI elements on the frame
        
        Args:
            image (numpy.ndarray): Input frame
            counter (int): Rep counter
            stage (str): Current exercise stage
            angle (float): Calculated joint angle
            width (int): Frame width
            exercise_type (str): Type of exercise
        
        Returns:
            numpy.ndarray: Frame with UI elements
        """
        # Exercise-specific angle ranges
        exercise_configs = {
            'pushup': {'max_angle': 178, 'min_angle': 25},
            'squat': {'max_angle': 160, 'min_angle': 90},
            'bicep_curl': {'max_angle': 160, 'min_angle': 30}
        }
        
        config = exercise_configs.get(exercise_type, 
                                      {'max_angle': 178, 'min_angle': 25})
        
        # Title and background
        cv2.rectangle(image, 
                      (int(width/2) - 150, 0), 
                      (int(width/2) + 250, 73), 
                      self.BLUE, -1)
        cv2.putText(image, f'{exercise_type.upper()} Tracker', 
                    (int(width/2) - 100, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, 
                    self.WHITE, 2, cv2.LINE_AA)
        
        # Reps counter
        cv2.rectangle(image, (0, 0), (255, 73), self.BLUE, -1)
        cv2.putText(image, 'REPS', (15, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                    self.WHITE, 1, cv2.LINE_AA)
        cv2.putText(image, str(counter), (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, 
                    self.WHITE, 2, cv2.LINE_AA)
        
        # Stage
        cv2.putText(image, 'STAGE', (95, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                    self.WHITE, 1, cv2.LINE_AA)
        cv2.putText(image, stage, (95, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, 
                    self.WHITE, 2, cv2.LINE_AA)
        
        # Progress bar
        progress = ((angle - config['min_angle']) / 
                    (config['max_angle'] - config['min_angle'])) * 100
        cv2.rectangle(image, 
                      (50, 350), 
                      (50 + int(progress * 2), 370), 
                      self.GREEN, cv2.FILLED)
        cv2.rectangle(image, (50, 350), (250, 370), 
                      self.WHITE, 2)
        cv2.putText(image, f'{int(progress)}%', (50, 400), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, 
                    self.WHITE, 2, cv2.LINE_AA)
        
        return image

    def detect_pushup(self, landmarks, stage, counter):
        """Pushup-specific detection logic"""
        shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        
        angle = self.calculate_angle(shoulder, elbow, wrist)
        
        # Stage logic
        if angle > 160:  # Fully extended position
            if stage == "down":  # Transition from down to up
                stage = "up"
        elif angle < 60:  # Fully bent position
            if stage == "up":  # Transition from up to down
                stage = "down"
                counter += 1  # Increment counter on valid rep
        
        return angle, stage, counter

    def detect_squat(self, landmarks, stage, counter):
        """Squat-specific detection logic"""
        hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        
        angle = self.calculate_angle(hip, knee, ankle)
        
        # Stage logic
        if angle > 155:  # Fully standing
            if stage == "down":  # Transition from down to up
                stage = "up"
                counter += 1  # Increment counter on valid rep
        elif angle < 90:  # Fully squatted
            if stage == "up":  # Transition from up to down
                stage = "down"
        
        return angle, stage, counter

    def detect_bicep_curl(self, landmarks, stage, counter):
        """Bicep Curl-specific detection logic"""
        shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        
        angle = self.calculate_angle(shoulder, elbow, wrist)
        
        # Stage logic
        if angle > 160:  # Fully extended
            if stage == "down" or stage == "init":  # Transition from down to up
                stage = "up"
        elif angle < 40:  # Fully bent
            if stage == "up":  # Transition from up to down
                stage = "down"
                counter += 1  # Increment counter on valid rep
        
        return angle, stage, counter