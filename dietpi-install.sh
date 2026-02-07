#!/bin/bash

# SolarApp Diet Pi Installation Script
# Automated installation for Raspberry Pi running Diet Pi OS
# Installs backend, XML parser, and configures nginx for frontend

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
    print_warning "This script is optimized for Diet Pi"
    print_warning "Continuing installation on standard Raspberry Pi OS..."
fi

# Detect installation directory
INSTALL_DIR=$(cd "$(dirname "$0")" && pwd)
print_info "Installation directory: $INSTALL_DIR"

# Detect current user
CURRENT_USER=${SUDO_USER:-$(whoami)}
print_info "Installing for user: $CURRENT_USER"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run with sudo"
    echo "Usage: sudo ./dietpi-install.sh"
    exit 1
fi

echo
print_info "=========================================="
print_info "SolarApp Diet Pi Installation"
print_info "=========================================="
echo

# Step 1: Check prerequisites
print_info "Step 1: Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_warning "Python 3 not found. Installing..."
    if [ "$IS_DIETPI" = true ]; then
        dietpi-software install 130  # Python 3
    else
        apt update
        apt install -y python3 python3-pip python3-venv
    fi
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_info "Python $PYTHON_VERSION installed"

# Check nginx
if ! command -v nginx &> /dev/null; then
    print_warning "nginx not found. Installing..."
    if [ "$IS_DIETPI" = true ]; then
        dietpi-software install 85  # nginx
    else
        apt update
        apt install -y nginx
    fi
fi

NGINX_VERSION=$(nginx -v 2>&1 | awk '{print $3}')
print_info "nginx $NGINX_VERSION installed"

# Check Git
if ! command -v git &> /dev/null; then
    print_warning "Git not found. Installing..."
    if [ "$IS_DIETPI" = true ]; then
        dietpi-software install 17  # Git
    else
        apt update
        apt install -y git
    fi
fi

echo
print_info "Step 2: Running backend installation..."
cd "$INSTALL_DIR"

# Create backend virtual environment
if [ ! -d "backend/.venv" ]; then
    print_info "Creating Python virtual environment for backend..."
    cd backend
    python3 -m venv .venv
    cd ..
fi

# Install backend dependencies
print_info "Installing backend dependencies..."
cd backend
source .venv/bin/activate || { print_error "Failed to activate backend virtual environment"; exit 1; }
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
deactivate
cd ..

# Setup .env file
if [ ! -f "backend/.env" ]; then
    print_info "Creating .env file from template..."
    cp backend/.env.example backend/.env
    # Update database path for absolute path
    sed -i "s|sqlite:///./data/solarapp.db|sqlite:///$INSTALL_DIR/backend/data/solarapp.db|g" backend/.env
fi

echo
print_info "Step 3: Setting up XML Parser service..."

# Create XML parser virtual environment
if [ ! -d "backend/services/xml_parser/.venv" ]; then
    print_info "Creating Python virtual environment for XML parser..."
    cd backend/services/xml_parser
    python3 -m venv .venv
    cd ../../..
fi

# Install XML parser dependencies
print_info "Installing XML parser dependencies..."
cd backend/services/xml_parser
source .venv/bin/activate || { print_error "Failed to activate XML parser virtual environment"; exit 1; }
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
deactivate
cd ../../..

echo
print_info "Step 4: Setting up frontend..."

# Check if Node.js is available
if command -v npm &> /dev/null; then
    print_info "Node.js found. Building frontend..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install --silent
    fi
    
    print_info "Building frontend for production..."
    npm run build
    cd ..
    
    FRONTEND_BUILT=true
else
    print_warning "Node.js not found. Frontend will need to be built separately."
    print_info "To build frontend: install Node.js 18+, then run 'cd frontend && npm install && npm run build'"
    FRONTEND_BUILT=false
fi

echo
print_info "Step 5: Configuring nginx..."

# Create nginx site configuration
NGINX_SITE_CONF="/etc/nginx/sites-available/solarapp"

print_info "Creating nginx configuration at $NGINX_SITE_CONF..."

cat > "$NGINX_SITE_CONF" <<EOF
# SolarApp Frontend - Optimized for Diet Pi / Raspberry Pi
server {
    listen 80;
    server_name _;
    
    root $INSTALL_DIR/frontend/dist;
    index index.html;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Main location - serve React app
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API documentation endpoints
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }
}
EOF

# Enable the site
print_info "Enabling SolarApp nginx site..."
ln -sf "$NGINX_SITE_CONF" /etc/nginx/sites-enabled/solarapp

# Remove default site
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    print_info "Removing default nginx site..."
    rm -f /etc/nginx/sites-enabled/default
fi

# Optimize nginx configuration for Raspberry Pi
NGINX_CONF="/etc/nginx/nginx.conf"
if grep -q "worker_processes auto;" "$NGINX_CONF"; then
    print_info "Optimizing nginx worker processes for Raspberry Pi..."
    sed -i 's/worker_processes auto;/worker_processes 1;/g' "$NGINX_CONF"
fi

# Enable gzip in nginx if not already enabled
if ! grep -q "gzip on;" "$NGINX_CONF"; then
    print_info "Enabling gzip compression in nginx..."
    sed -i '/http {/a \    gzip on;\n    gzip_vary on;\n    gzip_min_length 1024;\n    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;' "$NGINX_CONF"
fi

# Test nginx configuration
print_info "Testing nginx configuration..."
if nginx -t 2>&1 | grep -q "successful"; then
    print_info "nginx configuration is valid"
