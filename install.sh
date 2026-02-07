#!/usr/bin/env bash
# SolarApp Installation Script for Raspberry Pi / Ubuntu / Debian

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
INSTALL_DIR="/opt/solarapp"
INSTALL_SERVICES="ask"
INSTALL_MODE="prod"  # prod or dev
SAMPLE_DATA="ask"
REPO_URL="https://github.com/catar13274/SolarApp.git"

# Functions
print_header() { 
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "This script should not be run as root"
    print_info "Run as a regular user with sudo privileges"
    exit 1
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            INSTALL_MODE="dev"
            shift
            ;;
        --prod)
            INSTALL_MODE="prod"
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --no-services)
            INSTALL_SERVICES="no"
            shift
            ;;
        --sample-data)
            SAMPLE_DATA="yes"
            shift
            ;;
        --auto-confirm)
            INSTALL_SERVICES="yes"
            SAMPLE_DATA="yes"
            shift
            ;;
        --help)
            echo "SolarApp Installation Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev              Install in development mode"
            echo "  --prod             Install in production mode (default)"
            echo "  --install-dir DIR  Installation directory (default: /opt/solarapp)"
            echo "  --no-services      Don't install systemd services"
            echo "  --sample-data      Load sample data automatically"
            echo "  --auto-confirm     Auto-confirm all prompts"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_header "SolarApp Installation Script"
print_info "Installation mode: $INSTALL_MODE"
print_info "Installation directory: $INSTALL_DIR"
echo ""

# Check prerequisites
print_header "Checking Prerequisites"

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_warning "$1 is not installed"
        return 1
    fi
}

# Check Python
if check_command python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_info "Python version: $PYTHON_VERSION"
fi

# Check Node.js
if check_command node; then
    NODE_VERSION=$(node --version)
    print_info "Node.js version: $NODE_VERSION"
fi

# Check npm
if check_command npm; then
    NPM_VERSION=$(npm --version)
    print_info "npm version: $NPM_VERSION"
fi

# Check git
if check_command git; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_info "git version: $GIT_VERSION"
fi

# Install missing dependencies
print_header "Installing Missing Dependencies"

sudo apt-get update

# Install Python if missing
if ! command -v python3 &> /dev/null; then
    print_info "Installing Python 3..."
    sudo apt-get install -y python3 python3-pip python3-venv
    print_success "Python 3 installed"
fi

# Install Node.js if missing or version too old
if ! command -v node &> /dev/null; then
    print_info "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_success "Node.js installed"
fi

# Install git if missing
if ! command -v git &> /dev/null; then
    print_info "Installing git..."
    sudo apt-get install -y git
    print_success "Git installed"
fi

# Create installation directory
print_header "Setting Up Installation Directory"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Directory $INSTALL_DIR already exists"
    read -p "Do you want to remove it and reinstall? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf "$INSTALL_DIR"
        print_success "Removed existing installation"
    else
        print_error "Installation cancelled"
        exit 1
    fi
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown $(whoami):$(whoami) "$INSTALL_DIR"
print_success "Created installation directory: $INSTALL_DIR"

# Clone repository
print_header "Cloning SolarApp Repository"

cd "$INSTALL_DIR"
if [ -d ".git" ]; then
    print_info "Repository already cloned, pulling latest changes..."
    git pull
else
    print_info "Cloning from $REPO_URL..."
    git clone "$REPO_URL" .
fi
print_success "Repository cloned"

# Setup Backend
print_header "Setting Up Backend"

cd "$INSTALL_DIR/backend"

# Create virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv .venv
print_success "Virtual environment created"

# Activate and install dependencies
print_info "Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Install XML parser dependencies
print_info "Installing XML parser dependencies..."
cd services/xml_parser
pip install -r requirements.txt
cd ../..
print_success "XML parser dependencies installed"

# Generate random token for XML parser
XML_PARSER_TOKEN=$(openssl rand -hex 32)

# Create .env file
print_info "Creating .env file..."
cat > .env << EOF
SOLARAPP_DB_URL=sqlite:///./solarapp.db
XML_PARSER_URL=http://localhost:5000
XML_PARSER_TOKEN=$XML_PARSER_TOKEN
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF
print_success ".env file created"

# Initialize database
print_info "Initializing database..."
python3 -c "from app.database import create_db_and_tables; create_db_and_tables()"
print_success "Database initialized"

# Load sample data if requested
if [ "$SAMPLE_DATA" = "ask" ]; then
    read -p "Do you want to load sample data? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        SAMPLE_DATA="yes"
    fi
fi

if [ "$SAMPLE_DATA" = "yes" ]; then
    print_info "Loading sample data..."
    python3 sample_data.py
    print_success "Sample data loaded"
fi

deactivate

# Setup Frontend
print_header "Setting Up Frontend"

cd "$INSTALL_DIR/frontend"

# Create .env file
print_info "Creating frontend .env file..."
cat > .env << EOF
VITE_API_URL=http://localhost:8000
EOF
print_success "Frontend .env file created"

# Install npm dependencies
print_info "Installing Node.js dependencies (this may take a while)..."
npm install
print_success "Node.js dependencies installed"

