# SolarApp

**SolarApp** is a comprehensive Solar Panel Management System designed to streamline the management of solar panel installations, inventory, and projects. Built with a modern tech stack, it provides an intuitive interface for tracking materials, managing stock levels, coordinating projects, and processing invoices.

**🎯 Optimized for Raspberry Pi!** See [RASPBERRY_PI.md](RASPBERRY_PI.md) for detailed Raspberry Pi installation and optimization guide.

## 🌟 Features

- **Dashboard**: Real-time overview of system statistics, including total materials, low stock alerts, and active projects
- **Materials Management**: Track solar panels, inverters, batteries, cables, mounting equipment, and other components with SKU-based inventory
- **Stock Management**: Monitor current inventory levels, track stock movements (in/out/adjustments), and manage multiple warehouse locations
- **Project Management**: Organize solar installation projects with client information, capacity tracking, cost estimation, and material allocation
- **Invoice Processing**: Upload and parse XML invoices (ANAF e-factura format) with automatic material matching and purchase record creation
- **Low Stock Alerts**: Automatic notifications when materials fall below minimum stock levels
- **Comprehensive API**: RESTful API with FastAPI for easy integration with other systems

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLModel**: SQL databases using Python type hints (based on Pydantic and SQLAlchemy)
- **Uvicorn**: Lightning-fast ASGI server
- **Python 3.9+**: Latest Python features and performance improvements
- **SQLite**: Lightweight, file-based database (easily upgradable to PostgreSQL)

### Frontend
- **React 18**: Modern React with hooks and concurrent features
- **Vite**: Next-generation frontend tooling for fast development
- **TailwindCSS**: Utility-first CSS framework for rapid UI development
- **React Router**: Declarative routing for React applications
- **Axios**: Promise-based HTTP client
- **React Query**: Powerful data synchronization and caching
- **React Hook Form**: Performant, flexible forms with validation
- **Lucide React**: Beautiful, consistent icon set

### Services
- **XML Parser Service**: Dedicated microservice for parsing ANAF e-factura XML invoices
- **DefusedXML**: Secure XML parsing to prevent XML vulnerabilities

## 📋 Prerequisites

Before installing SolarApp, ensure you have the following installed:

### Required:
- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip3** - Usually comes with Python

