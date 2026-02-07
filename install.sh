#!/bin/bash

# This script installs necessary services for SolarApp

set -e  # Exit on error, but we'll handle critical checks manually

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Track missing prerequisites
MISSING_PREREQS=()
WARNINGS=()

# Function to check command availability
check_command() {
    local cmd=$1
    local name=$2
    local required=$3
    
    if command -v "$cmd" &> /dev/null; then
        print_info "$name is installed"
        return 0
    else
        if [ "$required" = "true" ]; then
            MISSING_PREREQS+=("$name")
            print_error "$name is NOT installed"
        else
            WARNINGS+=("$name")
            print_warning "$name is NOT installed (optional)"
        fi
        return 1
    fi
}

# Function to check version
check_python_version() {
    if command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1 | awk '{print $2}')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            print_info "Python $version detected (>= 3.9 required)"
            return 0
        else
            print_error "Python $version detected, but 3.9+ is required"
            MISSING_PREREQS+=("Python 3.9+")
            return 1
        fi
    else
        print_error "python3 is NOT installed"
        MISSING_PREREQS+=("Python 3.9+")
        return 1
    fi
}

check_node_version() {
    if command -v node &> /dev/null; then
        local version=$(node --version 2>&1 | sed 's/v//')
        local major=$(echo $version | cut -d. -f1)
        
        if [ "$major" -ge 18 ]; then
            print_info "Node.js $version detected (>= 18 required)"
            return 0
        else
            print_error "Node.js $version detected, but 18+ is required"
            MISSING_PREREQS+=("Node.js 18+")
            return 1
        fi
    else
        # Node not found - this case is already handled by check_command
        return 1
    fi
}

print_info "Starting SolarApp installation..."
echo

# Check prerequisites
print_info "Checking prerequisites..."
check_python_version || true
check_command "pip3" "pip3" "true" || true
# Only check node version if node command exists
if command -v node &> /dev/null; then
    check_node_version || true
else
    check_command "node" "Node.js" "true" || true
fi
check_command "npm" "npm" "true" || true
check_command "git" "git" "false" || true
echo

# If critical prerequisites are missing, display helpful message and exit
if [ ${#MISSING_PREREQS[@]} -gt 0 ]; then
    print_error "Missing required prerequisites:"
    for prereq in "${MISSING_PREREQS[@]}"; do
        echo "  - $prereq"
    done
    echo
    print_info "Please install the missing prerequisites and try again:"
    echo "  - Python 3.9+: https://www.python.org/downloads/"
    echo "  - Node.js 18+: https://nodejs.org/en/download/"
    echo "  - pip3: Usually comes with Python, or install via package manager"
    echo "  - npm: Usually comes with Node.js"
    echo "  - git (optional): https://git-scm.com/downloads"
    exit 1
fi

# Display warnings for optional prerequisites
if [ ${#WARNINGS[@]} -gt 0 ]; then
    print_warning "Optional prerequisites missing (installation will continue):"
    for warning in "${WARNINGS[@]}"; do
        echo "  - $warning"
    done
    echo
fi

print_info "All required prerequisites are installed!"
echo

# Setup backend
print_info "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv .venv
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup .env file
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_info "Please review and update backend/.env with your configuration"
else
    print_info ".env file already exists"
fi

# Initialize database
print_info "Database will be initialized on first run"

cd ..
echo

# Setup frontend
print_info "Setting up frontend..."
cd frontend

# Install Node dependencies
print_info "Installing Node.js dependencies (this may take a few minutes)..."
npm install

# Build frontend
print_info "Building frontend..."
npm run build

cd ..
echo

# Setup XML Parser Service
print_info "Setting up XML Parser service..."
cd backend/services/xml_parser

# Create virtual environment for XML parser if it doesn't exist
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment for XML parser..."
    python3 -m venv .venv
else
    print_info "Virtual environment already exists for XML parser"
fi

# Activate virtual environment
source .venv/bin/activate

# Install XML parser dependencies
print_info "Installing XML parser dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

deactivate
cd ../../..
echo

# Define installation variable for systemd services
INSTALL_SERVICES="yes"

# Create systemd services
if [ "$INSTALL_SERVICES" = "yes" ]; then
    print_info "Setting up systemd services..."
    
    # Check if systemd is available
    if [ ! -d "/etc/systemd/system" ]; then
        print_warning "Systemd not available on this system, skipping service creation"
    elif [ "$EUID" -ne 0 ]; then
        # Not running as root
        print_warning "Systemd service installation requires sudo privileges"
        print_info "You can manually create systemd services later or run this script with sudo"
        print_info "Skipping systemd service creation..."
    else
        # We're running as root and systemd is available
        INSTALL_DIR=$(pwd)
        
        # Determine the user to run services as
        # If running via sudo, use SUDO_USER; otherwise use a default non-root user
        if [ -n "$SUDO_USER" ]; then
            SERVICE_USER="$SUDO_USER"
        else
            # Running directly as root, try to find a reasonable user
            SERVICE_USER=$(logname 2>/dev/null || echo "nobody")
            print_warning "Running as root without sudo, using user: $SERVICE_USER"
        fi
        
        # Create backend service
        print_info "Creating solarapp-backend.service..."
        cat > /etc/systemd/system/solarapp-backend.service <<EOF
[Unit]
Description=SolarApp Backend API
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/.venv/bin"
ExecStart=$INSTALL_DIR/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        # Create XML parser service
        print_info "Creating solarapp-xml-parser.service..."
        cat > /etc/systemd/system/solarapp-xml-parser.service <<EOF
[Unit]
Description=SolarApp XML Parser Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/backend/services/xml_parser
Environment="PATH=$INSTALL_DIR/backend/services/xml_parser/.venv/bin"
ExecStart=$INSTALL_DIR/backend/services/xml_parser/.venv/bin/python parser_app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        # Reload systemd, enable and start services
        systemctl daemon-reload
        systemctl enable solarapp-backend.service
        systemctl enable solarapp-xml-parser.service
        systemctl start solarapp-backend.service
        systemctl start solarapp-xml-parser.service
        
        print_info "Systemd services created and started"
    fi
else
    print_info "Skipping systemd service installation (INSTALL_SERVICES != yes)"
fi

echo

# Ask about loading sample data
print_info "Installation complete!"
echo
read -p "Would you like to load sample data? (y/N): " load_sample
if [[ $load_sample =~ ^[Yy]$ ]]; then
    print_info "Loading sample data..."
    cd backend
    source .venv/bin/activate
    python sample_data.py
    deactivate
    cd ..
    print_info "Sample data loaded successfully"
else
    print_info "Skipping sample data loading"
fi

echo
print_info "=========================================="
print_info "SolarApp installation completed successfully!"
print_info "=========================================="
echo
print_info "Next steps:"
if [ "$INSTALL_SERVICES" = "yes" ] && [ -d "/etc/systemd/system" ] && [ "$EUID" -eq 0 ]; then
    echo "  - Backend API is running at http://localhost:8000"
    echo "  - XML Parser service is running at http://localhost:5000"
    echo "  - Check service status: systemctl status solarapp-backend"
else
    echo "  - Start backend: cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo "  - Start XML parser: cd backend/services/xml_parser && source .venv/bin/activate && python parser_app.py"
    echo "  - Start frontend dev server: cd frontend && npm run dev"
fi
echo "  - Review and update configuration in backend/.env"
echo "  - API documentation: http://localhost:8000/docs"
echo