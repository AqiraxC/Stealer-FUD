import os
import sys
import ctypes
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import psutil
except ImportError:
    pass

try:
    import win32api
    import win32con
    import win32process
    import win32security
    import win32gui
except ImportError:
    pass

class AntiAnalysis:
    def __init__(self):
        self.analysis_detected = False
        self.analysis_indicators = []
        self.analysis_type = None
        
    def check_analysis_processes(self):
        analysis_processes = [
            "wireshark.exe", "procmon.exe", "processhacker.exe",
            "processexplorer.exe", "tcpview.exe", "autoruns.exe",
            "fiddler.exe", "regmon.exe", "filemon.exe",
            "ollydbg.exe", "x64dbg.exe", "x32dbg.exe",
            "immunitydebugger.exe", "windbg.exe", "ida.exe",
            "ida64.exe", "ghidra.exe", "radare2.exe",
            "cuckoo.exe", "anyrun.exe", "joebox.exe",
            "regshot.exe", "apimonitor.exe", "api_monitor.exe",
            "sysmon.exe", "procmon64.exe", "processhacker64.exe"
        ]
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name']:
                    proc_name = proc.info['name'].lower()
                    
                    if proc_name in analysis_processes:
                        self.analysis_indicators.append(f"Process: {proc.info['name']} (PID: {proc.info['pid']})")
                        self.analysis_type = proc.info['name']
                        return True
        except:
            pass
        
        return False
    
    def check_analysis_windows(self):
        analysis_windows = [
            "wireshark", "procmon", "process hacker", "process explorer",
            "tcpview", "autoruns", "fiddler", "regmon", "filemon",
            "ollydbg", "x64dbg", "x32dbg", "immunity debugger",
            "windbg", "ida", "ghidra", "cuckoo", "any.run"
        ]
        
        try:
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd).lower()
                    
                    for analysis_window in analysis_windows:
                        if analysis_window in window_title:
                            results.append({
                                "hwnd": hwnd,
                                "title": window_title
                            })
                            return True
                return True
            
            results = []
            win32gui.EnumWindows(enum_windows_callback, results)
            
            if results:
                self.analysis_indicators.append(f"Window: {results[0]['title']}")
                return True
        except:
            pass
        
        return False
    
    def check_analysis_services(self):
        analysis_services = [
            "wireshark", "procmon", "processhacker",
            "fiddler", "tcpview"
        ]
        
        try:
            # Check running services
            output = subprocess.check_output("sc query", shell=True, stderr=subprocess.DEVNULL).decode().lower()
            
            for service in analysis_services:
                if service in output:
                    self.analysis_indicators.append(f"Service: {service}")
                    return True
        except:
            pass
        
        return False
    
    def check_analysis_drivers(self):
        analysis_drivers = [
            "wireshark", "npcap", "winpcap",
            "procmon", "processhacker"
        ]
        
        try:
            # Check loaded drivers
            output = subprocess.check_output("driverquery", shell=True, stderr=subprocess.DEVNULL).decode().lower()
            
            for driver in analysis_drivers:
                if driver in output:
                    self.analysis_indicators.append(f"Driver: {driver}")
                    return True
        except:
            pass
        
        return False
    
    def check_analysis_files(self):
        analysis_files = [
            "C:\\Program Files\\Wireshark\\Wireshark.exe",
            "C:\\Program Files (x86)\\Wireshark\\Wireshark.exe",
            "C:\\Program Files\\Process Hacker\\ProcessHacker.exe",
            "C:\\Program Files (x86)\\Process Hacker\\ProcessHacker.exe",
            "C:\\Program Files\\Process Explorer\\procexp.exe",
            "C:\\Program Files (x86)\\Process Explorer\\procexp.exe",
            "C:\\Tools\\Wireshark\\Wireshark.exe",
            "C:\\Tools\\Process Hacker\\ProcessHacker.exe"
        ]
        
        for file_path in analysis_files:
            if os.path.exists(file_path):
                self.analysis_indicators.append(f"File: {file_path}")
                return True
        
        return False
    
    def check_analysis_registry(self):
        analysis_registry_keys = [
            r"SOFTWARE\Wireshark",
            r"SOFTWARE\Process Hacker",
            r"SOFTWARE\Process Explorer",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Wireshark"
        ]
        
        try:
            import winreg
            
            for key_path in analysis_registry_keys:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    winreg.CloseKey(key)
                    self.analysis_indicators.append(f"Registry: {key_path}")
                    return True
                except:
                    pass
        except:
            pass
        
        return False
    
    def check_network_connections(self):
        try:
            # Check for suspicious network connections
            analysis_ports = [
                5555,  # ADB
                8080,  # Common analysis port
                8888,  # Fiddler
                9090,  # Common analysis port
                10000,  # Common analysis port
            ]
            
            connections = psutil.net_connections()
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    if conn.raddr:
                        remote_port = conn.raddr[1]
                        
                        if remote_port in analysis_ports:
                            self.analysis_indicators.append(f"Network: port {remote_port}")
                            return True
        except:
            pass
        
        return False
    
    def check_environment_variables(self):
        analysis_env_vars = [
            "SANDBOX", "ANALYSIS", "MALWARE", "VIRUS",
            "CUCKOO", "ANYRUN", "JOEBOX"
        ]
        
        try:
            for env_var in analysis_env_vars:
                if env_var in os.environ:
                    self.analysis_indicators.append(f"Env: {env_var}")
                    return True
        except:
            pass
        
        return False
    
    def check_username(self):
        suspicious_usernames = [
            "sandbox", "virus", "malware", "test",
            "analysis", "cuckoo", "anyrun", "joebox",
            "admin", "user", "guest"
        ]
        
        try:
            username = os.getenv("USERNAME", "").lower()
            
            for suspicious in suspicious_usernames:
                if suspicious in username:
                    self.analysis_indicators.append(f"Username: {username}")
                    return True
        except:
            pass
        
        return False
    
    def check_hostname(self):
        suspicious_hostnames = [
            "sandbox", "virus", "malware", "test",
            "analysis", "cuckoo", "anyrun", "joebox"
        ]
        
        try:
            hostname = os.getenv("COMPUTERNAME", "").lower()
            
            for suspicious in suspicious_hostnames:
                if suspicious in hostname:
                    self.analysis_indicators.append(f"Hostname: {hostname}")
                    return True
        except:
            pass
        
        return False
    
    def check_uptime(self):
        try:
            import time
            
            # Get system uptime
            uptime = time.time() - psutil.boot_time()
            
            # If system has been running for less than 5 minutes, might be analysis environment
            if uptime < 300:
                self.analysis_indicators.append(f"Short uptime: {uptime} seconds")
                return True
        except:
            pass
        
        return False
    
    def check_mouse_movement(self):
        try:
            import ctypes
            from ctypes import wintypes
            
            # Check mouse position
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            
            point1 = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point1))
            
            import time
            time.sleep(1)
            
            point2 = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point2))
            
            # If mouse hasn't moved, might be automated analysis
            if point1.x == point2.x and point1.y == point2.y:
                self.analysis_indicators.append("No mouse movement detected")
                return True
        except:
            pass
        
        return False
    
    def check_screen_resolution(self):
        try:
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            # Check for common analysis resolutions
            analysis_resolutions = [
                (800, 600),
                (1024, 768),
                (1280, 720)
            ]
            
            for width, height in analysis_resolutions:
                if screen_width == width and screen_height == height:
                    self.analysis_indicators.append(f"Resolution: {screen_width}x{screen_height}")
                    return True
        except:
            pass
        
        return False
    
    def run_all_checks(self):
        checks = [
            self.check_analysis_processes,
            self.check_analysis_windows,
            self.check_analysis_services,
            self.check_analysis_drivers,
            self.check_analysis_files,
            self.check_analysis_registry,
            self.check_network_connections,
            self.check_environment_variables,
            self.check_username,
            self.check_hostname,
            self.check_uptime,
            self.check_mouse_movement,
            self.check_screen_resolution
        ]
        
        analysis_detected = False
        
        for check in checks:
            try:
                if check():
                    analysis_detected = True
                    break
            except:
                continue
        
        self.analysis_detected = analysis_detected
        
        return {
            "analysis_detected": analysis_detected,
            "analysis_type": self.analysis_type,
            "indicators": self.analysis_indicators
        }

if __name__ == "__main__":
    anti_analysis = AntiAnalysis()
    results = anti_analysis.run_all_checks()
    
    if results["analysis_detected"]:
        print(f"Analysis tools detected: {results['analysis_type']}")
        print(f"Indicators: {results['indicators']}")
    else:
        print("No analysis tools detected")