### Optional (for frontend):
- **Node.js 18 or higher** - [Download Node.js](https://nodejs.org/)
- **npm** - Usually comes with Node.js

### Optional (for development):
- **git** - [Download Git](https://git-scm.com/downloads/)

**Note:** The installation script will install the backend and XML parser service even if Node.js/npm are not available. The frontend can be installed later by installing Node.js 18+ and npm, then running `cd frontend && npm install && npm run build`.

## 🚀 Installation

### Quick Installation (Recommended)

SolarApp includes an automated installation script that handles all setup steps:

```bash
# Clone the repository (if you have git)
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Run the installation script
chmod +x install.sh
./install.sh

# For systemd service installation (requires sudo)
sudo ./install.sh
```

The installation script will:
1. ✅ Check all prerequisites and their versions
2. ✅ Set up Python virtual environment for the backend
3. ✅ Install backend dependencies
4. ✅ Set up the XML parser service
5. ✅ Install frontend dependencies and build the application (if Node.js/npm are available)
6. ✅ Create and configure systemd services (when run with sudo)
7. ✅ Optionally load sample data for testing

**Note:** If Node.js and npm are not installed, the script will skip frontend installation and continue with backend setup. The frontend can be installed later once Node.js and npm are available.

For detailed installation testing and troubleshooting, see [INSTALL_TEST.md](INSTALL_TEST.md).

### Manual Installation

If you prefer to install manually:

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the backend
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`.

#### 2. XML Parser Service Setup

```bash
cd backend/services/xml_parser

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Run the service
python3 app.py
```

The XML parser service will be available at `http://localhost:5000`.

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Or build for production
npm run build
```

The frontend will be available at `http://localhost:5173` (development) or `http://localhost:3000` (production).

### Docker Installation

For containerized deployment:

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- XML Parser: `http://localhost:5000`

### Raspberry Pi Installation

**🎯 Optimized for resource-constrained devices!**

SolarApp has been specially optimized for Raspberry Pi with reduced memory footprint, optimized database configuration, and ARM-specific optimizations.

```bash
# Use the Raspberry Pi optimized Docker Compose
docker-compose -f docker-compose.rpi.yml up -d

# Or install natively for best performance
sudo ./install.sh
sudo cp systemd/solarapp-backend-rpi.service /etc/systemd/system/
sudo cp systemd/solarapp-xml-parser-rpi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now solarapp-backend-rpi solarapp-xml-parser-rpi
```

**📘 For complete Raspberry Pi guide, see [RASPBERRY_PI.md](RASPBERRY_PI.md)**

**Resource usage on Raspberry Pi:**
- Docker mode: ~300-500MB total RAM
- Native mode: ~150-250MB total RAM
- Backend-only: ~60-120MB RAM

**Supports:**
- Raspberry Pi 4 (2GB+) - Full features
- Raspberry Pi 3 B+ (1GB) - Full features  
- Raspberry Pi Zero 2 W (512MB) - Backend only

### Diet Pi Installation (Recommended for Raspberry Pi)

**🚀 Ultra-lightweight installation with nginx frontend!**

Diet Pi is a minimal Debian-based OS that provides the best performance on Raspberry Pi. SolarApp includes a specialized installer for Diet Pi with native nginx configuration.

```bash
# Clone the repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Run the Diet Pi installer (includes nginx setup)
chmod +x dietpi-install.sh
sudo ./dietpi-install.sh
```

The Diet Pi installer will:
- ✅ Install all prerequisites (Python, nginx, etc.)
- ✅ Set up backend and XML parser services
- ✅ Build and configure frontend with nginx
- ✅ Create optimized systemd services
- ✅ Configure nginx as reverse proxy

**📗 For complete Diet Pi guide, see [DIETPI.md](DIETPI.md)**

**Resource usage on Diet Pi:**
- nginx: ~10-20MB RAM
- Backend: ~80-150MB RAM  
- XML Parser: ~40-80MB RAM
- **Total: ~130-250MB RAM** (50-100MB less than standard Raspberry Pi OS!)

**Benefits of Diet Pi:**
- 50MB+ less RAM usage compared to standard Raspberry Pi OS
- Faster boot times (~20-30 seconds)
- Built-in software manager for easy updates
- Optimized for headless operation

## 📖 Usage

### Accessing the Application

1. Open your web browser and navigate to `http://localhost:5173` (development) or `http://localhost:3000` (production)
2. The application will open on the Dashboard page showing real-time system statistics
3. Use the sidebar navigation to access other sections:
   - **Materials**: Manage inventory items
   - **Stock**: Track inventory levels and movements
   - **Projects**: Manage solar installation projects
   - **Invoices**: Upload and process XML invoices

### API Documentation

The backend API includes interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Loading Sample Data

To test the application with sample data:

```bash
cd backend
source .venv/bin/activate
python3 sample_data.py
```

This will populate the database with example materials, projects, and stock records.

### Managing Services

If you installed with systemd services:

```bash
# Check service status
systemctl status solarapp-backend
systemctl status solarapp-xml-parser

# Start services
sudo systemctl start solarapp-backend
sudo systemctl start solarapp-xml-parser

# Stop services
sudo systemctl stop solarapp-backend
sudo systemctl stop solarapp-xml-parser

# View logs
journalctl -u solarapp-backend -f
journalctl -u solarapp-xml-parser -f
```

**📋 For comprehensive logging commands and troubleshooting**, see [LOGGING.md](LOGGING.md) which includes:
- Viewing and filtering logs
- Exporting logs to files
- Common troubleshooting scenarios
- Commands for sending logs to support

## 🏗️ Architecture

```
SolarApp/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── main.py          # FastAPI app and routes
│   │   ├── models.py        # SQLModel database models
│   │   ├── database.py      # Database configuration
│   │   └── api/             # API route modules
│   ├── services/
│   │   └── xml_parser/      # XML invoice parsing service
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment configuration template
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable UI components
│   │   ├── services/        # API service layer
│   │   └── App.jsx          # Main application component
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite configuration
├── docker-compose.yml        # Docker composition for all services
├── install.sh               # Automated installation script
└── README.md                # This file
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Follow the existing code style and conventions
4. **Test your changes**: Ensure all features work as expected
5. **Commit your changes**: `git commit -m "Add your feature description"`
6. **Push to your branch**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**: Describe your changes and their benefits

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Use ESLint configuration for JavaScript/React code
- Write descriptive commit messages
- Add comments for complex logic
- Update documentation for new features
- Test thoroughly before submitting PRs

## 🐛 Troubleshooting

**📋 For detailed logging and troubleshooting commands**, see [LOGGING.md](LOGGING.md)

### Common Issues

**Service not starting or errors:**
```bash
# Check service status
systemctl status solarapp-backend

# View recent error logs
journalctl -u solarapp-backend -n 50 -p err

# See LOGGING.md for more diagnostic commands
```

**Port already in use:**
```bash
# Check what's using the port
lsof -i :8000  # or :5173, :5000, :3000

# Kill the process or change ports in configuration
```

**Database migration issues:**
```bash
# Remove the database and restart
rm backend/data/solarapp.db
# Restart the backend - it will recreate the database
```

**Frontend build errors:**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Permission errors with systemd:**
```bash
# Ensure you run the install script with sudo for systemd setup
sudo ./install.sh
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Review the API documentation at `http://localhost:8000/docs`
- Check [LOGGING.md](LOGGING.md) for log collection commands when reporting issues
- Check [INSTALL_TEST.md](INSTALL_TEST.md) for installation troubleshooting
- See [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) for recent changes

## 🔄 Project Status

Active development. See [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) for recent improvements and changes.

---

**Made with ❤️ for efficient solar panel project management**