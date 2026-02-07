# SolarApp 🌞

Complete solar panel installation management system with inventory, materials, projects, and invoice management.

## Features

- 📦 **Materials Management**: Track solar panels, inverters, batteries, and all components
- 📊 **Inventory Control**: Real-time stock levels with low-stock alerts
- 🏗️ **Project Management**: Manage installations from planning to completion
- 📄 **Invoice Processing**: Upload and parse XML invoices (e-Factura RO format)
- 📈 **Dashboard**: Overview of business metrics and recent activities
- 🔄 **Automatic Stock Updates**: Stock updates when purchases or projects change

## Quick Installation

### One-Command Install (Raspberry Pi / Ubuntu / Debian)

```bash
curl -fsSL https://raw.githubusercontent.com/catar13274/SolarApp/main/install.sh | bash
```

## Tech Stack

**Backend:**
- FastAPI
- SQLModel (SQLAlchemy + Pydantic)
- SQLite
- defusedxml for XML parsing

**Frontend:**
- React 18
- Vite
- Tailwind CSS
- TanStack Query
- React Router

## Usage

- **Dashboard**: `http://localhost:3000`
- **API Documentation**: `http://localhost:8000/docs`

## License

MIT License

---

🚀 Full application coming soon!