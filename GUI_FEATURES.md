# SolarApp - Graphical User Interface Features

## Overview

SolarApp includes a complete graphical user interface (GUI) with navigation menus and multiple pages for managing solar panel installations.

## Interface Components

### Navigation Menu (Sidebar)

The application features a responsive sidebar navigation menu with the following sections:

1. **Dashboard** (`/`) - Home page with system overview
2. **Materials** (`/materials`) - Inventory management
3. **Stock** (`/stock`) - Stock level monitoring
4. **Projects** (`/projects`) - Project management
5. **Invoices** (`/invoices`) - Invoice processing

The sidebar is:
- Always visible on desktop (≥1024px)
- Collapsible on mobile with a hamburger menu
- Features the SolarApp logo and brand name
- Highlights the active/current page

### Top Navigation Bar

The top bar displays:
- Menu toggle button (mobile only)
- Page title "Solar Panel Management"
- Current date in Romanian format

## Pages

### 1. Dashboard Page (`/`)

**Features:**
- **Statistics Cards**: Display key metrics
  - Total Materials
  - Low Stock Alerts
  - Active Projects
  - Total Projects
- **Recent Stock Movements**: Shows latest inventory changes
- **Quick Actions**: Fast access buttons for common tasks
  - Add Material
  - New Project
  - Upload Invoice

### 2. Materials Page (`/materials`)

**Features:**
- **Search Bar**: Search materials by name or SKU
- **Category Filter**: Filter by material type
  - Solar Panels
  - Inverters
  - Batteries
  - Cables
  - Mounting
  - Other
- **Add Material Button**: Create new material entries
- **Materials List**: Display all materials with details

### 3. Stock Management Page (`/stock`)

**Features:**
- **Stock Levels Section**: View current inventory
- **Filter Tabs**: 
  - All Stock
  - Low Stock Only (with count)
- **Record Movement Button**: Add stock changes
- **Stock Movements History**: Timeline of inventory changes

### 4. Projects Page (`/projects`)

**Features:**
- **Status Filter**: Filter projects by status
  - All Projects
  - Planned
  - In Progress
  - Completed
  - Cancelled
- **New Project Button**: Create new solar installation projects
- **Projects List**: Display all projects with details

### 5. Invoices Page (`/invoices`)

**Features:**
- **Upload Invoice Button**: Upload XML invoices
- **Invoice List**: Display uploaded invoices
- **XML Parser Integration**: Process e-Factura format
- **Material Matching**: Automatic matching with inventory

## Design System

### Colors
- Primary Blue: `#2563eb` (buttons, active states)
- Background: White and light gray tones
- Text: Gray scale for hierarchy
- Status Colors: Red (alerts), Green (success), Purple (info)

### Typography
- System fonts with clean, modern appearance
- Clear hierarchy with heading sizes
- Readable body text

### Icons
- Lucide React icon library
- Consistent 5x5 (20px) sizing in navigation
- Contextual icons for actions and status

## Responsive Design

The interface is fully responsive:

- **Desktop (≥1024px)**: Fixed sidebar, full layout
- **Tablet (768px-1023px)**: Collapsible sidebar
- **Mobile (<768px)**: Hidden sidebar with overlay menu

## Accessibility

- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus states for interactive elements

## Technology Stack

### Frontend
- **React 18**: Modern React with hooks
- **React Router**: Client-side routing
- **TailwindCSS**: Utility-first CSS framework
- **Vite**: Fast development and build tool
- **Lucide React**: Icon library

### Backend
- **FastAPI**: REST API backend
- **SQLModel**: Database ORM
- **Uvicorn**: ASGI server

## Running the Application

### Development Mode

1. **Start Backend:**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the GUI:**
   - Open browser to `http://localhost:5173`

### Production Mode

1. **Build Frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start Services:**
   ```bash
   # Using the installation script
   sudo ./install.sh
   
   # Or using Docker
   docker-compose up -d
   ```

3. **Access the GUI:**
   - Open browser to `http://localhost:3000`

## Screenshots

### Dashboard
The main dashboard provides an overview of the entire system with statistics and quick actions.

### Materials Management
Browse, search, and manage all solar panel components and materials in inventory.

### Stock Control
Monitor current stock levels, track movements, and receive low stock alerts.

### Project Management
Create and manage solar installation projects from planning to completion.

### Invoice Processing
Upload and process XML invoices in e-Factura format with automatic material matching.

## Future Enhancements

Potential improvements to the GUI:

1. Dark mode support
2. Advanced filtering and sorting
3. Data visualization with charts
4. Bulk operations
5. Export functionality
6. User authentication and roles
7. Multi-language support
8. Custom themes

## Support

For questions or issues related to the GUI:
- See the main [README.md](README.md) for general documentation
- Check [INSTALL_TEST.md](INSTALL_TEST.md) for installation help
- Review [RASPBERRY_PI.md](RASPBERRY_PI.md) for Raspberry Pi specific guidance

---

**Interface Status**: ✅ Fully Implemented and Functional
