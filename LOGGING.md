# SolarApp Logging Guide

This guide provides commands for viewing and collecting logs from SolarApp for troubleshooting purposes.

## 📋 Table of Contents

- [Systemd Service Logs](#systemd-service-logs)
- [Docker Logs](#docker-logs)
- [Application Logs](#application-logs)
- [Common Scenarios](#common-scenarios)
- [Sending Logs for Support](#sending-logs-for-support)

## 🔍 Systemd Service Logs

If you installed SolarApp using the install script with systemd services, use these commands:

### View Real-Time Logs (Follow Mode)

```bash
# Backend API logs (live)
journalctl -u solarapp-backend -f

# XML Parser service logs (live)
journalctl -u solarapp-xml-parser -f

# Both services together
journalctl -u solarapp-backend -u solarapp-xml-parser -f
```

### View Recent Logs

```bash
# Last 100 lines from backend
journalctl -u solarapp-backend -n 100

# Last 100 lines from XML parser
journalctl -u solarapp-xml-parser -n 100

# Last 50 lines from both services
journalctl -u solarapp-backend -u solarapp-xml-parser -n 50
```

### View Logs from Specific Time Period

```bash
# Logs from the last hour
journalctl -u solarapp-backend --since "1 hour ago"

# Logs from today
journalctl -u solarapp-backend --since today

# Logs from specific date
journalctl -u solarapp-backend --since "2026-02-07"

# Logs between two dates
journalctl -u solarapp-backend --since "2026-02-07 00:00:00" --until "2026-02-07 23:59:59"
```

### Filter by Log Level

```bash
# Show only errors
journalctl -u solarapp-backend -p err

# Show errors and warnings
journalctl -u solarapp-backend -p warning

# Priority levels: emerg, alert, crit, err, warning, notice, info, debug
```

### Save Logs to File

```bash
# Save backend logs to file
journalctl -u solarapp-backend > backend-logs.txt

# Save last 1000 lines
journalctl -u solarapp-backend -n 1000 > backend-logs.txt

# Save logs from specific time period
journalctl -u solarapp-backend --since "1 hour ago" > backend-logs-last-hour.txt

# Save both services
journalctl -u solarapp-backend -u solarapp-xml-parser > all-logs.txt

# Save with timestamps in verbose format
journalctl -u solarapp-backend -o verbose > backend-logs-verbose.txt
```

### Search in Logs

```bash
# Search for specific text
journalctl -u solarapp-backend | grep "error"

# Case-insensitive search
journalctl -u solarapp-backend | grep -i "error"

# Search for multiple terms
journalctl -u solarapp-backend | grep -E "error|warning|failed"
```

## 🐳 Docker Logs

If you're running SolarApp with Docker Compose:

### View Real-Time Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f xml-parser

# Multiple specific services
docker-compose logs -f backend xml-parser
```

### View Recent Logs

```bash
# Last 100 lines from all services
docker-compose logs --tail=100

# Last 100 lines from backend
docker-compose logs --tail=100 backend

# All logs from a service
docker-compose logs backend
```

### View Logs with Timestamps

```bash
# Include timestamps
docker-compose logs -f --timestamps

# Specific service with timestamps
docker-compose logs -f --timestamps backend
```

### Save Docker Logs to File

```bash
# Save all services logs
docker-compose logs > docker-logs.txt

# Save specific service
docker-compose logs backend > backend-docker-logs.txt

# Save last 500 lines
docker-compose logs --tail=500 > docker-logs-recent.txt
```

## 📝 Application Logs

### Direct Backend Logs

If running the backend directly (not as a service):

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Run with debug logging
uvicorn app.main:app --reload --log-level debug
```

### Frontend Development Logs

```bash
# Navigate to frontend directory
cd frontend

# Run development server (logs to console)
npm run dev

# Build with verbose output
npm run build -- --mode development
```

### XML Parser Logs

```bash
# Navigate to XML parser directory
cd backend/services/xml_parser

# Activate virtual environment
source .venv/bin/activate

# Run with debug output
python parser_app.py
```

## 🎯 Common Scenarios

### Scenario 1: Service Won't Start

```bash
# Check service status
systemctl status solarapp-backend
systemctl status solarapp-xml-parser

# View recent error logs
journalctl -u solarapp-backend -n 50 -p err

# Check if port is already in use
lsof -i :8000
lsof -i :5000
```

### Scenario 2: Application Errors

```bash
# View last hour of logs with errors
journalctl -u solarapp-backend --since "1 hour ago" -p err

# Follow logs and filter for errors
journalctl -u solarapp-backend -f | grep -i error

# Check for Python exceptions
journalctl -u solarapp-backend | grep -i traceback -A 20
```

### Scenario 3: Performance Issues

```bash
# View logs with timing information
journalctl -u solarapp-backend -o verbose --since "1 hour ago"

# Monitor resource usage
systemctl status solarapp-backend
systemctl status solarapp-xml-parser

# Check memory and CPU limits (Raspberry Pi)
systemctl show solarapp-backend | grep -i memory
systemctl show solarapp-backend | grep -i cpu
```

### Scenario 4: Database Issues

```bash
# Look for database-related errors
journalctl -u solarapp-backend | grep -i "database\|sqlite\|connection"

# Check database file permissions
ls -la backend/data/solarapp.db

# View backend logs during database operations
journalctl -u solarapp-backend --since "10 minutes ago" | grep -i "sqlmodel\|database"
```

### Scenario 5: API Request Debugging

```bash
# View logs with HTTP request details
journalctl -u solarapp-backend -f | grep -E "POST|GET|PUT|DELETE"

# View logs for specific endpoint
journalctl -u solarapp-backend -f | grep "/api/v1/materials"

# Check for 4xx and 5xx errors
journalctl -u solarapp-backend | grep -E " (4[0-9]{2}|5[0-9]{2}) "
```

## 📤 Sending Logs for Support

When requesting support, collect logs using these commands:

### Complete Log Package

```bash
# Create a logs directory
mkdir solarapp-logs
cd solarapp-logs

# Collect service status
systemctl status solarapp-backend > service-status-backend.txt
systemctl status solarapp-xml-parser > service-status-xml-parser.txt

# Collect recent logs (last 1000 lines)
journalctl -u solarapp-backend -n 1000 > backend-logs.txt
journalctl -u solarapp-xml-parser -n 1000 > xml-parser-logs.txt

# Collect logs from last 24 hours
journalctl -u solarapp-backend --since "24 hours ago" > backend-logs-24h.txt
journalctl -u solarapp-xml-parser --since "24 hours ago" > xml-parser-logs-24h.txt

# System information
uname -a > system-info.txt
python3 --version >> system-info.txt
node --version >> system-info.txt 2>&1 || echo "Node.js not installed" >> system-info.txt

# Create archive
cd ..
tar -czf solarapp-logs.tar.gz solarapp-logs/
echo "Logs package created: solarapp-logs.tar.gz"
```

### Quick Error Log Collection

```bash
# Collect only errors from last hour
journalctl -u solarapp-backend --since "1 hour ago" -p err > backend-errors.txt
journalctl -u solarapp-xml-parser --since "1 hour ago" -p err > xml-parser-errors.txt

# Display the content
cat backend-errors.txt
cat xml-parser-errors.txt
```

### Docker Logs Package

```bash
# Create logs directory
mkdir docker-logs
cd docker-logs

# Collect Docker logs
docker-compose logs > all-services.txt
docker-compose logs backend > backend.txt
docker-compose logs frontend > frontend.txt
docker-compose logs xml-parser > xml-parser.txt

# Docker system info
docker-compose ps > containers-status.txt
docker --version > docker-info.txt
docker-compose --version >> docker-info.txt

# Create archive
cd ..
tar -czf docker-logs.tar.gz docker-logs/
echo "Docker logs package created: docker-logs.tar.gz"
```

## 🔧 Advanced Commands

### Monitor Logs in Real-Time with Filtering

```bash
# Show only INFO level and above
journalctl -u solarapp-backend -f -p info

# Highlight specific terms
journalctl -u solarapp-backend -f | grep --color=always -E "ERROR|WARNING|$"

# Monitor multiple patterns
journalctl -u solarapp-backend -f | grep -E "api/v1/|ERROR|WARNING"
```

### Log Rotation Information

```bash
# Check journal disk usage
journalctl --disk-usage

# Vacuum old logs (keep only 100MB)
sudo journalctl --vacuum-size=100M

# Vacuum logs older than 2 weeks
sudo journalctl --vacuum-time=2weeks
```

### Export Logs in Different Formats

```bash
# JSON format (useful for parsing)
journalctl -u solarapp-backend -n 100 -o json > logs.json

# JSON Pretty format
journalctl -u solarapp-backend -n 100 -o json-pretty > logs-pretty.json

# Short format (one line per log)
journalctl -u solarapp-backend -n 100 -o short > logs-short.txt

# Export format (suitable for import elsewhere)
journalctl -u solarapp-backend -n 100 -o export > logs.export
```

## 📚 Additional Resources

- [systemd journal documentation](https://www.freedesktop.org/software/systemd/man/journalctl.html)
- [Docker logs documentation](https://docs.docker.com/engine/reference/commandline/logs/)
- [FastAPI logging](https://fastapi.tiangolo.com/tutorial/debugging/)

## 💡 Tips

1. **Use `-f` flag** for real-time log monitoring during debugging
2. **Combine with grep** to filter for specific issues
3. **Save logs before restarting services** to preserve debugging information
4. **Use time filters** to focus on relevant time periods
5. **Include system info** when reporting issues
6. **Check both backend and XML parser logs** - issues may span services
7. **For Raspberry Pi**: Logs are limited by MemoryLimit settings in service files

## 🆘 Quick Reference

| Task | Command |
|------|---------|
| View live backend logs | `journalctl -u solarapp-backend -f` |
| View last 100 lines | `journalctl -u solarapp-backend -n 100` |
| View errors only | `journalctl -u solarapp-backend -p err` |
| View logs from last hour | `journalctl -u solarapp-backend --since "1 hour ago"` |
| Save logs to file | `journalctl -u solarapp-backend > logs.txt` |
| Search in logs | `journalctl -u solarapp-backend | grep "error"` |
| View service status | `systemctl status solarapp-backend` |
| Docker live logs | `docker-compose logs -f` |
| Docker last 100 lines | `docker-compose logs --tail=100` |
