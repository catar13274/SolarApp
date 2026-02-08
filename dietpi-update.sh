#!/bin/bash

# SolarApp Diet Pi Update Script
# Updates SolarApp installation on Raspberry Pi running Diet Pi OS

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_note() {
    echo -e "${BLUE}[NOTE]${NC} $1"
}

# Detect if running on Diet Pi
IS_DIETPI=false
if [ -f "/boot/dietpi/.version" ] || [ -f "/boot/dietpi.txt" ]; then
    IS_DIETPI=true
    DIETPI_VERSION=$(cat /boot/dietpi/.version 2>/dev/null || echo "unknown")
    print_note "Diet Pi detected - Version: $DIETPI_VERSION"
else
    print_warning "Diet Pi not detected, continuing on standard system..."
fi

# Detect installation directory
INSTALL_DIR=$(cd "$(dirname "$0")" && pwd)
print_info "Installation directory: $INSTALL_DIR"

# Detect current user
CURRENT_USER=${SUDO_USER:-$(whoami)}
print_info "Running as user: $CURRENT_USER"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run with sudo"
    echo "Usage: sudo ./dietpi-update.sh"
    exit 1
fi

echo
print_info "=========================================="
print_info "SolarApp Diet Pi Update"
print_info "=========================================="
echo

# Check if this is a git repository
if [ ! -d ".git" ]; then
    print_error "This directory is not a git repository"
    print_info "Cannot update from git. Please manually update the application."
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    print_warning "You have uncommitted changes in the repository"
    echo
    git status --short
    echo
    read -p "Continue with update? This may cause conflicts. (y/N): " continue_update
    if [[ ! $continue_update =~ ^[Yy]$ ]]; then
        print_info "Update cancelled."
        exit 0
    fi
fi

echo
print_info "Step 1: Stopping services..."

# Detect which services are running
BACKEND_SERVICE=""
XML_PARSER_SERVICE=""

if systemctl is-active --quiet solarapp-backend-rpi.service 2>/dev/null; then
    BACKEND_SERVICE="solarapp-backend-rpi.service"
elif systemctl is-active --quiet solarapp-backend.service 2>/dev/null; then
    BACKEND_SERVICE="solarapp-backend.service"
fi

if systemctl is-active --quiet solarapp-xml-parser-rpi.service 2>/dev/null; then
    XML_PARSER_SERVICE="solarapp-xml-parser-rpi.service"
elif systemctl is-active --quiet solarapp-xml-parser.service 2>/dev/null; then
    XML_PARSER_SERVICE="solarapp-xml-parser.service"
fi

# Stop services
if [ -n "$BACKEND_SERVICE" ]; then
    print_info "Stopping $BACKEND_SERVICE..."
    systemctl stop "$BACKEND_SERVICE"
else
    print_warning "Backend service not found or not running"
fi

if [ -n "$XML_PARSER_SERVICE" ]; then
    print_info "Stopping $XML_PARSER_SERVICE..."
    systemctl stop "$XML_PARSER_SERVICE"
else
    print_warning "XML parser service not found or not running"
fi

echo
print_info "Step 2: Backing up database..."

BACKUP_DIR="$INSTALL_DIR/backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)

if [ -f "$INSTALL_DIR/backend/data/solarapp.db" ]; then
    print_info "Creating database backup..."
    cp "$INSTALL_DIR/backend/data/solarapp.db" "$BACKUP_DIR/solarapp_${DATE}.db"
    print_info "Database backed up to $BACKUP_DIR/solarapp_${DATE}.db"
    
    # Keep only last 10 backups
    print_info "Cleaning old backups (keeping last 10)..."
    cd "$BACKUP_DIR"
    ls -t solarapp_*.db 2>/dev/null | tail -n +11 | xargs -r rm --
    cd "$INSTALL_DIR"
else
    print_warning "Database file not found, skipping backup"
fi

echo
print_info "Step 3: Fetching latest changes from git..."

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_info "Current branch: $CURRENT_BRANCH"

# Get current commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
print_info "Current commit: $CURRENT_COMMIT"

# Fetch updates
print_info "Fetching updates..."
git fetch origin

# Check if there are updates available
UPDATES_AVAILABLE=$(git rev-list HEAD..origin/$CURRENT_BRANCH --count 2>/dev/null || echo "0")

if [ "$UPDATES_AVAILABLE" = "0" ]; then
    print_info "Already up to date! No updates available."
    echo
    read -p "Do you want to reinstall dependencies anyway? (y/N): " reinstall
    if [[ ! $reinstall =~ ^[Yy]$ ]]; then
        print_info "Update cancelled. Restarting services..."
        if [ -n "$BACKEND_SERVICE" ]; then
            systemctl start "$BACKEND_SERVICE"
        fi
        if [ -n "$XML_PARSER_SERVICE" ]; then
            systemctl start "$XML_PARSER_SERVICE"
        fi
        exit 0
    fi
    SKIP_GIT_PULL=true
else
    print_info "$UPDATES_AVAILABLE update(s) available"
    SKIP_GIT_PULL=false
fi

