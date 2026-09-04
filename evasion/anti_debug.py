import os
import sys
import ctypes
import struct
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
except ImportError:
    pass

class AntiDebug:
    def __init__(self):
        self.debugger_detected = False
        self.debug_indicators = []
        self.debugger_type = None
        
    def check_is_debugger_present(self):
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent():
                self.debug_indicators.append("IsDebuggerPresent: True")
                self.debugger_type = "Basic Debugger"
                return True
        except:
            pass
        
        return False
    
    def check_remote_debugger(self):
        try:
            remote_debugger = ctypes.c_bool(False)
            process_handle = ctypes.windll.kernel32.GetCurrentProcess()
            
            result = ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                process_handle,
                ctypes.byref(remote_debugger)
            )
            
            if result and remote_debugger.value:
                self.debug_indicators.append("CheckRemoteDebuggerPresent: True")
                self.debugger_type = "Remote Debugger"
                return True
        except:
            pass
        
        return False
    
    def check_nt_global_flag(self):
        try:
            # Check NtGlobalFlag in PEB
            # PEB is at fs:[0x30] on x86 and gs:[0x60] on x64
            if platform.architecture()[0] == '64bit':
                peb_offset = 0x60
            else:
                peb_offset = 0x30
            
            # Read PEB
            process_basic_info = ctypes.c_ulong()
            
            # NtQueryInformationProcess with ProcessBasicInformation (0)
            result = ctypes.windll.ntdll.NtQueryInformationProcess(
                ctypes.windll.kernel32.GetCurrentProcess(),
                0,
                ctypes.byref(process_basic_info),
                ctypes.sizeof(process_basic_info),
                None
            )
            
            if result == 0:
                # PEB address is in process_basic_info
                # NtGlobalFlag is at offset 0x68 on x64 and 0x68 on x86
                nt_global_flag_offset = 0x68
                
                # Read NtGlobalFlag
                nt_global_flag = ctypes.c_ulong.from_address(
                    process_basic_info.value + nt_global_flag_offset
                ).value
                
                # Check for debug flags
                debug_flags = [
                    0x20,  # FLG_HEAP_ENABLE_TAIL_CHECK
                    0x40,  # FLG_HEAP_ENABLE_FREE_CHECK
                    0x80,  # FLG_HEAP_VALIDATE_PARAMETERS
                    0x40000000  # FLG_HEAP_VALIDATE_ALL
                ]
                
                flags_set = []
                for flag in debug_flags:
                    if nt_global_flag & flag:
                        flags_set.append(hex(flag))
                
                if len(flags_set) >= 2:
                    self.debug_indicators.append(f"NtGlobalFlag: {flags_set}")
                    self.debugger_type = "PEB Debug Flags"
                    return True
        except:
            pass
        
        return False
    
    def check_heap_flags(self):
        try:
            # Check heap flags in PEB
            # These are set when debugging
            process_heap = ctypes.windll.kernel32.GetProcessHeap()
            
            if process_heap:
                # Heap flags are at offset 0x40 for x64
                heap_flags_offset = 0x40
                
                heap_flags = ctypes.c_ulong.from_address(
                    process_heap + heap_flags_offset
                ).value
                
                # Check for debug flags
                if heap_flags & 0x00000002:  # HEAP_GROWABLE
                    self.debug_indicators.append("HeapFlags: HEAP_GROWABLE")
                    return True
                
                if heap_flags & 0x00001000:  # HEAP_TAIL_CHECKING_ENABLED
                    self.debug_indicators.append("HeapFlags: HEAP_TAIL_CHECKING_ENABLED")
                    return True
        except:
            pass
        
        return False
    
    def check_timing(self):
        try:
            import time
            
            # Check for timing anomalies
            start_time = time.time()
            
            # Perform some operations
            for i in range(1000000):
                pass
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # If execution is too slow, might be debugged
            if execution_time > 0.5:
                self.debug_indicators.append(f"Timing anomaly: {execution_time}")
                return True
        except:
            pass
        
        return False
    
    def check_int3(self):
        try:
            # Check for INT 3 breakpoints
            # This is a common debugging technique
            kernel32 = ctypes.windll.kernel32
            
            # Get address of IsDebuggerPresent
            is_debugger_present_addr = ctypes.cast(
                kernel32.IsDebuggerPresent,
                ctypes.c_void_p
            ).value
            
            # Check for INT 3 (0xCC) at function start
            first_byte = ctypes.c_ubyte.from_address(is_debugger_present_addr).value
            
            if first_byte == 0xCC:
                self.debug_indicators.append("INT3 breakpoint detected")
                return True
        except:
            pass
        
        return False
    
    def check_hardware_breakpoints(self):
        try:
            # Check for hardware breakpoints
            # DR0-DR3 registers
            # This requires access to debug registers
            context = None
            
            # Use GetThreadContext to check debug registers
            # This is complex and may not work in Python
            pass
        except:
            pass
        
        return False
    
    def check_debugger_processes(self):
        debugger_processes = [
            "ollydbg.exe", "x64dbg.exe", "x32dbg.exe",
            "immunitydebugger.exe", "windbg.exe", "ida.exe",
            "ida64.exe", "ghidra.exe", "radare2.exe",
            "peid.exe", "die.exe", "detectiteasy.exe"
        ]
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name']:
                    proc_name = proc.info['name'].lower()
                    
                    if proc_name in debugger_processes:
                        self.debug_indicators.append(f"Debugger process: {proc.info['name']}")
                        self.debugger_type = proc.info['name']
                        return True
        except:
            pass
        
        return False
    
    def check_debugger_windows(self):
        debugger_windows = [
            "ollydbg", "x64dbg", "x32dbg", "immunity debugger",
            "windbg", "ida", "ghidra"
        ]
        
        try:
            import win32gui
            
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd).lower()
                    
                    for debugger in debugger_windows:
                        if debugger in window_title:
                            results.append(window_title)
                            return True
                return True
            
            results = []
            win32gui.EnumWindows(enum_windows_callback, results)
            
            if results:
                self.debug_indicators.append(f"Debugger window: {results}")
                return True
        except:
            pass
        
        return False
    
    def check_parent_process(self):
        try:
            current_pid = os.getpid()
            
            # Get parent process
            parent_pid = None
            
            try:
                import psutil
                process = psutil.Process(current_pid)
                parent = process.parent()
                
                if parent:
                    parent_pid = parent.pid
                    parent_name = parent.name().lower()
                    
                    debugger_names = [
                        "ollydbg", "x64dbg", "x32dbg", "windbg",
                        "ida", "ghidra", "radare2"
                    ]
                    
                    if any(name in parent_name for name in debugger_names):
                        self.debug_indicators.append(f"Parent process: {parent_name}")
                        return True
            except:
                pass
        except:
            pass
        
        return False
    
    def check_seh(self):
        try:
            # Check for Structured Exception Handling
            # Debuggers often modify SEH
            pass
        except:
            pass
        
        return False
    
    def check_output_debug_string(self):
        try:
            # Check if OutputDebugString is being intercepted
            # Call OutputDebugString with a test string
            test_string = "debug_test_" + str(datetime.now().timestamp())
            
            # If a debugger is attached, it will intercept this
            ctypes.windll.kernel32.OutputDebugStringW(test_string)
            
            # Check for error
            error = ctypes.windll.kernel32.GetLastError()
            
            if error != 0:
                self.debug_indicators.append(f"OutputDebugString error: {error}")
                return True
        except:
            pass
        
        return False
    
    def run_all_checks(self):
        checks = [
            self.check_is_debugger_present,
            self.check_remote_debugger,
            self.check_nt_global_flag,
            self.check_heap_flags,
            self.check_timing,
            self.check_int3,
            self.check_debugger_processes,
            self.check_debugger_windows,
            self.check_parent_process,
            self.check_output_debug_string
        ]
        
        debugger_detected = False
        
        for check in checks:
            try:
                if check():
                    debugger_detected = True
                    break
            except:
                continue
        
        self.debugger_detected = debugger_detected
        
        return {
            "debugger_detected": debugger_detected,
            "debugger_type": self.debugger_type,
            "indicators": self.debug_indicators
        }

if __name__ == "__main__":
    anti_debug = AntiDebug()
    results = anti_debug.run_all_checks()
    
    if results["debugger_detected"]:
        print(f"Debugger detected: {results['debugger_type']}")
        print(f"Indicators: {results['indicators']}")
    else:
        print("No debugger detected")