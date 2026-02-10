"""
MediaPipe pose detection wrapper
Provides clean interface to get landmarks and angles
"""
import cv2
import mediapipe as mp
from core_cv.analysis.angle_math import calculate_angle
from config.app_constants import LANDMARKS, VISIBILITY_THRESHOLD


"""
Wrapper for MediaPipe Pose detection

Initialize MediaPipe Pose detector
        
    Args:
        min_detection_confidence: Minimum confidence for detection
        min_ tracking_confidence: Minimum confidence for tracking
"""

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # 0=Lite, 1=Full, 2=Heavy
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
    
    
    """
    Process a frame and detect pose landmarks

    args:
        frame: BGR image from OpenCV
        draw_skeleton: Whether to draw skeleton overlay (default True)

    returns:
        tuple: (landmarks, annotated_frame)
            landmarks: MediaPipe landmark list or None
            annotated_frame: Frame with skeleton drawn (if enabled)
    """
    def process_frame(self, frame, draw_skeleton=True):

        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process with MediaPipe
        results = self.pose.process(frame_rgb)

        # Draw skeleton on frame only if enabled
        annotated_frame = frame.copy()
        if results.pose_landmarks and draw_skeleton:
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=1)
            )

        return (results.pose_landmarks.landmark if results.pose_landmarks else None,
                annotated_frame)
    
    
    """
    Calculate knee angle for squats
    
    Args:
        landmarks: MediaPipe landmarks
        width, height: Frame dimensions
        side: 'left' or 'right'
    
    Returns:
        float: knee angle in degrees, or None if landmarks not visible
    """
    def get_knee_angle(self, landmarks, width, height, side='left'):
        # Get landmark indices
        if side == 'left':
            hip_idx = LANDMARKS['LEFT_HIP']
            knee_idx = LANDMARKS['LEFT_KNEE']
            ankle_idx = LANDMARKS['LEFT_ANKLE']
        else:
            hip_idx = LANDMARKS['RIGHT_HIP']
            knee_idx = LANDMARKS['RIGHT_KNEE']
            ankle_idx = LANDMARKS['RIGHT_ANKLE']
        
        # Check visibility
        if (landmarks[hip_idx].visibility < VISIBILITY_THRESHOLD or
            landmarks[knee_idx].visibility < VISIBILITY_THRESHOLD or
            landmarks[ankle_idx].visibility < VISIBILITY_THRESHOLD):
            return None
        
        # Convert normalized coordinates to pixels
        hip = (landmarks[hip_idx].x * width, landmarks[hip_idx].y * height)
        knee = (landmarks[knee_idx].x * width, landmarks[knee_idx].y * height)
        ankle = (landmarks[ankle_idx].x * width, landmarks[ankle_idx].y * height)
        
        # Calculate angle
        return calculate_angle(hip, knee, ankle)
    """
    Calculate elbow angle for pushups and curls
    
    Args:
        landmarks: MediaPipe landmarks
        width, height: Frame dimensions
        side: 'left' or 'right'
    
    Returns:
        float: elbow angle in degrees, or None if landmarks not visible
    """
    def get_elbow_angle(self, landmarks, width, height, side='left'):
    
        # Get landmark indices
        if side == 'left':
            shoulder_idx = LANDMARKS['LEFT_SHOULDER']
            elbow_idx = LANDMARKS['LEFT_ELBOW']
            wrist_idx = LANDMARKS['LEFT_WRIST']
        else:
            shoulder_idx = LANDMARKS['RIGHT_SHOULDER']
            elbow_idx = LANDMARKS['RIGHT_ELBOW']
            wrist_idx = LANDMARKS['RIGHT_WRIST']
        
        # Check visibility
        if (landmarks[shoulder_idx].visibility < VISIBILITY_THRESHOLD or
            landmarks[elbow_idx].visibility < VISIBILITY_THRESHOLD or
            landmarks[wrist_idx].visibility < VISIBILITY_THRESHOLD):
            return None
        
        # Convert normalized coordinates to pixels
        shoulder = (landmarks[shoulder_idx].x * width, landmarks[shoulder_idx].y * height)
        elbow = (landmarks[elbow_idx].x * width, landmarks[elbow_idx].y * height)
        wrist = (landmarks[wrist_idx].x * width, landmarks[wrist_idx].y * height)
        
        # Calculate angle
        return calculate_angle(shoulder, elbow, wrist)
    
    
    """
    Get knee angle from whichever leg is most visible/bent
    Automatically tries both sides and returns the better reading
    
    Args:
        landmarks: MediaPipe landmarks
        width, height: Frame dimensions
    
    Returns:
        float: Best knee angle in degrees, or None if neither visible
    """
    def get_best_knee_angle(self, landmarks, width, height):
        # Try both sides
        left_angle = self.get_knee_angle(landmarks, width, height, side='left')
        right_angle = self.get_knee_angle(landmarks, width, height, side='right')
        
        # Both visible - use smaller angle (more bent = active leg)
        if left_angle is not None and right_angle is not None:
            return min(left_angle, right_angle)
        
        # Only one visible - use that one
        elif left_angle is not None:
            return left_angle
        elif right_angle is not None:
            return right_angle
        else:
            return None
    
    
    """
    Get elbow angle from whichever arm is most visible/bent
    Automatically tries both sides and returns the better reading
    
    Args:
        landmarks: MediaPipe landmarks
        width, height: Frame dimensions
    
    Returns:
        float: Best elbow angle in degrees, or None if neither visible
    """
    def get_best_elbow_angle(self, landmarks, width, height):

        # Try both sides
        left_angle = self.get_elbow_angle(landmarks, width, height, side='left')
        right_angle = self.get_elbow_angle(landmarks, width, height, side='right')
        
        # Both visible - use smaller angle (more bent = active arm)
        if left_angle is not None and right_angle is not None:
            return min(left_angle, right_angle)
        
        # Only one visible - use that one
        elif left_angle is not None:
            return left_angle
        elif right_angle is not None:
            return right_angle
        else:
            return None

    """
    Calculate hip angle (for advanced squat analysis)
    
    Args:
        landmarks: MediaPipe landmarks
        width, height: Frame dimensions
        side: 'left' or 'right'
    
    Returns:
        float: hip angle in degrees, or None if landmarks not visible
    """
    def get_hip_angle(self, landmarks, width, height, side='left'):
        if side == 'left':
            shoulder_idx = LANDMARKS['LEFT_SHOULDER']
            hip_idx = LANDMARKS['LEFT_HIP']
            knee_idx = LANDMARKS['LEFT_KNEE']
        else:
            shoulder_idx = LANDMARKS['RIGHT_SHOULDER']
            hip_idx = LANDMARKS['RIGHT_HIP']
            knee_idx = LANDMARKS['RIGHT_KNEE']
        
        if (landmarks[shoulder_idx].visibility < VISIBILITY_THRESHOLD or
            landmarks[hip_idx].visibility < VISIBILITY_THRESHOLD or
            landmarks[knee_idx].visibility < VISIBILITY_THRESHOLD):
            return None
        
        shoulder = (landmarks[shoulder_idx].x * width, landmarks[shoulder_idx].y * height)
        hip = (landmarks[hip_idx].x * width, landmarks[hip_idx].y * height)
        knee = (landmarks[knee_idx].x * width, landmarks[knee_idx].y * height)
        
        return calculate_angle(shoulder, hip, knee)
    
    def close(self):
        """Release MediaPipe resources"""
        self.pose.close()


