# Install Script Testing Documentation

## Purpose
This document describes how to test the `install.sh` script to verify that it handles missing prerequisites correctly without exiting prematurely.

## What Was Fixed
The original `install.sh` script was minimal and would exit prematurely when npm or git were missing. The updated script now:

1. **Checks all prerequisites before exiting** - Collects all missing required prerequisites and displays them together
2. **Treats git as optional** - Shows a warning if git is missing but continues installation
3. **Provides helpful installation instructions** - Shows URLs and guidance for installing missing prerequisites
4. **Continues with installation** - Only exits if required prerequisites are missing, after checking all of them

## Prerequisites Checked

### Required:
- Python 3.9+
- pip3
- Node.js 18+
- npm

### Optional:
- git (shows warning if missing but continues)

## Testing the Fix

### Test 1: All Prerequisites Present
```bash
./install.sh
```

Expected: Script proceeds with installation, setting up backend, frontend, and services.

### Test 2: Missing npm (Required)
```bash
# Create a test environment without npm
TEMP_BIN=$(mktemp -d)
ln -s $(which python3) "$TEMP_BIN/python3"
ln -s $(which pip3) "$TEMP_BIN/pip3"
ln -s $(which node) "$TEMP_BIN/node"
ln -s $(which git) "$TEMP_BIN/git"
# npm intentionally omitted

# Run with modified PATH
PATH="$TEMP_BIN:$PATH" ./install.sh

# Cleanup
rm -rf "$TEMP_BIN"
```

Expected output:
```
[INFO] Starting SolarApp installation...

[INFO] Checking prerequisites...
[INFO] Python 3.x.x detected (>= 3.9 required)
[INFO] pip3 is installed
[INFO] Node.js is installed
[INFO] Node.js 18.x.x detected (>= 18 required)
[ERROR] npm is NOT installed
[INFO] git is installed

[ERROR] Missing required prerequisites:
  - npm

[INFO] Please install the missing prerequisites and try again:
  - Python 3.9+: https://www.python.org/downloads/
  - Node.js 18+: https://nodejs.org/en/download/
  - pip3: Usually comes with Python, or install via package manager
  - npm: Usually comes with Node.js
  - git (optional): https://git-scm.com/downloads
```

Exit code: 1

### Test 3: Missing git (Optional)
```bash
# Create a test environment without git
TEMP_BIN=$(mktemp -d)
ln -s $(which python3) "$TEMP_BIN/python3"
ln -s $(which pip3) "$TEMP_BIN/pip3"
ln -s $(which node) "$TEMP_BIN/node"
ln -s $(which npm) "$TEMP_BIN/npm"
# git intentionally omitted

# Run with modified PATH
PATH="$TEMP_BIN:$PATH" ./install.sh

# Cleanup
rm -rf "$TEMP_BIN"
```

Expected: Script shows a warning about git being missing but continues with installation.

### Test 4: Multiple Missing Prerequisites
```bash
# Create a test environment without npm and pip3
TEMP_BIN=$(mktemp -d)
ln -s $(which python3) "$TEMP_BIN/python3"
ln -s $(which node) "$TEMP_BIN/node"
ln -s $(which git) "$TEMP_BIN/git"
# npm and pip3 intentionally omitted

# Run with modified PATH
PATH="$TEMP_BIN:$PATH" ./install.sh

# Cleanup
rm -rf "$TEMP_BIN"
```

Expected: Script checks all prerequisites, collects all missing ones, and displays them together before exiting.

## Key Improvements

1. **No Premature Exit**: The script uses `|| true` after each check to prevent `set -e` from causing premature exit
2. **Collects All Errors**: Missing prerequisites are collected in an array and displayed together
3. **User-Friendly**: Provides colored output and clear installation instructions
4. **Optional Dependencies**: Distinguishes between required and optional prerequisites
5. **Comprehensive Setup**: Includes backend, frontend, XML parser service, systemd services, and optional sample data

## Verification Commands

After installation completes successfully:

```bash
# Check backend virtual environment
ls -la backend/.venv

# Check frontend node_modules
ls -la frontend/node_modules

# Check XML parser virtual environment
ls -la backend/services/xml_parser/.venv

# Check environment file
cat backend/.env

# Check systemd services (if running with sudo)
systemctl status solarapp-backend
systemctl status solarapp-xml-parser
```

## Manual Testing Results

✅ Script checks all prerequisites before exiting
✅ Missing required prerequisites are collected and displayed together
✅ Optional prerequisites (git) show warnings but don't block installation
✅ Helpful installation instructions are provided
✅ When all prerequisites are present, installation proceeds correctly
