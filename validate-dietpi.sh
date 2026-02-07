#!/bin/bash

# Validation script for Diet Pi installation
# This script checks that all components are properly configured

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "=========================================="
echo "SolarApp Diet Pi Installation Validator"
echo "=========================================="
echo

# Test 1: Check if we're in the right directory
print_info "Checking installation directory..."
if [ -d "backend" ] && [ -d "frontend" ] && [ -f "README.md" ]; then
    print_pass "Running from SolarApp root directory"
else
    print_fail "Not running from SolarApp root directory"
    echo "Please run this script from the SolarApp root directory"
    exit 1
fi

# Test 2: Check Python installation
print_info "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_pass "Python installed: $PYTHON_VERSION"
else
    print_fail "Python 3 not found"
fi

# Test 3: Check backend virtual environment
print_info "Checking backend virtual environment..."
if [ -d "backend/.venv" ]; then
    print_pass "Backend virtual environment exists"
else
    print_fail "Backend virtual environment not found"
fi

# Test 4: Check XML parser virtual environment
print_info "Checking XML parser virtual environment..."
if [ -d "backend/services/xml_parser/.venv" ]; then
    print_pass "XML parser virtual environment exists"
else
    print_fail "XML parser virtual environment not found"
fi

# Test 5: Check nginx installation
print_info "Checking nginx..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1 | awk '{print $3}')
    print_pass "nginx installed: $NGINX_VERSION"
else
    print_fail "nginx not found"
fi

# Test 6: Check nginx configuration syntax
print_info "Checking nginx configuration..."
if command -v nginx &> /dev/null; then
    if sudo nginx -t &> /dev/null; then
        print_pass "nginx configuration is valid"
    else
        print_fail "nginx configuration has errors"
        sudo nginx -t
    fi
fi

# Test 7: Check if nginx site is configured
print_info "Checking SolarApp nginx site..."
if [ -f "/etc/nginx/sites-available/solarapp" ]; then
    print_pass "SolarApp nginx site configuration exists"
else
    print_fail "SolarApp nginx site configuration not found"
fi

if [ -L "/etc/nginx/sites-enabled/solarapp" ]; then
    print_pass "SolarApp nginx site is enabled"
else
    print_fail "SolarApp nginx site is not enabled"
fi

# Test 8: Check systemd services
print_info "Checking systemd services..."

if [ -f "/etc/systemd/system/solarapp-backend.service" ] || [ -f "/etc/systemd/system/solarapp-backend-rpi.service" ]; then
    print_pass "Backend service file exists"
else
    print_fail "Backend service file not found"
fi

if [ -f "/etc/systemd/system/solarapp-xml-parser.service" ] || [ -f "/etc/systemd/system/solarapp-xml-parser-rpi.service" ]; then
    print_pass "XML parser service file exists"
else
    print_fail "XML parser service file not found"
fi

# Test 9: Check if services are running (if systemd is available)
if command -v systemctl &> /dev/null; then
    print_info "Checking service status..."
    
    # Check backend service
    if systemctl is-active --quiet solarapp-backend.service 2>/dev/null; then
        print_pass "Backend service is running"
    elif systemctl is-active --quiet solarapp-backend-rpi.service 2>/dev/null; then
        print_pass "Backend service (rpi) is running"
    else
        print_fail "Backend service is not running"
    fi
    
    # Check XML parser service
    if systemctl is-active --quiet solarapp-xml-parser.service 2>/dev/null; then
        print_pass "XML parser service is running"
    elif systemctl is-active --quiet solarapp-xml-parser-rpi.service 2>/dev/null; then
        print_pass "XML parser service (rpi) is running"
    else
        print_fail "XML parser service is not running"
    fi
    
    # Check nginx service
    if systemctl is-active --quiet nginx.service 2>/dev/null; then
        print_pass "nginx service is running"
    else
        print_fail "nginx service is not running"
    fi
fi

# Test 10: Check if frontend is built
print_info "Checking frontend build..."
if [ -d "frontend/dist" ] && [ -f "frontend/dist/index.html" ]; then
    print_pass "Frontend is built (dist folder exists)"
else
    print_fail "Frontend is not built (dist folder missing)"
fi

# Test 11: Check if ports are listening
print_info "Checking if services are listening on ports..."

if command -v netstat &> /dev/null || command -v ss &> /dev/null; then
    # Check port 80 (nginx)
    if sudo netstat -tlnp 2>/dev/null | grep -q ":80 " || sudo ss -tlnp 2>/dev/null | grep -q ":80 "; then
        print_pass "Port 80 is listening (nginx)"
    else
        print_fail "Port 80 is not listening"
    fi
    
    # Check port 8000 (backend)
    if sudo netstat -tlnp 2>/dev/null | grep -q ":8000 " || sudo ss -tlnp 2>/dev/null | grep -q ":8000 "; then
        print_pass "Port 8000 is listening (backend)"
    else
        print_fail "Port 8000 is not listening"
    fi
    
    # Check port 5000 (XML parser)
    if sudo netstat -tlnp 2>/dev/null | grep -q ":5000 " || sudo ss -tlnp 2>/dev/null | grep -q ":5000 "; then
        print_pass "Port 5000 is listening (XML parser)"
    else
        print_fail "Port 5000 is not listening"
    fi
else
    print_info "netstat/ss not available, skipping port checks"
fi

# Test 12: Check database
print_info "Checking database..."
if [ -f "backend/data/solarapp.db" ]; then
    print_pass "Database file exists"
else
    print_fail "Database file not found (will be created on first run)"
fi

# Test 13: Check .env file
print_info "Checking configuration..."
if [ -f "backend/.env" ]; then
    print_pass "Backend .env file exists"
else
    print_fail "Backend .env file not found"
fi

# Test 14: Check if frontend/dist is accessible by nginx
print_info "Checking frontend permissions..."
if [ -d "frontend/dist" ]; then
    DIST_PERMS=$(stat -c "%a" frontend/dist 2>/dev/null || stat -f "%A" frontend/dist 2>/dev/null)
    if [ -n "$DIST_PERMS" ]; then
        print_pass "Frontend dist folder is readable (permissions: $DIST_PERMS)"
    else
        print_info "Could not check permissions"
    fi
fi

echo
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo
    echo "Your SolarApp installation appears to be configured correctly."
    echo
    echo "Access your application:"
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    echo "  Frontend:  http://$IP_ADDRESS/"
    echo "  API Docs:  http://$IP_ADDRESS/docs"
    echo
    exit 0
else
    echo -e "${RED}✗ Some checks failed.${NC}"
    echo
    echo "Please review the failed checks above and:"
    echo "  1. Make sure you ran the installation script: sudo ./dietpi-install.sh"
    echo "  2. Check service logs: sudo journalctl -u solarapp-backend -n 50"
    echo "  3. Verify nginx config: sudo nginx -t"
    echo "  4. See DIETPI.md for troubleshooting"
    echo
    exit 1
fi
