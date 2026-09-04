import os
import sys
import ctypes
import subprocess
import platform
import socket
import uuid
import struct
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import psutil
except ImportError:
    pass

try:
    import wmi
except ImportError:
    pass

try:
    import win32api
    import win32con
    import win32process
except ImportError:
    pass

class AntiVM:
    def __init__(self):
        self.wmi_connection = None
        self.vm_indicators = []
        self.vm_type = None
        
        try:
            self.wmi_connection = wmi.WMI()
        except:
            pass
    
    def check_mac_address(self):
        try:
            mac = uuid.getnode()
            mac_str = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
            
            vm_mac_prefixes = {
                "00:0c:29": "VMware",
                "00:1c:14": "VMware",
                "00:50:56": "VMware",
                "00:05:69": "VMware",
                "08:00:27": "VirtualBox",
                "00:16:3e": "Xen",
                "00:15:5d": "Hyper-V",
                "00:03:ff": "VirtualPC",
                "00:0f:4b": "Virtual Iron",
                "00:1c:42": "Parallels",
                "00:1a:4a": "QEMU"
            }
            
            for prefix, vm_name in vm_mac_prefixes.items():
                if mac_str.startswith(prefix):
                    self.vm_indicators.append(f"MAC: {mac_str} -> {vm_name}")
                    self.vm_type = vm_name
                    return True
        except:
            pass
        
        return False
    
    def check_wmi_devices(self):
        try:
            if not self.wmi_connection:
                return False
            
            # Check disk drives
            for disk in self.wmi_connection.Win32_DiskDrive():
                model = str(disk.Model).lower()
                manufacturer = str(disk.Manufacturer).lower()
                
                vm_models = [
                    "vbox", "vmware", "qemu", "virtual", "xen",
                    "hyper-v", "parallels"
                ]
                
                for vm_model in vm_models:
                    if vm_model in model or vm_model in manufacturer:
                        self.vm_indicators.append(f"Disk: {disk.Model}")
                        self.vm_type = vm_model
                        return True
            
            # Check computer system
            for computer in self.wmi_connection.Win32_ComputerSystem():
                manufacturer = str(computer.Manufacturer).lower()
                model = str(computer.Model).lower()
                
                vm_manufacturers = [
                    "vmware", "virtualbox", "qemu", "xen",
                    "microsoft corporation", "parallels"
                ]
                
                for vm_manufacturer in vm_manufacturers:
                    if vm_manufacturer in manufacturer or vm_manufacturer in model:
                        self.vm_indicators.append(f"System: {computer.Manufacturer} {computer.Model}")
                        self.vm_type = vm_manufacturer
                        return True
            
            # Check BIOS
            for bios in self.wmi_connection.Win32_BIOS():
                manufacturer = str(bios.Manufacturer).lower()
                version = str(bios.Version).lower()
                serial = str(bios.SerialNumber).lower()
                
                vm_bios = [
                    "vmware", "virtualbox", "qemu", "xen",
                    "parallels", "hyper-v"
                ]
                
                for vm_bios_indicator in vm_bios:
                    if vm_bios_indicator in manufacturer or vm_bios_indicator in version or vm_bios_indicator in serial:
                        self.vm_indicators.append(f"BIOS: {bios.Manufacturer} {bios.Version}")
                        self.vm_type = vm_bios_indicator
                        return True
        except:
            pass
        
        return False
    
    def check_processes(self):
        vm_processes = [
            "vmtoolsd.exe", "vmwaretray.exe", "vmwareuser.exe",
            "vmware.exe", "vmware-vmx.exe", "vboxservice.exe",
            "vboxtray.exe", "vboxclient.exe", "xenservice.exe",
            "qemu-ga.exe", "qemu-system-x86_64.exe", "prl_tools.exe",
            "prl_cc.exe", "parallels.exe"
        ]
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name']:
                    proc_name = proc.info['name'].lower()
                    
                    if proc_name in vm_processes:
                        self.vm_indicators.append(f"Process: {proc.info['name']}")
                        return True
        except:
            pass
        
        return False
    
    def check_files(self):
        vm_files = [
            "C:\\Windows\\System32\\drivers\\vmmouse.sys",
            "C:\\Windows\\System32\\drivers\\vmhgfs.sys",
            "C:\\Windows\\System32\\drivers\\vmci.sys",
            "C:\\Windows\\System32\\drivers\\vboxguest.sys",
            "C:\\Windows\\System32\\drivers\\vboxsf.sys",
            "C:\\Windows\\System32\\drivers\\vboxvideo.sys",
            "C:\\Windows\\System32\\drivers\\xen.sys",
            "C:\\Windows\\System32\\drivers\\prl_tools.sys",
            "C:\\Windows\\System32\\drivers\\hyperv_vmbus.sys"
        ]
        
        for vm_file in vm_files:
            if os.path.exists(vm_file):
                self.vm_indicators.append(f"File: {vm_file}")
                return True
        
        return False
    
    def check_registry(self):
        vm_registry_keys = [
            r"SOFTWARE\VMware, Inc.\VMware Tools",
            r"SOFTWARE\Oracle\VirtualBox Guest Additions",
            r"SOFTWARE\Parallels\Parallels Tools",
            r"SOFTWARE\Microsoft\Virtual Machine\Guest"
        ]
        
        try:
            import winreg
            
            for key_path in vm_registry_keys:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    winreg.CloseKey(key)
                    self.vm_indicators.append(f"Registry: {key_path}")
                    return True
                except:
                    pass
        except:
            pass
        
        return False
    
    def check_cpuid(self):
        try:
            # Check CPUID hypervisor bit
            cpuid_result = ctypes.c_uint32(0)
            
            # CPUID instruction with EAX=1
            # ECX bit 31 indicates hypervisor
            try:
                import numpy as np
                # Use numpy for CPUID
            except:
                pass
            
            # Try using inline assembly via ctypes
            # This is platform-specific and may not work in Python
            # Alternative: Check for hypervisor via WMI
            if self.wmi_connection:
                for cpu in self.wmi_connection.Win32_Processor():
                    if "hypervisor" in str(cpu.Description).lower():
                        self.vm_indicators.append(f"CPU: {cpu.Description}")
                        return True
        except:
            pass
        
        return False
    
    def check_devices(self):
        try:
            if not self.wmi_connection:
                return False
            
            # Check for VM devices
            vm_devices = [
                "vmware", "virtualbox", "qemu", "xen",
                "hyper-v", "parallels"
            ]
            
            for device in self.wmi_connection.Win32_PnPEntity():
                name = str(device.Name).lower()
                
                for vm_device in vm_devices:
                    if vm_device in name:
                        self.vm_indicators.append(f"Device: {device.Name}")
                        return True
        except:
            pass
        
        return False
    
    def check_system_info(self):
        try:
            system_info = subprocess.check_output("systeminfo", shell=True, stderr=subprocess.DEVNULL).decode().lower()
            
            vm_keywords = [
                "vmware", "virtualbox", "qemu", "xen",
                "hyper-v", "parallels"
            ]
            
            for keyword in vm_keywords:
                if keyword in system_info:
                    self.vm_indicators.append(f"SystemInfo: {keyword}")
                    return True
        except:
            pass
        
        return False
    
    def check_network_adapters(self):
        try:
            if not self.wmi_connection:
                return False
            
            for adapter in self.wmi_connection.Win32_NetworkAdapter():
                if adapter.MACAddress:
                    mac = adapter.MACAddress.lower()
                    
                    vm_mac_prefixes = [
                        "00:0c:29", "00:1c:14", "00:50:56", "00:05:69",  # VMware
                        "08:00:27",  # VirtualBox
                        "00:16:3e",  # Xen
                        "00:15:5d",  # Hyper-V
                        "00:03:ff",  # VirtualPC
                        "00:0f:4b",  # Virtual Iron
                        "00:1c:42"   # Parallels
                    ]
                    
                    for prefix in vm_mac_prefixes:
                        if mac.startswith(prefix):
                            self.vm_indicators.append(f"Network: {adapter.MACAddress}")
                            return True
        except:
            pass
        
        return False
    
    def run_all_checks(self):
        checks = [
            self.check_mac_address,
            self.check_wmi_devices,
            self.check_processes,
            self.check_files,
            self.check_registry,
            self.check_cpuid,
            self.check_devices,
            self.check_system_info,
            self.check_network_adapters
        ]
        
        vm_detected = False
        
        for check in checks:
            try:
                if check():
                    vm_detected = True
                    break
            except:
                continue
        
        return {
            "vm_detected": vm_detected,
            "vm_type": self.vm_type,
            "indicators": self.vm_indicators
        }

if __name__ == "__main__":
    anti_vm = AntiVM()
    results = anti_vm.run_all_checks()
    
    if results["vm_detected"]:
        print(f"VM detected: {results['vm_type']}")
        print(f"Indicators: {results['indicators']}")
    else:
        print("No VM detected")