else
    print_error "nginx configuration test failed"
    nginx -t
    exit 1
fi

echo
print_info "Step 6: Creating systemd services..."

# Create backend service
BACKEND_SERVICE="/etc/systemd/system/solarapp-backend.service"
print_info "Creating backend service at $BACKEND_SERVICE..."

cat > "$BACKEND_SERVICE" <<EOF
[Unit]
Description=SolarApp Backend API
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/.venv/bin"
# Optimized for Raspberry Pi with single worker
ExecStart=$INSTALL_DIR/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 50 --timeout-keep-alive 5
Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=solarapp-backend

[Install]
WantedBy=multi-user.target
EOF

# Create XML parser service
XML_PARSER_SERVICE="/etc/systemd/system/solarapp-xml-parser.service"
print_info "Creating XML parser service at $XML_PARSER_SERVICE..."

cat > "$XML_PARSER_SERVICE" <<EOF
[Unit]
Description=SolarApp XML Parser Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR/backend/services/xml_parser
Environment="PATH=$INSTALL_DIR/backend/services/xml_parser/.venv/bin"
ExecStart=$INSTALL_DIR/backend/services/xml_parser/.venv/bin/python parser_app.py
Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=solarapp-xml-parser

[Install]
WantedBy=multi-user.target
EOF

# Set proper ownership
chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"

echo
print_info "Step 7: Enabling and starting services..."

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable solarapp-backend.service
systemctl enable solarapp-xml-parser.service
systemctl enable nginx.service

# Start services
print_info "Starting backend service..."
systemctl start solarapp-backend.service

print_info "Starting XML parser service..."
systemctl start solarapp-xml-parser.service

print_info "Restarting nginx..."
systemctl restart nginx.service

# Wait a moment for services to start
sleep 3

echo
print_info "Step 8: Checking service status..."

# Check service status
BACKEND_STATUS=$(systemctl is-active solarapp-backend.service)
XML_PARSER_STATUS=$(systemctl is-active solarapp-xml-parser.service)
NGINX_STATUS=$(systemctl is-active nginx.service)

if [ "$BACKEND_STATUS" = "active" ]; then
    print_info "✓ Backend service is running"
else
    print_error "✗ Backend service failed to start"
    systemctl status solarapp-backend.service --no-pager -l
fi

if [ "$XML_PARSER_STATUS" = "active" ]; then
    print_info "✓ XML Parser service is running"
else
    print_error "✗ XML Parser service failed to start"
    systemctl status solarapp-xml-parser.service --no-pager -l
fi

if [ "$NGINX_STATUS" = "active" ]; then
    print_info "✓ nginx service is running"
else
    print_error "✗ nginx service failed to start"
    systemctl status nginx.service --no-pager -l
fi

echo
print_info "=========================================="
print_info "Installation Complete!"
print_info "=========================================="
echo

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

print_info "SolarApp is now running!"
echo
echo "Access the application:"
echo "  Frontend:  http://$IP_ADDRESS/"
echo "  API Docs:  http://$IP_ADDRESS/docs"
echo "  Backend:   http://$IP_ADDRESS/api"
echo

print_info "Service Management:"
echo "  Check status:  sudo systemctl status solarapp-backend"
echo "  View logs:     sudo journalctl -u solarapp-backend -f"
echo "  Restart:       sudo systemctl restart solarapp-backend"
echo "  Stop:          sudo systemctl stop solarapp-backend"
echo

if [ "$FRONTEND_BUILT" = false ]; then
    print_warning "Frontend was not built (Node.js not available)"
    print_info "To build frontend later:"
    echo "  1. Install Node.js 18+ and npm"
    echo "  2. cd $INSTALL_DIR/frontend"
    echo "  3. npm install && npm run build"
    echo "  4. sudo systemctl restart nginx"
    echo
fi

# Offer to load sample data (only if running interactively)
if [ -t 0 ]; then
    read -t 30 -p "Would you like to load sample data for testing? (y/N): " load_sample || load_sample="n"
    if [[ $load_sample =~ ^[Yy]$ ]]; then
        print_info "Loading sample data..."
        cd "$INSTALL_DIR/backend"
        source .venv/bin/activate
        python sample_data.py
        deactivate
        print_info "Sample data loaded successfully"
    fi
else
    print_info "Running non-interactively, skipping sample data prompt"
fi

echo
print_info "Diet Pi optimization tips:"
echo "  - Monitor resources: htop or dietpi-services"
echo "  - View Diet Pi logs: sudo dietpi-services logs"
echo "  - Configure Diet Pi: sudo dietpi-config"
echo "  - See DIETPI.md for complete optimization guide"
echo

if [ "$IS_DIETPI" = true ]; then
    print_note "=========================================="
    print_note "Diet Pi Resource Optimization Applied"
    print_note "=========================================="
    echo
    print_info "Estimated resource usage:"
    echo "  - nginx:      ~10-20MB RAM"
    echo "  - Backend:    ~80-150MB RAM"
    echo "  - XML Parser: ~40-80MB RAM"
    echo "  - Total:      ~130-250MB RAM"
    echo
    print_info "This leaves plenty of RAM available for other services on your Raspberry Pi!"
fi

echo
print_info "For more information, see:"
echo "  - DIETPI.md - Complete Diet Pi guide"
echo "  - RASPBERRY_PI.md - Raspberry Pi optimization guide"
echo "  - README.md - General documentation"
echo

print_info "Installation script completed successfully! 🎉"
