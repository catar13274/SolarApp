# SolarApp

**SolarApp** is a comprehensive Solar Panel Management System designed to streamline the management of solar panel installations, inventory, and projects. Built with a modern tech stack, it provides an intuitive interface for tracking materials, managing stock levels, coordinating projects, and processing invoices.

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

- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip3** - Usually comes with Python
- **Node.js 18 or higher** - [Download Node.js](https://nodejs.org/)
- **npm** - Usually comes with Node.js
- **git** (optional) - [Download Git](https://git-scm.com/downloads/)

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
5. ✅ Install frontend dependencies and build the application
6. ✅ Create and configure systemd services (when run with sudo)
7. ✅ Optionally load sample data for testing

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

## 📖 Usage

### Accessing the Application

1. Open your web browser and navigate to `http://localhost:5173` (development) or `http://localhost:3000` (production)
2. The application will open on the Dashboard page showing real-time system statistics
3. Use the sidebar navigation to access different sections:
   - **Dashboard**: Overview of system statistics
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

### Common Issues

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
- Check [INSTALL_TEST.md](INSTALL_TEST.md) for installation troubleshooting
- See [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) for recent changes

## 🔄 Project Status

Active development. See [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md) for recent improvements and changes.

---

**Made with ❤️ for efficient solar panel project management**