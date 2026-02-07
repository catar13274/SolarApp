# Systemd Service Files

This directory contains systemd service files for SolarApp. Choose the appropriate file based on your installation location.

## Available Service Files

### For Raspberry Pi Installation at `/home/pi/SolarApp`
- `solarapp-backend-rpi.service` - Backend API service
- `solarapp-xml-parser-rpi.service` - XML Parser service

**Installation:**
```bash
sudo cp systemd/solarapp-backend-rpi.service /etc/systemd/system/
sudo cp systemd/solarapp-xml-parser-rpi.service /etc/systemd/system/

# Edit to customize if needed
sudo nano /etc/systemd/system/solarapp-backend-rpi.service
sudo nano /etc/systemd/system/solarapp-xml-parser-rpi.service

sudo systemctl daemon-reload
sudo systemctl enable --now solarapp-backend-rpi solarapp-xml-parser-rpi
```

### For Installation at `/opt/SolarApp`
- `solarapp-backend-opt.service` - Backend API service
- `solarapp-xml-parser-opt.service` - XML Parser service

**Installation:**
```bash
sudo cp systemd/solarapp-backend-opt.service /etc/systemd/system/
sudo cp systemd/solarapp-xml-parser-opt.service /etc/systemd/system/

# IMPORTANT: Update the User field to your actual username
sudo sed -i 's/your-username/YOUR_ACTUAL_USERNAME/g' /etc/systemd/system/solarapp-backend-opt.service
sudo sed -i 's/your-username/YOUR_ACTUAL_USERNAME/g' /etc/systemd/system/solarapp-xml-parser-opt.service

sudo systemctl daemon-reload
sudo systemctl enable --now solarapp-backend-opt solarapp-xml-parser-opt
```

## Customizing for Other Installation Paths

If you installed SolarApp in a different location (e.g., `/usr/local/SolarApp`, `/home/username/custom-path`):

1. Copy one of the template files:
   ```bash
   cp systemd/solarapp-backend-rpi.service my-backend.service
   cp systemd/solarapp-xml-parser-rpi.service my-parser.service
   ```

2. Edit the files and update all paths:
   - `User=` - Your username
   - `WorkingDirectory=` - Your installation path
   - `Environment="PATH=..."` - Your installation path
   - `Environment="SOLARAPP_DB_URL=..."` - Your installation path (backend service only)
   - `ExecStart=` - Your installation path

3. Install the customized files:
   ```bash
   sudo cp my-backend.service /etc/systemd/system/solarapp-backend.service
   sudo cp my-parser.service /etc/systemd/system/solarapp-xml-parser.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now solarapp-backend solarapp-xml-parser
   ```

## Checking Service Status

```bash
# Check status
systemctl status solarapp-backend-rpi  # or solarapp-backend-opt
systemctl status solarapp-xml-parser-rpi  # or solarapp-xml-parser-opt

# View logs
journalctl -u solarapp-backend-rpi -f
journalctl -u solarapp-xml-parser-rpi -f

# Restart services
sudo systemctl restart solarapp-backend-rpi
sudo systemctl restart solarapp-xml-parser-rpi
```

## Troubleshooting

### Error: "No such file or directory" when starting service

This error occurs when the paths in the service file don't match your actual installation location.

**Solution:**
1. Check where SolarApp is actually installed:
   ```bash
   which uvicorn  # Should show something like /path/to/SolarApp/backend/.venv/bin/uvicorn
   ```

2. Edit the service file and update all paths to match your installation:
   ```bash
   sudo nano /etc/systemd/system/solarapp-backend-rpi.service
   ```

3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart solarapp-backend-rpi
   ```

### Common Installation Paths
- **Raspberry Pi (default):** `/home/pi/SolarApp`
- **System-wide installation:** `/opt/SolarApp`
- **User installation:** `/home/username/SolarApp`
- **Development:** `/home/username/dev/SolarApp`

Always update the service file paths to match your actual installation location!