# Build for production if in prod mode
if [ "$INSTALL_MODE" = "prod" ]; then
    print_info "Building frontend for production..."
    npm run build
    print_success "Frontend built"
    
    # Install serve globally
    print_info "Installing serve package..."
    sudo npm install -g serve
    print_success "Serve package installed"
fi

# Setup systemd services
if [ "$INSTALL_SERVICES" = "ask" ]; then
    echo ""
    read -p "Do you want to install systemd services? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        INSTALL_SERVICES="yes"
    else
        INSTALL_SERVICES="no"
    fi
fi

if [ "$INSTALL_SERVICES" = "yes" ]; then
    print_header "Installing Systemd Services"
    
    # Create solarapp user
    if ! id "solarapp" &>/dev/null; then
        print_info "Creating solarapp user..."
        sudo useradd -r -s /bin/false solarapp
        print_success "User created"
    fi
    
    # Set ownership
    print_info "Setting permissions..."
    sudo chown -R solarapp:solarapp "$INSTALL_DIR"
    sudo chmod -R 755 "$INSTALL_DIR"
    
    # Backend service
    print_info "Creating backend service..."
    sudo tee /etc/systemd/system/solarapp-backend.service > /dev/null << EOF
[Unit]
Description=SolarApp Backend API
After=network.target

[Service]
Type=simple
User=solarapp
Group=solarapp
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/.venv/bin"
EnvironmentFile=$INSTALL_DIR/backend/.env
ExecStart=$INSTALL_DIR/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    print_success "Backend service created"
    
    # XML Parser service
    print_info "Creating XML parser service..."
    sudo tee /etc/systemd/system/solarapp-xml-parser.service > /dev/null << EOF
[Unit]
Description=SolarApp XML Parser Service
After=network.target

[Service]
Type=simple
User=solarapp
Group=solarapp
WorkingDirectory=$INSTALL_DIR/backend/services/xml_parser
Environment="PATH=$INSTALL_DIR/backend/.venv/bin"
Environment="XML_PARSER_TOKEN=$XML_PARSER_TOKEN"
ExecStart=$INSTALL_DIR/backend/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 parser_app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    print_success "XML parser service created"
    
    # Frontend service
    if [ "$INSTALL_MODE" = "prod" ]; then
        print_info "Creating frontend service..."
        sudo tee /etc/systemd/system/solarapp-frontend.service > /dev/null << EOF
[Unit]
Description=SolarApp Frontend
After=network.target solarapp-backend.service

[Service]
Type=simple
User=solarapp
Group=solarapp
WorkingDirectory=$INSTALL_DIR/frontend
ExecStart=/usr/bin/serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        print_success "Frontend service created"
    fi
    
    # Reload systemd
    print_info "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    # Enable and start services
    print_info "Enabling and starting services..."
    sudo systemctl enable solarapp-backend
    sudo systemctl enable solarapp-xml-parser
    sudo systemctl start solarapp-backend
    sudo systemctl start solarapp-xml-parser
    
    if [ "$INSTALL_MODE" = "prod" ]; then
        sudo systemctl enable solarapp-frontend
        sudo systemctl start solarapp-frontend
    fi
    
    print_success "Services started"
    
    # Check status
    sleep 2
    if sudo systemctl is-active --quiet solarapp-backend; then
        print_success "Backend service is running"
    else
        print_warning "Backend service failed to start. Check logs with: sudo journalctl -u solarapp-backend -n 50"
    fi
    
    if sudo systemctl is-active --quiet solarapp-xml-parser; then
        print_success "XML parser service is running"
    else
        print_warning "XML parser service failed to start. Check logs with: sudo journalctl -u solarapp-xml-parser -n 50"
    fi
fi

# Print completion message
print_header "Installation Complete!"

echo ""
print_success "SolarApp has been successfully installed!"
echo ""
print_info "Installation directory: $INSTALL_DIR"
print_info "XML Parser Token: $XML_PARSER_TOKEN"
echo ""

if [ "$INSTALL_SERVICES" = "yes" ]; then
    print_info "Services have been installed and started"
    echo ""
    print_info "Backend API: http://localhost:8000"
    print_info "API Documentation: http://localhost:8000/docs"
    if [ "$INSTALL_MODE" = "prod" ]; then
        print_info "Frontend: http://localhost:3000"
    fi
    echo ""
    print_info "Manage services with:"
    echo "  sudo systemctl start/stop/restart solarapp-backend"
    echo "  sudo systemctl start/stop/restart solarapp-xml-parser"
    if [ "$INSTALL_MODE" = "prod" ]; then
        echo "  sudo systemctl start/stop/restart solarapp-frontend"
    fi
    echo ""
    print_info "View logs with:"
    echo "  sudo journalctl -u solarapp-backend -f"
    echo "  sudo journalctl -u solarapp-xml-parser -f"
else
    print_info "To run manually:"
    echo ""
    echo "  Backend:"
    echo "    cd $INSTALL_DIR/backend"
    echo "    ./run.sh"
    echo ""
    echo "  Frontend:"
    echo "    cd $INSTALL_DIR/frontend"
    if [ "$INSTALL_MODE" = "dev" ]; then
        echo "    npm run dev"
    else
        echo "    serve -s dist -l 3000"
    fi
fi

echo ""
print_success "Happy solar panel managing! ☀️"
echo ""
