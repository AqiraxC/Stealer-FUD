import os
import sys
import json
import base64
import hashlib
import hmac
import zlib
import secrets
import string
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    pass

try:
    from Crypto.Cipher import AES
    from Crypto.Cipher import DES3
    from Crypto.Cipher import Blowfish
    from Crypto.Cipher import ARC4
    from Crypto.Cipher import ChaCha20
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Random import get_random_bytes
except ImportError:
    pass

class EncryptionManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.key = None
        self.iv = None
        self.salt = None
        self.algorithm = self.config.get("encryption_algorithm", "AES-256-GCM")
        
    def generate_key(self, key_size=32):
        return secrets.token_bytes(key_size)
    
    def generate_iv(self, iv_size=16):
        return secrets.token_bytes(iv_size)
    
    def generate_salt(self, salt_size=16):
        return secrets.token_bytes(salt_size)
    
    def derive_key_from_password(self, password, salt=None, iterations=100000):
        if salt is None:
            salt = self.generate_salt()
        
        if isinstance(password, str):
            password = password.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password)
        return key, salt
    
    def aes_encrypt_cbc(self, data, key=None, iv=None):
        try:
            if key is None:
                key = self.key or self.generate_key()
            
            if iv is None:
                iv = self.iv or self.generate_iv()
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            # Pad data
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()
            
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            
            return {
                "encrypted": encrypted,
                "key": key,
                "iv": iv
            }
        except:
            return None
    
    def aes_decrypt_cbc(self, encrypted_data, key, iv):
        try:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            return decrypted
        except:
            return None
    
    def aes_encrypt_gcm(self, data, key=None, nonce=None):
        try:
            if key is None:
                key = self.key or self.generate_key()
            
            if nonce is None:
                nonce = secrets.token_bytes(12)
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            
            encrypted = encryptor.update(data) + encryptor.finalize()
            tag = encryptor.tag
            
            return {
                "encrypted": encrypted,
                "tag": tag,
                "key": key,
                "nonce": nonce
            }
        except:
            return None
    
    def aes_decrypt_gcm(self, encrypted_data, key, nonce, tag):
        try:
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            
            decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return decrypted
        except:
            return None
    
    def aes_encrypt_ctr(self, data, key=None, nonce=None):
        try:
            if key is None:
                key = self.key or self.generate_key()
            
            if nonce is None:
                nonce = secrets.token_bytes(16)
            
            if isinstance(data, str):
                data = data.encode()
            
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            
            encrypted = encryptor.update(data) + encryptor.finalize()
            
            return {
                "encrypted": encrypted,
                "key": key,
                "nonce": nonce
            }
        except:
            return None
    
    def aes_decrypt_ctr(self, encrypted_data, key, nonce):
        try:
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            decryptor = cipher.decryptor()
            
            decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return decrypted
        except:
            return None
    
    def xor_encrypt(self, data, key=None):
        try:
            if key is None:
                key = self.key or self.generate_key(16)
            
            if isinstance(data, str):
                data = data.encode()
            
            if isinstance(key, str):
                key = key.encode()
            
            encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
            
            return {
                "encrypted": encrypted,
                "key": key
            }
        except:
            return None
    
    def xor_decrypt(self, encrypted_data, key):
        try:
            if isinstance(key, str):
                key = key.encode()
            
            decrypted = bytes([encrypted_data[i] ^ key[i % len(key)] for i in range(len(encrypted_data))])
            return decrypted
        except:
            return None
    
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
    
    def chacha20_encrypt(self, data, key=None):
        try:
            if key is None:
                key = self.key or self.generate_key(32)
            
            if isinstance(data, str):
                data = data.encode()
            
            nonce = secrets.token_bytes(12)
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
    
    def multi_layer_encrypt(self, data, layers=3):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            keys_info = []
            encrypted_data = data
            
            for i in range(layers):
                # Choose random encryption method
                method = random.choice(['aes_gcm', 'xor', 'rc4', 'chacha20', 'fernet'])
                
                if method == 'aes_gcm':
                    result = self.aes_encrypt_gcm(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys_info.append({
                        "method": "aes_gcm",
                        "key": base64.b64encode(result["key"]).decode(),
                        "nonce": base64.b64encode(result["nonce"]).decode(),
                        "tag": base64.b64encode(result["tag"]).decode()
                    })
                
                elif method == 'xor':
                    result = self.xor_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys_info.append({
                        "method": "xor",
                        "key": base64.b64encode(result["key"]).decode()
                    })
                
                elif method == 'rc4':
                    result = self.rc4_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys_info.append({
                        "method": "rc4",
                        "key": base64.b64encode(result["key"]).decode()
                    })
                
                elif method == 'chacha20':
                    result = self.chacha20_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys_info.append({
                        "method": "chacha20",
                        "key": base64.b64encode(result["key"]).decode(),
                        "nonce": base64.b64encode(result["nonce"]).decode()
                    })
                
                elif method == 'fernet':
                    result = self.fernet_encrypt(encrypted_data)
                    encrypted_data = result["encrypted"]
                    keys_info.append({
                        "method": "fernet",
                        "key": base64.b64encode(result["key"]).decode()
                    })
            
            return {
                "encrypted": base64.b64encode(encrypted_data).decode(),
                "keys": keys_info
            }
        except:
            return None
    
    def multi_layer_decrypt(self, encrypted_data_b64, keys_info):
        try:
            encrypted_data = base64.b64decode(encrypted_data_b64.encode())
            
            for key_info in reversed(keys_info):
                method = key_info["method"]
                
                if method == 'aes_gcm':
                    key = base64.b64decode(key_info["key"])
                    nonce = base64.b64decode(key_info["nonce"])
                    tag = base64.b64decode(key_info["tag"])
                    encrypted_data = self.aes_decrypt_gcm(encrypted_data, key, nonce, tag)
                
                elif method == 'xor':
                    key = base64.b64decode(key_info["key"])
                    encrypted_data = self.xor_decrypt(encrypted_data, key)
                
                elif method == 'rc4':
                    key = base64.b64decode(key_info["key"])
                    encrypted_data = self.rc4_decrypt(encrypted_data, key)
                
                elif method == 'chacha20':
                    key = base64.b64decode(key_info["key"])
                    nonce = base64.b64decode(key_info["nonce"])
                    encrypted_data = self.chacha20_decrypt(encrypted_data, key, nonce)
                
                elif method == 'fernet':
                    key = base64.b64decode(key_info["key"])
                    encrypted_data = self.fernet_decrypt(encrypted_data, key)
                
                if encrypted_data is None:
                    return None
            
            return encrypted_data
        except:
            return None
    
    def encode_data(self, data, encoding='base64'):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            if encoding == 'base64':
                return base64.b64encode(data).decode()
            elif encoding == 'base64_url':
                return base64.urlsafe_b64encode(data).decode()
            elif encoding == 'hex':
                return data.hex()
            elif encoding == 'zlib_base64':
                return base64.b64encode(zlib.compress(data)).decode()
            else:
                return base64.b64encode(data).decode()
        except:
            return None
    
    def decode_data(self, data, encoding='base64'):
        try:
            if encoding == 'base64':
                return base64.b64decode(data.encode())
            elif encoding == 'base64_url':
                return base64.urlsafe_b64decode(data.encode())
            elif encoding == 'hex':
                return bytes.fromhex(data)
            elif encoding == 'zlib_base64':
                return zlib.decompress(base64.b64decode(data.encode()))
            else:
                return base64.b64decode(data.encode())
        except:
            return None
    
    def hash_data(self, data, algorithm='sha256'):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            if algorithm == 'sha256':
                return hashlib.sha256(data).hexdigest()
            elif algorithm == 'sha512':
                return hashlib.sha512(data).hexdigest()
            elif algorithm == 'md5':
                return hashlib.md5(data).hexdigest()
            elif algorithm == 'sha1':
                return hashlib.sha1(data).hexdigest()
            else:
                return hashlib.sha256(data).hexdigest()
        except:
            return None
    
    def generate_hmac(self, data, key=None, algorithm='sha256'):
        try:
            if key is None:
                key = self.key or self.generate_key()
            
            if isinstance(data, str):
                data = data.encode()
            
            if isinstance(key, str):
                key = key.encode()
            
            if algorithm == 'sha256':
                return hmac.new(key, data, hashlib.sha256).hexdigest()
            elif algorithm == 'sha512':
                return hmac.new(key, data, hashlib.sha512).hexdigest()
            elif algorithm == 'md5':
                return hmac.new(key, data, hashlib.md5).hexdigest()
            else:
                return hmac.new(key, data, hashlib.sha256).hexdigest()
        except:
            return None
    
    def encrypt_file(self, file_path, output_path=None, method='aes_gcm'):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            
            if method == 'aes_gcm':
                result = self.aes_encrypt_gcm(data)
            elif method == 'xor':
                result = self.xor_encrypt(data)
            elif method == 'rc4':
                result = self.rc4_encrypt(data)
            elif method == 'chacha20':
                result = self.chacha20_encrypt(data)
            else:
                result = self.aes_encrypt_gcm(data)
            
            if result is None:
                return None
            
            if output_path is None:
                output_path = file_path + ".encrypted"
            
            encrypted_b64 = base64.b64encode(result["encrypted"]).decode()
            key_b64 = base64.b64encode(result.get("key", b"")).decode()
            
            metadata = {
                "method": method,
                "encrypted_data": encrypted_b64,
                "key": key_b64
            }
            
            if "nonce" in result:
                metadata["nonce"] = base64.b64encode(result["nonce"]).decode()
            
            if "tag" in result:
                metadata["tag"] = base64.b64encode(result["tag"]).decode()
            
            with open(output_path, "w") as f:
                json.dump(metadata, f)
            
            return output_path
        except:
            return None
    
    def decrypt_file(self, file_path, output_path=None):
        try:
            with open(file_path, "r") as f:
                metadata = json.load(f)
            
            method = metadata.get("method", "aes_gcm")
            encrypted_data = base64.b64decode(metadata["encrypted_data"])
            key = base64.b64decode(metadata["key"])
            
            if method == 'aes_gcm':
                nonce = base64.b64decode(metadata["nonce"])
                tag = base64.b64decode(metadata["tag"])
                decrypted = self.aes_decrypt_gcm(encrypted_data, key, nonce, tag)
            elif method == 'xor':
                decrypted = self.xor_decrypt(encrypted_data, key)
            elif method == 'rc4':
                decrypted = self.rc4_decrypt(encrypted_data, key)
            elif method == 'chacha20':
                nonce = base64.b64decode(metadata["nonce"])
                decrypted = self.chacha20_decrypt(encrypted_data, key, nonce)
            else:
                return None
            
            if output_path is None:
                output_path = file_path.replace(".encrypted", "")
            
            with open(output_path, "wb") as f:
                f.write(decrypted)
            
            return output_path
        except:
            return None

if __name__ == "__main__":
    manager = EncryptionManager()
    
    test_data = "This is sensitive data that needs to be encrypted"
    
    # Multi-layer encryption
    result = manager.multi_layer_encrypt(test_data, layers=3)
    print(f"Encrypted: {result['encrypted'][:50]}...")
    
    # Decrypt
    decrypted = manager.multi_layer_decrypt(result['encrypted'], result['keys'])
    print(f"Decrypted: {decrypted.decode()}")