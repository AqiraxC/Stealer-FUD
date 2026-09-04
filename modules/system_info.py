import os
import sys
import json
import time
import platform
import socket
import uuid
import ctypes
import hashlib
import subprocess
import psutil
import wmi
import winreg
from datetime import datetime
from typing import Dict, Any, List, Optional

class SystemInfo:
    def __init__(self):
        self.wmi_connection = None
        try:
            self.wmi_connection = wmi.WMI()
        except:
            pass
    
    def get_os_info(self):
        info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": "x64" if sys.maxsize > 2**32 else "x86"
        }
        
        try:
            if self.wmi_connection:
                for os_info in self.wmi_connection.Win32_OperatingSystem():
                    info["caption"] = os_info.Caption
                    info["version_number"] = os_info.Version
                    info["build_number"] = os_info.BuildNumber
                    info["serial_number"] = os_info.SerialNumber
                    info["install_date"] = os_info.InstallDate
                    info["last_boot_time"] = os_info.LastBootUpTime
                    info["os_architecture"] = os_info.OSArchitecture
                    info["total_visible_memory"] = os_info.TotalVisibleMemorySize
                    info["total_virtual_memory"] = os_info.TotalVirtualMemorySize
                    info["free_physical_memory"] = os_info.FreePhysicalMemory
                    info["free_virtual_memory"] = os_info.FreeVirtualMemory
                    break
        except:
            pass
        
        return info
    
    def get_cpu_info(self):
        info = {}
        try:
            if self.wmi_connection:
                for cpu in self.wmi_connection.Win32_Processor():
                    info["name"] = cpu.Name
                    info["manufacturer"] = cpu.Manufacturer
                    info["processor_id"] = cpu.ProcessorId
                    info["cores"] = cpu.NumberOfCores
                    info["logical_processors"] = cpu.NumberOfLogicalProcessors
                    info["max_clock_speed"] = cpu.MaxClockSpeed
                    info["current_clock_speed"] = cpu.CurrentClockSpeed
                    info["socket"] = cpu.SocketDesignation
                    info["status"] = cpu.Status
                    break
        except:
            pass
        
        # Additional CPU info from psutil
        try:
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
            info["cpu_freq_current"] = psutil.cpu_freq().current if psutil.cpu_freq() else None
            info["cpu_freq_max"] = psutil.cpu_freq().max if psutil.cpu_freq() else None
            info["cpu_stats"] = dict(psutil.cpu_stats()._asdict())
            info["cpu_times"] = dict(psutil.cpu_times()._asdict())
        except:
            pass
        
        return info
    
    def get_gpu_info(self):
        info = []
        try:
            if self.wmi_connection:
                for gpu in self.wmi_connection.Win32_VideoController():
                    gpu_info = {
                        "name": gpu.Name,
                        "manufacturer": gpu.Manufacturer,
                        "driver_version": gpu.DriverVersion,
                        "video_memory": gpu.AdapterRAM,
                        "resolution": f"{gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution}" if gpu.CurrentHorizontalResolution else None,
                        "refresh_rate": gpu.CurrentRefreshRate,
                        "status": gpu.Status
                    }
                    info.append(gpu_info)
        except:
            pass
        return info
    
    def get_disk_info(self):
        info = []
        try:
            if self.wmi_connection:
                for disk in self.wmi_connection.Win32_DiskDrive():
                    disk_info = {
                        "model": disk.Model,
                        "serial_number": disk.SerialNumber,
                        "size": disk.Size,
                        "interface_type": disk.InterfaceType,
                        "partitions": disk.Partitions,
                        "status": disk.Status
                    }
                    info.append(disk_info)
        except:
            pass
        
        # Logical drives
        try:
            for partition in psutil.disk_partitions():
                usage = psutil.disk_usage(partition.mountpoint)
                info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent_used": usage.percent
                })
        except:
            pass
        
        return info
    
    def get_network_info(self):
        info = {}
        try:
            # IP Address
            hostname = socket.gethostname()
            info["hostname"] = hostname
            info["ip_address"] = socket.gethostbyname(hostname)
            info["mac_address"] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
            
            # Network adapters
            adapters = []
            if self.wmi_connection:
                for adapter in self.wmi_connection.Win32_NetworkAdapterConfiguration():
                    if adapter.IPEnabled:
                        adapter_info = {
                            "description": adapter.Description,
                            "mac_address": adapter.MACAddress,
                            "ip_addresses": adapter.IPAddress,
                            "subnet_masks": adapter.IPSubnet,
                            "default_gateway": adapter.DefaultIPGateway,
                            "dns_servers": adapter.DNSServerSearchOrder,
                            "dhcp_enabled": adapter.DHCPEnabled
                        }
                        adapters.append(adapter_info)
            info["adapters"] = adapters
            
            # Network stats
            net_io = psutil.net_io_counters()
            info["bytes_sent"] = net_io.bytes_sent
            info["bytes_received"] = net_io.bytes_recv
            info["packets_sent"] = net_io.packets_sent
            info["packets_received"] = net_io.packets_recv
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def get_memory_info(self):
        info = {}
        try:
            vm = psutil.virtual_memory()
            info["total"] = vm.total
            info["available"] = vm.available
            info["used"] = vm.used
            info["free"] = vm.free
            info["percent"] = vm.percent
            
            swap = psutil.swap_memory()
            info["swap_total"] = swap.total
            info["swap_used"] = swap.used
            info["swap_free"] = swap.free
            info["swap_percent"] = swap.percent
        except:
            pass
        return info
    
    def get_process_list(self):
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time']):
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "username": proc.info['username'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "memory_percent": proc.info['memory_percent'],
                    "create_time": datetime.fromtimestamp(proc.info['create_time']).isoformat() if proc.info['create_time'] else None
                })
        except:
            pass
        return processes
    
    def get_installed_software(self):
        software = []
        try:
            if self.wmi_connection:
                for product in self.wmi_connection.Win32_Product():
                    software.append({
                        "name": product.Name,
                        "vendor": product.Vendor,
                        "version": product.Version,
                        "install_date": product.InstallDate,
                        "location": product.InstallLocation
                    })
        except:
            pass
        return software
    
    def get_hwid(self):
        try:
            cpu_id = ""
            disk_serial = ""
            mac_address = uuid.getnode()
            
            if self.wmi_connection:
                for cpu in self.wmi_connection.Win32_Processor():
                    cpu_id = cpu.ProcessorId.strip()
                    break
                
                for disk in self.wmi_connection.Win32_DiskDrive():
                    disk_serial = disk.SerialNumber.strip()
                    break
            
            combined = f"{cpu_id}{disk_serial}{mac_address}"
            return hashlib.sha256(combined.encode()).hexdigest()
        except:
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()
    
    def get_bios_info(self):
        info = {}
        try:
            if self.wmi_connection:
                for bios in self.wmi_connection.Win32_BIOS():
                    info["manufacturer"] = bios.Manufacturer
                    info["serial_number"] = bios.SerialNumber
                    info["version"] = bios.Version
                    info["release_date"] = bios.ReleaseDate
                    info["description"] = bios.Description
                    break
        except:
            pass
        return info
    
    def get_motherboard_info(self):
        info = {}
        try:
            if self.wmi_connection:
                for board in self.wmi_connection.Win32_BaseBoard():
                    info["manufacturer"] = board.Manufacturer
                    info["product"] = board.Product
                    info["serial_number"] = board.SerialNumber
                    info["version"] = board.Version
                    break
        except:
            pass
        return info
    
    def get_antivirus_info(self):
        av_list = []
        av_processes = [
            "avast", "avg", "avira", "bitdefender", "kaspersky", "mcafee",
            "norton", "symantec", "windows defender", "msmpeng", "malwarebytes",
            "eset", "trend micro", "comodo", "panda", "sophos", "webroot",
            "gdata", "f-secure", "zonealarm", "clamav"
        ]
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name']:
                    proc_name = proc.info['name'].lower()
                    for av in av_processes:
                        if av in proc_name:
                            av_list.append(proc.info['name'])
                            break
        except:
            pass
        
        # Check for Windows Defender
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender")
            winreg.CloseKey(key)
            av_list.append("Windows Defender")
        except:
            pass
        
        return list(set(av_list))
    
    def get_user_accounts(self):
        accounts = []
        try:
            if self.wmi_connection:
                for account in self.wmi_connection.Win32_UserAccount():
                    accounts.append({
                        "name": account.Name,
                        "full_name": account.FullName,
                        "sid": account.SID,
                        "disabled": account.Disabled,
                        "lockout": account.Lockout,
                        "password_required": account.PasswordRequired
                    })
        except:
            pass
        return accounts
    
    def get_startup_programs(self):
        startup_programs = []
        try:
            # Registry Run keys
            registry_paths = [
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        name, value, _ = winreg.EnumValue(key, i)
                        startup_programs.append({
                            "source": f"HKCU\\{reg_path}",
                            "name": name,
                            "path": value
                        })
                    winreg.CloseKey(key)
                except:
                    pass
                
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        name, value, _ = winreg.EnumValue(key, i)
                        startup_programs.append({
                            "source": f"HKLM\\{reg_path}",
                            "name": name,
                            "path": value
                        })
                    winreg.CloseKey(key)
                except:
                    pass
            
            # Startup folder
            startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            if os.path.exists(startup_folder):
                for file in os.listdir(startup_folder):
                    startup_programs.append({
                        "source": "Startup Folder",
                        "name": file,
                        "path": os.path.join(startup_folder, file)
                    })
        except:
            pass
        
        return startup_programs
    
    def get_all_info(self):
        info = {
            "timestamp": datetime.now().isoformat(),
            "hwid": self.get_hwid(),
            "os": self.get_os_info(),
            "cpu": self.get_cpu_info(),
            "gpu": self.get_gpu_info(),
            "disks": self.get_disk_info(),
            "memory": self.get_memory_info(),
            "network": self.get_network_info(),
            "bios": self.get_bios_info(),
            "motherboard": self.get_motherboard_info(),
            "antivirus": self.get_antivirus_info(),
            "user_accounts": self.get_user_accounts(),
            "startup_programs": self.get_startup_programs(),
            "processes": self.get_process_list()[:50],  # Limit to first 50 processes
            "installed_software": self.get_installed_software()[:20],  # Limit to first 20
            "username": os.getenv("USERNAME"),
            "hostname": os.getenv("COMPUTERNAME"),
            "is_admin": self.check_admin()
        }
        return info
    
    def check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def get_public_ip(self):
        try:
            import requests
            response = requests.get("https://api.ipify.org", timeout=5)
            return response.text
        except:
            try:
                response = requests.get("http://ifconfig.me/ip", timeout=5)
                return response.text.strip()
            except:
                try:
                    response = requests.get("http://icanhazip.com", timeout=5)
                    return response.text.strip()
                except:
                    return "Unknown"
    
    def get_geolocation(self):
        try:
            import requests
            ip = self.get_public_ip()
            if ip != "Unknown":
                response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return {}
    
    def to_json(self):
        return json.dumps(self.get_all_info(), indent=2, default=str)

if __name__ == "__main__":
    sys_info = SystemInfo()
    info = sys_info.get_all_info()
    print(json.dumps(info, indent=2, default=str))