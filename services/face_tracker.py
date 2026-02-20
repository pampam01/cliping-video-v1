import cv2
import mediapipe as mp
import numpy as np


class FaceTracker:
    """
    Tracks faces in a video and crops the frame to keep the speaker centered.
    """
    def __init__(self):
        """
        Initializes the FaceTracker with a MediaPipe face detection model.
        """
        self.mp_face_detection = mp.solutions.face_detection
        # Use model_selection=0 (short-range) for better performance
        # Increase min_detection_confidence to reduce false positives
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.4
        )
        # Cache for detected faces to avoid reprocessing
        self.face_cache = {}
        print("🎯 Initialized intelligent face tracking with MediaPipe (optimized)")

    def detect_faces_in_frame(self, frame, frame_time=None):
        """
        Detects faces in a single frame of a video.

        Args:
            frame (numpy.ndarray): The video frame to process.
            frame_time (float, optional): The timestamp of the frame.
                                           Defaults to None.

        Returns:
            list: A list of dictionaries, each representing a detected face.
        """
        # Use cache if available
        if frame_time is not None and frame_time in self.face_cache:
            return self.face_cache[frame_time]
            
        try:
            # Resize frame for faster processing (half size)
            h, w, _ = frame.shape
            scale = 0.5
            small_frame = cv2.resize(frame, (int(w*scale), int(h*scale)))
            
            # Convert to RGB (required by MediaPipe)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)

            faces = []
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * w)  # Scale back to original size
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)

                    center_x = x + width // 2
                    center_y = y + height // 2
                    confidence = detection.score[0]

                    faces.append({
                        'center_x': center_x,
                        'center_y': center_y,
                        'width': width,
                        'height': height,
                        'confidence': confidence,
                        'area': width * height
                    })

            result = sorted(faces, key=lambda f: f['confidence'] * f['area'], reverse=True)
            
            # Cache the result
            if frame_time is not None:
                self.face_cache[frame_time] = result
                
            return result
        except Exception as e:
            print(f"    ⚠️ Face detection error: {e}")
            return []

    def smooth_trajectory(self, positions, window_size=5):
        """
        Smoothes a trajectory of positions using a moving average.

        Args:
            positions (list): A list of (x, y) tuples representing positions.
            window_size (int, optional): The size of the moving average window.
                                         Defaults to 5.

        Returns:
            list: A list of smoothed (x, y) tuples.
        """
        if len(positions) <= window_size:
            return positions

        smoothed = []
        for i in range(len(positions)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(positions), i + window_size // 2 + 1)
            window = positions[start_idx:end_idx]

            avg_x = sum(pos[0] for pos in window) / len(window)
            avg_y = sum(pos[1] for pos in window) / len(window)
            smoothed.append((avg_x, avg_y))

        return smoothed

    def track_and_crop(self, clip):
        """
        Dynamically tracks faces. If a face is found, crops to 9:16 centered on face.
        If no face is found, shows the full video frame (letterboxed/scaled to fit width).

        Args:
            clip (moviepy.editor.VideoFileClip): The video clip to process.

        Returns:
            moviepy.editor.VideoFileClip: The processed video clip.
        """
        w_video, h_video = clip.size
        
        # Target dimensions (9:16)
        # We want the output to have the height of the original video (or scaled up?)
        # Let's keep original height as reference, so output width is h_video * 9/16
        w_target = int(h_video * 9 / 16)
        if w_target % 2 != 0: w_target -= 1
        
        print(f"    🎯 Analyzing video for dynamic face tracking (Target: {w_target}x{h_video})...")

        # 1. Analyze frames at 2 FPS to build a "face map"
        # We need a dense map to switch modes responsively
        fps_analyze = 2
        duration = clip.duration
        timestamps = np.arange(0, duration, 1.0 / fps_analyze)
        
        face_map = [] # [(time, center_x), ...] or None if no face
        
        print(f"    ⏳ Scanning {len(timestamps)} frames...")
        
        for i, t in enumerate(timestamps):
            try:
                frame = clip.get_frame(t)
                faces = self.detect_faces_in_frame(frame, frame_time=t)
                
                if faces:
                    # Found a face
                    best_face = faces[0]
                    face_map.append({'time': t, 'center_x': best_face['center_x'], 'has_face': True})
                else:
                    # No face
                    face_map.append({'time': t, 'center_x': w_video // 2, 'has_face': False})
                    
            except Exception as e:
                print(f"    ⚠️ Error scanning frame at {t:.2f}s: {e}")
                face_map.append({'time': t, 'center_x': w_video // 2, 'has_face': False})

        # 2. Gap Filling / Stabilization
        # If we have Face -> No Face -> Face within a short window (e.g., 1.0s), 
        # assume the face was there but missed.
        
        gap_fill_window = 1.0  # seconds
        print(f"    🛠️ Stabilizing tracking (Filling gaps < {gap_fill_window}s)...")
        
        for i in range(len(face_map)):
            if not face_map[i]['has_face']:
                # Look back: was there a face recently?
                prev_face_idx = -1
                for j in range(i - 1, -1, -1):
                    if face_map[j]['has_face']:
                        prev_face_idx = j
                        break
                    if (face_map[i]['time'] - face_map[j]['time']) > gap_fill_window:
                        break
                
                # Look forward: will there be a face soon?
                next_face_idx = -1
                for j in range(i + 1, len(face_map)):
                    if face_map[j]['has_face']:
                        next_face_idx = j
                        break
                    if (face_map[j]['time'] - face_map[i]['time']) > gap_fill_window:
                        break
                
                # If surrounded by faces within window, fill the gap
                if prev_face_idx != -1 and next_face_idx != -1:
                    # Interpolate center_x
                    t1 = face_map[prev_face_idx]['time']
                    x1 = face_map[prev_face_idx]['center_x']
                    t2 = face_map[next_face_idx]['time']
                    x2 = face_map[next_face_idx]['center_x']
                    t_curr = face_map[i]['time']
                    
                    # Linear interpolation
                    ratio = (t_curr - t1) / (t2 - t1)
                    interp_x = int(x1 + ratio * (x2 - x1))
                    
                    face_map[i]['has_face'] = True
                    face_map[i]['center_x'] = interp_x
                    # print(f"    🔧 Filled gap at {t_curr:.2f}s")
        
        # 3. Smooth the face positions and state
        # We want to avoid jittery switching. 
        # For simplicity, we'll just look up the closest analyzed frame during rendering.
        
        print("    ✅ Analysis complete. Generating dynamic crop...")

        def get_face_state(t):
            # Find closest timestamp in face_map
            # Since timestamps are sorted, we can use binary search or just simple index calc
            idx = int(t * fps_analyze)
            if idx >= len(face_map): idx = len(face_map) - 1
            if idx < 0: idx = 0
            return face_map[idx]

        def process_frame(get_frame, t):
            frame = get_frame(t) # Original frame (H, W, 3)
            img_h, img_w, _ = frame.shape
            
            state = get_face_state(t)
            
            if state['has_face']:
                # === FACE MODE: Crop 9:16 Centered on Face ===
                center_x = state['center_x']
                
                # Ensure crop is within bounds
                left = center_x - (w_target // 2)
                if left < 0: left = 0
                if left + w_target > img_w: left = img_w - w_target
                
                # Crop
                # Note: numpy cropping is y:y+h, x:x+w
                crop = frame[:, left:left+w_target]
                return crop
            
            else:
                # === NO FACE MODE: Show Full Width (Zoom Out) ===
                # We want to show the full width of the video, fitting into the 9:16 target.
                # Since source is usually 16:9 (Landscape) and target is 9:16 (Portrait),
                # "Fitting" the width means shrinking the video to fit inside w_target.
                # But that leaves huge black bars top/bottom.
                
                # Logic:
                # 1. Resize original frame so its width == w_target
                # 2. This makes height = img_h * (w_target / img_w)
                # 3. Paste this resized image into a black canvas of size (w_target, img_h)
                
                scale = w_target / img_w
                new_h = int(img_h * scale)
                
                # Resize using OpenCV (faster than PIL for per-frame)
                # Ensure frame is uint8 for cv2
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                resized = cv2.resize(frame, (w_target, new_h))
                
                # Create black canvas
                canvas = np.zeros((img_h, w_target, 3), dtype=np.uint8)
                
                # Center vertically
                y_offset = (img_h - new_h) // 2
                
                canvas[y_offset:y_offset+new_h, :] = resized
                return canvas

        return clip.fl(process_frame)

    def close(self):
        """Releases resources used by the face detector."""
        try:
            # Clear cache to free memory
            self.face_cache = {}
            # Close the face detection model
            self.face_detection.close()
            print("🎯 Face tracking resources released")
        except Exception as e:
            print(f"⚠️ Error closing face tracker: {e}")