# Pull latest changes
if [ "$SKIP_GIT_PULL" = false ]; then
    print_info "Pulling latest changes..."
    if git pull origin "$CURRENT_BRANCH"; then
        NEW_COMMIT=$(git rev-parse --short HEAD)
        print_info "Updated from $CURRENT_COMMIT to $NEW_COMMIT"
    else
        print_error "Failed to pull updates. Please resolve conflicts manually."
        print_info "Restarting services..."
        if [ -n "$BACKEND_SERVICE" ]; then
            systemctl start "$BACKEND_SERVICE"
        fi
        if [ -n "$XML_PARSER_SERVICE" ]; then
            systemctl start "$XML_PARSER_SERVICE"
        fi
        exit 1
    fi
fi

echo
print_info "Step 4: Updating backend dependencies..."

cd "$INSTALL_DIR/backend"

if [ ! -d ".venv" ]; then
    print_warning "Backend virtual environment not found, creating..."
    python3 -m venv .venv
fi

print_info "Activating virtual environment..."
source .venv/bin/activate

print_info "Upgrading pip..."
pip install --upgrade pip --quiet

print_info "Installing/updating backend dependencies..."
pip install -r requirements.txt --quiet

# Check if there are database migrations to run
if [ -f "alembic.ini" ] && [ -d "alembic" ]; then
    print_info "Checking for database migrations..."
    if command -v alembic &> /dev/null; then
        print_info "Running database migrations..."
        alembic upgrade head
    else
        print_warning "Alembic not found, skipping migrations"
    fi
fi

deactivate
cd "$INSTALL_DIR"

echo
print_info "Step 5: Updating XML parser dependencies..."

cd "$INSTALL_DIR/backend/services/xml_parser"

if [ ! -d ".venv" ]; then
    print_warning "XML parser virtual environment not found, creating..."
    python3 -m venv .venv
fi

print_info "Activating virtual environment..."
source .venv/bin/activate

print_info "Upgrading pip..."
pip install --upgrade pip --quiet

print_info "Installing/updating XML parser dependencies..."
pip install -r requirements.txt --quiet

deactivate
cd "$INSTALL_DIR"

echo
print_info "Step 6: Updating frontend..."

# Check if Node.js is available
if command -v npm &> /dev/null; then
    cd "$INSTALL_DIR/frontend"
    
    print_info "Installing/updating frontend dependencies..."
    npm install --silent
    
    print_info "Building frontend for production..."
    npm run build
    
    cd "$INSTALL_DIR"
    print_info "Frontend updated successfully"
else
    print_warning "Node.js not found. Frontend not updated."
    print_info "To update frontend manually:"
    echo "  1. Install Node.js 18+"
    echo "  2. cd $INSTALL_DIR/frontend"
    echo "  3. npm install && npm run build"
    echo "  4. sudo systemctl restart nginx"
fi

echo
print_info "Step 7: Setting proper ownership..."

chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"

echo
print_info "Step 8: Restarting services..."

# Start services
if [ -n "$BACKEND_SERVICE" ]; then
    print_info "Starting $BACKEND_SERVICE..."
    systemctl start "$BACKEND_SERVICE"
    
    # Wait a moment for service to start
    sleep 2
    
    if systemctl is-active --quiet "$BACKEND_SERVICE"; then
        print_info "✓ Backend service is running"
    else
        print_error "✗ Backend service failed to start"
        print_info "Check logs with: journalctl -u $BACKEND_SERVICE -n 50"
    fi
else
    print_warning "Backend service not configured"
fi

if [ -n "$XML_PARSER_SERVICE" ]; then
    print_info "Starting $XML_PARSER_SERVICE..."
    systemctl start "$XML_PARSER_SERVICE"
    
    # Wait a moment for service to start
    sleep 2
    
    if systemctl is-active --quiet "$XML_PARSER_SERVICE"; then
        print_info "✓ XML parser service is running"
    else
        print_error "✗ XML parser service failed to start"
        print_info "Check logs with: journalctl -u $XML_PARSER_SERVICE -n 50"
    fi
else
    print_warning "XML parser service not configured"
fi

# Restart nginx if it's running
if systemctl is-active --quiet nginx.service 2>/dev/null; then
    print_info "Restarting nginx..."
    systemctl restart nginx.service
fi

echo
print_info "=========================================="
print_info "Update Complete!"
print_info "=========================================="
echo

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

print_info "SolarApp has been updated successfully!"
echo
echo "Access the application:"
echo "  Frontend:  http://$IP_ADDRESS/"
echo "  API Docs:  http://$IP_ADDRESS/docs"
echo "  Backend:   http://$IP_ADDRESS/api"
echo

print_info "Database backups are stored in:"
echo "  $BACKUP_DIR"
echo

print_info "To view service logs:"
if [ -n "$BACKEND_SERVICE" ]; then
    echo "  Backend:     journalctl -u $BACKEND_SERVICE -f"
fi
if [ -n "$XML_PARSER_SERVICE" ]; then
    echo "  XML Parser:  journalctl -u $XML_PARSER_SERVICE -f"
fi
echo "  nginx:       journalctl -u nginx -f"
echo

print_info "Update completed successfully! 🎉"
