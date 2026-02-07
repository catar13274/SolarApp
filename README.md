# SolarApp 🌞

Complete solar panel installation management system with inventory, materials, projects, and invoice management.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 📦 **Materials Management**: Track solar panels, inverters, batteries, cables, and mounting hardware
- 📊 **Inventory Control**: Real-time stock levels with automatic low-stock alerts
- 🏗️ **Project Management**: Manage installations from planning to completion with material tracking
- 📄 **Invoice Processing**: Upload and parse XML invoices (e-Factura UBL format)
- 📈 **Dashboard**: Overview of business metrics and recent activities
- 🔄 **Automatic Stock Updates**: Stock automatically updates when purchases or projects change
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🚀 Quick Installation

### One-Command Install (Raspberry Pi / Ubuntu / Debian)

```bash
curl -fsSL https://raw.githubusercontent.com/catar13274/SolarApp/main/install.sh | bash
```

This will:
- Check and install prerequisites (Python 3.9+, Node.js 18+)
- Clone the repository
- Set up the backend with virtual environment
- Set up the frontend
- Optionally create systemd services for auto-start
- Optionally load sample data

### Manual Installation

#### Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn
- Git

#### Backend Setup

```bash
# Clone repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install XML parser dependencies
cd services/xml_parser
pip install -r requirements.txt
cd ../..

# Create .env file
cp .env.example .env
# Edit .env and set your configuration

# Initialize database
python3 -c "from app.database import create_db_and_tables; create_db_and_tables()"

# (Optional) Load sample data
python3 sample_data.py

# Run backend
./run.sh
```

Backend will be available at `http://localhost:8000`

#### Frontend Setup

```bash
# In a new terminal
cd SolarApp/frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit if needed (default should work)

# Development mode
npm run dev

# OR Production mode
npm run build
npx serve -s dist -l 3000
```

Frontend will be available at `http://localhost:5173` (dev) or `http://localhost:3000` (prod)

#### XML Parser Service

```bash
# In a new terminal
cd SolarApp/backend/services/xml_parser

# Make sure virtual environment is activated
source ../../.venv/bin/activate

# Run parser service
gunicorn --bind 0.0.0.0:5000 --workers 2 parser_app:app
```

Parser service will be available at `http://localhost:5000`

### Docker Installation

```bash
# Clone repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Set environment variables (optional)
export XML_PARSER_TOKEN=$(openssl rand -hex 32)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- XML Parser: `http://localhost:5000`

## 📖 Usage Guide

### Dashboard

The dashboard provides an overview of your business:
- Total materials count
- Low stock alerts with count
- Active projects
- Recent stock movements
- Quick action cards

### Materials Management

- **View Materials**: Browse all materials with search and category filters
- **Add Material**: Click "Add Material" button, fill in details (name, SKU, category, price, min stock)
- **Edit Material**: Click edit icon on any material row
- **Delete Material**: Click delete icon (with confirmation)
- **Stock Badge**: Green if stock is adequate, red if below minimum

Categories:
- Solar Panels
- Inverters
- Batteries
- Cables
- Mounting Hardware
- Other

### Stock Management

- **View Stock**: See current stock levels for all materials
- **Low Stock Filter**: Toggle to see only items below minimum threshold
- **Record Movement**: Add/remove stock, adjust quantities, or transfer stock
- **Movement History**: View all stock movements with dates, types, and notes

Movement Types:
- **In**: Add stock (purchases, returns)
- **Out**: Remove stock (used in projects, sold)
- **Adjustment**: Set stock to specific quantity
- **Transfer**: Move between locations

### Project Management

- **Create Project**: Add client details, location, capacity, estimated cost
- **Status Tracking**: Planned → In Progress → Completed
- **Materials Planning**: Add materials needed for each project
- **Track Usage**: Record materials used and compare to planned quantities
- **Cost Analysis**: Compare estimated vs actual costs

Project Statuses:
- **Planned**: Project scheduled
- **In Progress**: Installation ongoing
- **Completed**: Project finished
- **Cancelled**: Project cancelled

### Invoice Processing

- **Upload XML**: Drag & drop or select XML invoice files
- **Auto-Parse**: System automatically extracts invoice data
- **Create Purchase**: Purchase record created from invoice
- **Update Stock**: Stock automatically updated based on invoice items

Supported Format: e-Factura (UBL XML) format from Romania

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for APIs
- **SQLModel**: SQL databases in Python, designed for simplicity
- **SQLite**: Lightweight, serverless database
- **defusedxml**: Secure XML parsing
- **Uvicorn**: ASGI server
- **httpx**: Async HTTP client

### Frontend
- **React 18**: UI library
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **React Router v6**: Client-side routing
- **TanStack Query**: Data fetching and caching
- **React Hook Form**: Form management
- **React Hot Toast**: Notifications
- **React Dropzone**: File upload
- **Lucide React**: Icon library
- **Axios**: HTTP client

## 📁 Project Structure

```
SolarApp/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLModel models
│   │   └── api/                 # API endpoints
│   │       ├── materials.py
│   │       ├── stock.py
│   │       ├── projects.py
│   │       ├── purchases.py
│   │       └── invoices.py
│   ├── services/
│   │   └── xml_parser/          # XML parser service
│   ├── requirements.txt
│   ├── sample_data.py
│   └── run.sh
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/          # Navigation & layout
│   │   │   ├── Common/          # Reusable components
│   │   │   ├── Materials/
│   │   │   ├── Stock/
│   │   │   ├── Projects/
│   │   │   └── Invoices/
│   │   ├── pages/               # Page components
│   │   ├── services/            # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── install.sh
└── README.md
```

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
SOLARAPP_DB_URL=sqlite:///./solarapp.db
XML_PARSER_URL=http://localhost:5000
XML_PARSER_TOKEN=your-secret-token-here
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend Environment Variables

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## 🧪 API Documentation

Once the backend is running, visit:

- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Main Endpoints

- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/materials/` - List materials
- `POST /api/v1/materials/` - Create material
- `GET /api/v1/stock/` - List stock
- `GET /api/v1/stock/low` - Low stock items
- `POST /api/v1/stock/movement` - Record movement
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/invoices/upload` - Upload invoice

## 🔒 Security

- XML parsing uses `defusedxml` to prevent XML attacks
- API token authentication for XML parser service
- Input validation with Pydantic models
- SQL injection prevention with SQLModel
- CORS configuration for API access

## 📝 Sample Data

The sample data includes:
- 15 materials (panels, inverters, batteries, cables, mounting hardware)
- Initial stock levels for all materials
- 4 sample projects with different statuses

Load sample data:

```bash
cd backend
python3 sample_data.py
```

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Reinstall dependencies
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# Check logs
tail -f /path/to/error.log
```

### Frontend won't build

```bash
# Check Node version
node --version  # Should be 18+

# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Database issues

```bash
# Recreate database
cd backend
rm solarapp.db
python3 -c "from app.database import create_db_and_tables; create_db_and_tables()"
python3 sample_data.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**catar13274**

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React team for the amazing UI library
- All open-source contributors

---

Made with ☀️ for solar panel professionals