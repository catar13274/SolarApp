# Install Script Testing Documentation

## Purpose
This document describes how to test the `install.sh` script to verify that it handles missing prerequisites correctly without exiting prematurely.

## What Was Fixed
The installation script now supports optional frontend installation:

1. **Checks all prerequisites before exiting** - Collects all missing required prerequisites and displays them together
2. **Treats Node.js/npm as optional** - Shows a warning if Node.js/npm are missing but continues installation with backend only
3. **Treats git as optional** - Shows a warning if git is missing but continues installation
4. **Provides helpful installation instructions** - Shows URLs and guidance for installing missing prerequisites
5. **Continues with installation** - Only exits if required prerequisites (Python, pip3) are missing, after checking all of them
6. **Skips frontend when Node.js/npm unavailable** - Allows backend-only installation on systems without Node.js

## Prerequisites Checked

### Required:
- Python 3.9+
- pip3

### Optional (for frontend):
- Node.js 18+
- npm

### Optional (for development):
- git

## Testing the Fix

### Test 1: All Prerequisites Present
```bash
./install.sh
```

Expected: Script proceeds with installation, setting up backend, frontend, and services.

### Test 2: Missing Node.js and npm (Optional - Should Continue)
```bash
# Create a test environment without Node.js and npm
TEMP_BIN=$(mktemp -d)
ln -s $(which python3) "$TEMP_BIN/python3"
ln -s $(which pip3) "$TEMP_BIN/pip3"
ln -s $(which git) "$TEMP_BIN/git"
# Node.js and npm intentionally omitted

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
[WARNING] Node.js is NOT installed (optional)
[WARNING] npm is NOT installed (optional)
[INFO] git is installed

[WARNING] Node.js and/or npm are not installed - frontend will be skipped
[INFO] To install the frontend later, install Node.js 18+ and npm, then run:
  cd frontend && npm install && npm run build

[WARNING] Optional prerequisites missing (installation will continue):
  - Node.js
  - npm

[INFO] All required prerequisites are installed!
[INFO] Setting up backend...
[INFO] Skipping frontend setup (Node.js/npm not available)
[INFO] Setting up XML Parser service...
... (installation continues)
```

Exit code: 0 (success)

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

### Test 4: Missing Python (Required)
```bash
# Create a test environment without Python
TEMP_BIN=$(mktemp -d)
ln -s $(which node) "$TEMP_BIN/node"
ln -s $(which npm) "$TEMP_BIN/npm"
ln -s $(which git) "$TEMP_BIN/git"
# Python and pip3 intentionally omitted

# Run with modified PATH
PATH="$TEMP_BIN:$PATH" ./install.sh

# Cleanup
rm -rf "$TEMP_BIN"
```

Expected: Script checks all prerequisites, detects Python is missing, and displays error message before exiting with code 1.

## Key Improvements

1. **No Premature Exit**: The script uses `|| true` after each check to prevent `set -e` from causing premature exit
2. **Collects All Errors**: Missing prerequisites are collected in an array and displayed together
3. **User-Friendly**: Provides colored output and clear installation instructions
4. **Optional Frontend**: Node.js and npm are now optional - backend can be installed without frontend
5. **Flexible Installation**: Users can install just the backend on lightweight systems, then add frontend later
6. **Optional Dependencies**: Distinguishes between required and optional prerequisites
7. **Comprehensive Setup**: Includes backend, frontend (optional), XML parser service, systemd services, and optional sample data

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
✅ Optional prerequisites (git, Node.js, npm) show warnings but don't block installation
✅ Backend installation proceeds even without Node.js/npm
✅ Frontend installation is skipped when Node.js/npm are not available
✅ Helpful installation instructions are provided
✅ When all prerequisites are present, installation proceeds correctly with both backend and frontend