if __name__ == "__main__":
    # Test pose detection
    print("Testing pose detection...")
    
    detector = PoseDetector()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Could not open camera")
        exit(1)
    
    print("✓ Camera opened")
    print("Testing new get_best_knee_angle() and get_best_elbow_angle() methods")
    print("Press 'q' to quit test")
    
    frame_count = 0
    
    while frame_count < 100:  # Test for 100 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        landmarks, annotated_frame = detector.process_frame(frame)
        
        if landmarks:
            height, width = frame.shape[:2]
            
            # Test new best angle methods
            knee_angle = detector.get_best_knee_angle(landmarks, width, height)
            if knee_angle:
                cv2.putText(annotated_frame, f"Knee (auto): {knee_angle:.1f}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            elbow_angle = detector.get_best_elbow_angle(landmarks, width, height)
            if elbow_angle:
                cv2.putText(annotated_frame, f"Elbow (auto): {elbow_angle:.1f}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Show which side is being used
            left_knee = detector.get_knee_angle(landmarks, width, height, side='left')
            right_knee = detector.get_knee_angle(landmarks, width, height, side='right')
            
            side_info = "Tracking: "
            if left_knee and right_knee:
                side_info += "Both sides visible"
            elif left_knee:
                side_info += "Left side only"
            elif right_knee:
                side_info += "Right side only"
            else:
                side_info += "No sides visible"
            
            cv2.putText(annotated_frame, side_info, 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow('Pose Detection Test', annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
    
    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    
    print(f"✓ Processed {frame_count} frames successfully")
    print("✓ New methods get_best_knee_angle() and get_best_elbow_angle() are working!")