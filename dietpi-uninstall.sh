#!/bin/bash

# SolarApp Diet Pi Uninstallation Script
# Removes SolarApp installation from Raspberry Pi running Diet Pi OS

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

# Detect current user (for ownership operations if needed)
CURRENT_USER=${SUDO_USER:-$(whoami)}
if [ "$CURRENT_USER" = "root" ] && [ -n "$SUDO_USER" ]; then
    CURRENT_USER=$SUDO_USER
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run with sudo"
    echo "Usage: sudo ./dietpi-uninstall.sh"
    exit 1
fi

echo
print_warning "=========================================="
print_warning "SolarApp Diet Pi Uninstallation"
print_warning "=========================================="
echo
print_warning "This script will remove SolarApp and its components from your system."
echo

# Confirm uninstallation
read -p "Are you sure you want to uninstall SolarApp? (yes/no): " confirm
if [[ ! $confirm =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Uninstallation cancelled."
    exit 0
fi

echo
print_info "Step 1: Stopping services..."

# Stop and disable backend service
if systemctl is-active --quiet solarapp-backend.service 2>/dev/null; then
    print_info "Stopping solarapp-backend.service..."
    systemctl stop solarapp-backend.service
fi

if systemctl is-enabled --quiet solarapp-backend.service 2>/dev/null; then
    print_info "Disabling solarapp-backend.service..."
    systemctl disable solarapp-backend.service
fi

# Stop and disable backend RPI service
if systemctl is-active --quiet solarapp-backend-rpi.service 2>/dev/null; then
    print_info "Stopping solarapp-backend-rpi.service..."
    systemctl stop solarapp-backend-rpi.service
fi

if systemctl is-enabled --quiet solarapp-backend-rpi.service 2>/dev/null; then
    print_info "Disabling solarapp-backend-rpi.service..."
    systemctl disable solarapp-backend-rpi.service
fi

# Stop and disable XML parser service
if systemctl is-active --quiet solarapp-xml-parser.service 2>/dev/null; then
    print_info "Stopping solarapp-xml-parser.service..."
    systemctl stop solarapp-xml-parser.service
fi

if systemctl is-enabled --quiet solarapp-xml-parser.service 2>/dev/null; then
    print_info "Disabling solarapp-xml-parser.service..."
    systemctl disable solarapp-xml-parser.service
fi

# Stop and disable XML parser RPI service
if systemctl is-active --quiet solarapp-xml-parser-rpi.service 2>/dev/null; then
    print_info "Stopping solarapp-xml-parser-rpi.service..."
    systemctl stop solarapp-xml-parser-rpi.service
fi

if systemctl is-enabled --quiet solarapp-xml-parser-rpi.service 2>/dev/null; then
    print_info "Disabling solarapp-xml-parser-rpi.service..."
    systemctl disable solarapp-xml-parser-rpi.service
fi

echo
print_info "Step 2: Removing systemd service files..."

# Remove service files
SERVICE_FILES=(
    "/etc/systemd/system/solarapp-backend.service"
    "/etc/systemd/system/solarapp-backend-rpi.service"
    "/etc/systemd/system/solarapp-xml-parser.service"
    "/etc/systemd/system/solarapp-xml-parser-rpi.service"
)

for service_file in "${SERVICE_FILES[@]}"; do
    if [ -f "$service_file" ]; then
        print_info "Removing $service_file..."
        rm -f "$service_file"
    fi
done

# Reload systemd
print_info "Reloading systemd daemon..."
systemctl daemon-reload

echo
print_info "Step 3: Removing nginx configuration..."

# Remove nginx site configuration
if [ -f "/etc/nginx/sites-enabled/solarapp" ]; then
    print_info "Removing nginx site configuration from sites-enabled..."
    rm -f /etc/nginx/sites-enabled/solarapp
fi

if [ -f "/etc/nginx/sites-available/solarapp" ]; then
    print_info "Removing nginx site configuration from sites-available..."
    rm -f /etc/nginx/sites-available/solarapp
fi

# Test and restart nginx if it's running
if systemctl is-active --quiet nginx.service 2>/dev/null; then
    if nginx -t 2>&1 | grep -q "successful"; then
        print_info "Restarting nginx..."
        systemctl restart nginx.service
    else
        print_warning "nginx configuration has errors, skipping restart"
    fi
fi

echo
print_info "Step 4: Backing up database..."

# Ask if user wants to keep database backup
read -p "Do you want to create a backup of the database before removal? (y/N): " backup_db
if [[ $backup_db =~ ^[Yy]$ ]]; then
    BACKUP_DIR="$INSTALL_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    DATE=$(date +%Y%m%d_%H%M%S)
    
    if [ -f "$INSTALL_DIR/backend/data/solarapp.db" ]; then
        print_info "Backing up database to $BACKUP_DIR/solarapp_$DATE.db..."
        cp "$INSTALL_DIR/backend/data/solarapp.db" "$BACKUP_DIR/solarapp_$DATE.db"
        print_info "Database backup created successfully!"
    else
        print_warning "Database file not found, skipping backup"
    fi
else
    print_info "Skipping database backup"
fi

echo
print_info "Step 5: Removing application files..."

# Confirm removal of application directory
read -p "Remove application directory $INSTALL_DIR? (yes/no): " remove_app
if [[ $remove_app =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Removing application directory..."
    # Don't remove if it's the current directory and contains this script
    SCRIPT_PATH="$(readlink -f "$0")"
    SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
    
    if [ "$SCRIPT_DIR" = "$INSTALL_DIR" ]; then
        print_warning "Cannot remove current directory while script is running"
        print_info "Please remove manually after script completes:"
        echo "  rm -rf $INSTALL_DIR"
    else
        rm -rf "$INSTALL_DIR"
        print_info "Application directory removed"
    fi
else
    print_info "Keeping application directory at $INSTALL_DIR"
fi

echo
print_info "Step 6: Cleaning up optional components..."

# Ask about removing system packages
read -p "Remove system packages (Python, nginx, etc.)? This may affect other applications. (y/N): " remove_packages
if [[ $remove_packages =~ ^[Yy]$ ]]; then
    print_warning "Removing system packages..."
    
    # Only remove if Diet Pi
    if [ "$IS_DIETPI" = true ]; then
        print_info "Use 'dietpi-software uninstall' to remove packages as needed"
        echo "  - Python 3 (ID 130): dietpi-software uninstall 130"
        echo "  - nginx (ID 85): dietpi-software uninstall 85"
        echo "  - Node.js (ID 83): dietpi-software uninstall 83"
        echo "  - Git (ID 17): dietpi-software uninstall 17"
    else
        print_info "To remove packages manually:"
        echo "  sudo apt remove python3-pip python3-venv nginx nodejs npm git"
        echo "  sudo apt autoremove"
    fi
else
    print_info "Keeping system packages (Python, nginx, etc.)"
fi

echo
print_info "=========================================="
print_info "Uninstallation Complete!"
print_info "=========================================="
echo

print_info "Summary of removed components:"
echo "  ✓ Systemd services stopped and removed"
echo "  ✓ nginx configuration removed"
if [[ $remove_app =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "  ✓ Application files removed"
else
    echo "  - Application files kept at $INSTALL_DIR"
fi
if [[ $backup_db =~ ^[Yy]$ ]]; then
    echo "  ✓ Database backup created at $BACKUP_DIR"
fi
echo

if [ "$SCRIPT_DIR" = "$INSTALL_DIR" ]; then
    print_warning "Reminder: Remove installation directory manually:"
    echo "  rm -rf $INSTALL_DIR"
    echo
fi

print_info "SolarApp has been uninstalled from your system."
print_note "Thank you for using SolarApp! 👋"
