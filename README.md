# Advanced Python Infostealer Framework

# Made By: Aqirax (https://discord.gg/48SudwBTGD) :3

## Overview
Advanced information gathering and exfiltration framework designed for security research and educational purposes.

## Project Structure
infostealer/
│
├── main.py # Entry point, orchestrates all modules
├── config.json # Configuration file for all settings
├── requirements.txt # Python dependencies
├── README.md # Documentation
│
├── core/
│ ├── init.py # Core utilities and helper functions
│ ├── builder.py # Builds executable with PyInstaller
│ ├── obfuscator.py # Code obfuscation and string encryption
│ ├── crypter.py # Multi-layer encryption system
│ └── persistence.py # System persistence mechanisms
│
├── modules/
│ ├── init.py # Module initialization and utilities
│ ├── system_info.py # System information collection
│ ├── browser_stealer.py # Browser data extraction
│ │ ├── chrome.py # Chrome-specific stealer
│ │ ├── firefox.py # Firefox-specific stealer
│ │ ├── edge.py # Edge-specific stealer
│ │ └── brave.py # Brave-specific stealer
│ ├── cookies.py # Cookie extraction and decryption
│ ├── passwords.py # Password extraction and decryption
│ ├── wallets.py # Cryptocurrency wallet stealer
│ ├── discord_token.py # Discord token grabber
│ ├── telegram.py # Telegram session stealer
│ ├── file_grabber.py # File search and extraction
│ ├── keylogger.py # Keyboard input capture
│ ├── screenshot.py # Screen capture
│ ├── clipboard.py # Clipboard monitoring
│ └── camera.py # Webcam capture
│
├── evasion/
│ ├── init.py # Evasion manager
│ ├── anti_vm.py # Virtual machine detection
│ ├── anti_debug.py # Debugger detection
│ ├── anti_analysis.py # Analysis tool detection
│ ├── sleep_obfuscation.py # Sleep timing obfuscation
│ └── process_hollowing.py # Process injection
│
├── network/
│ ├── init.py # Network utilities
│ ├── exfil.py # Data exfiltration
│ ├── encryption.py # Data encryption
│ └── retry.py # Retry logic with backoff
│
├── output/
│ ├── logs/ # Keylogger logs
│ ├── screenshots/ # Captured screenshots
│ ├── stolen/ # Extracted data
│ └── temp/ # Temporary files
│
└── build/
├── icon.ico # Executable icon
├── version_info.txt # Version information
└── stub.py # Encrypted payload stub


## Module Descriptions

### Core Modules

#### `core/__init__.py`
Core utility functions including:
- System information gathering
- File operations
- Encryption helpers
- Process management
- Windows registry operations

#### `core/builder.py`
Build system for creating executable:
- PyInstaller integration
- Payload encryption
- Stub generation
- Icon and version info embedding

#### `core/obfuscator.py`
Code obfuscation techniques:
- Variable renaming
- String encryption
- Dead code insertion
- Control flow flattening

#### `core/crypter.py`
Multi-layer encryption:
- AES encryption
- XOR encryption
- RC4 encryption
- Fernet encryption
- Multi-layer encryption

#### `core/persistence.py`
System persistence:
- Registry Run keys
- Scheduled tasks
- Startup folder
- Service installation
- WMI event subscription

### Data Collection Modules

#### `modules/system_info.py`
Collects:
- OS information
- CPU details
- GPU information
- Disk information
- Network details
- Installed software
- User accounts

#### `modules/browser_stealer.py`
Extracts from browsers:
- Cookies
- Passwords
- History
- Bookmarks
- Autofill data
- Credit cards

#### `modules/wallets.py`
Steals cryptocurrency wallets:
- MetaMask
- Exodus
- Atomic
- Electrum
- Bitcoin Core
- And more

#### `modules/discord_token.py`
Discord token extraction:
- Local Storage scanning
- Token validation
- User information
- Guild information

#### `modules/telegram.py`
Telegram session stealing:
- Session files
- Cache data
- Password extraction

#### `modules/file_grabber.py`
File search and extraction:
- Document files
- Images
- Archives
- Databases
- Configuration files

#### `modules/keylogger.py`
Keyboard input capture:
- Keystroke logging
- Window tracking
- Clipboard monitoring

#### `modules/screenshot.py`
Screen capture:
- Multi-monitor support
- Active window capture
- Webcam capture

#### `modules/clipboard.py`
Clipboard monitoring:
- Text capture
- Crypto address detection
- File capture

#### `modules/camera.py`
Webcam capture:
- Camera detection
- Frame capture
- Video recording

### Evasion Modules

#### `evasion/anti_vm.py`
Virtual machine detection:
- MAC address analysis
- WMI device checking
- Process detection
- File system analysis

#### `evasion/anti_debug.py`
Debugger detection:
- IsDebuggerPresent
- Remote debugger check
- PEB analysis
- Timing analysis

#### `evasion/anti_analysis.py`
Analysis tool detection:
- Process monitoring
- Window enumeration
- Service detection
- Driver checking

#### `evasion/sleep_obfuscation.py`
Sleep timing obfuscation:
- Random delays
- Jitter sleep
- Fragmented sleep
- CPU-intensive sleep

#### `evasion/process_hollowing.py`
Process injection:
- Process hollowing
- Shellcode injection
- DLL injection

### Network Modules

#### `network/exfil.py`
Data exfiltration:
- Discord webhook
- Telegram bot
- FTP upload
- Multiple methods

#### `network/encryption.py`
Data encryption:
- AES encryption
- XOR encryption
- Multi-layer encryption
- File encryption

#### `network/retry.py`
Retry logic:
- Exponential backoff
- Linear backoff
- Fixed delay
- Circuit breaker

## Configuration

The `config.json` file contains all settings:

```json
{
    "webhook": "Discord webhook URL",
    "telegram_token": "Telegram bot token",
    "encryption_key": "Encryption key",
    "anti_vm": true,
    "anti_debug": true,
    "steal_cookies": true,
    "steal_passwords": true,
    "keylogger": true,
    "screenshot": true,
    "persistence": true
}

This Infostealer is coded by: overkillxxx on discord :3

Build Process
Configure settings in config.json

Run builder:

bash
python core/builder.py
Features
Multi-browser Support: Chrome, Firefox, Edge, Brave

Cryptocurrency Wallet Stealing: 15+ wallets

Discord Token Grabbing: With validation

Telegram Session Stealing: Full session extraction

Keylogging: With window tracking

Screen Capture: Multi-monitor support

Webcam Capture: Camera access

File Grabbing: Smart file search

Persistence: Multiple methods

Evasion: Anti-VM, anti-debug, anti-analysis

Encryption: Multi-layer encryption

Exfiltration: Multiple channels

Dependencies
Install all dependencies:

bash
pip install -r requirements.txt
Usage
python
# Basic usage
python main.py

# With custom config
python main.py --config custom_config.json

# Build executable
python core/builder.py
Output
All collected data is stored in the output/ directory:

logs/: Keylogger logs

screenshots/: Screen captures

stolen/: Extracted data

temp/: Temporary files

This Infostealer is coded by: overkillxxx on discord :3
