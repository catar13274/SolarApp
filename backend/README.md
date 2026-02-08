# SolarApp Backend

Backend API for the Solar Panel Management System built with FastAPI.

## Database Setup

The backend uses SQLite as the default database. The database is automatically created when the application starts, but you can also manually initialize it using the provided script.

### Quick Start

1. **Create environment configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python3 init_db.py
   ```
   
   This script will:
   - Create the database file (`solarapp.db`)
   - Create all necessary tables
   - Display confirmation and next steps

4. **(Optional) Load sample data:**
   ```bash
   python3 sample_data.py
   ```
   
   This will populate the database with:
   - 15 sample materials (panels, inverters, batteries, cables, etc.)
   - 4 sample projects
   - Initial stock levels for all materials

5. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   The API will be available at `http://localhost:8000`

## Database Location

The database file location is determined by the `SOLARAPP_DB_URL` environment variable in the `.env` file:

- **Default configuration**: `sqlite:///./solarapp.db`
  - Creates `solarapp.db` in the current working directory
  - When running from `backend/` directory: creates `backend/solarapp.db`
  - **Important**: Always run the backend from the `backend/` directory to ensure consistent file location
  
- **Absolute path configuration**: `sqlite:////absolute/path/to/solarapp.db`
  - Creates database at the specified absolute path
  - Recommended for production deployments (e.g., `/opt/solarapp/backend/data/solarapp.db`)

You can change the database location by modifying the `SOLARAPP_DB_URL` environment variable in the `.env` file.

**Best Practice**: Always run backend commands from the `backend/` directory to ensure the database is created in the expected location.

### SQLite Files

When using SQLite with WAL (Write-Ahead Logging) mode, you'll see three files:
- `solarapp.db` - Main database file
- `solarapp.db-shm` - Shared memory file
- `solarapp.db-wal` - Write-ahead log file

These files work together to provide better performance and concurrency. All three files are ignored by git (see `.gitignore`).

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Environment Variables

Configure these in your `.env` file:

- `SOLARAPP_DB_URL` - Database connection URL (default: `sqlite:///./solarapp.db`)
- `XML_PARSER_URL` - URL for the XML parser service (default: `http://localhost:5000`)
- `XML_PARSER_TOKEN` - Authentication token for XML parser service
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins

## Database Schema

The database includes the following tables:

- **Material** - Inventory items (panels, inverters, batteries, cables, etc.)
- **Stock** - Current inventory levels per material and location
- **StockMovement** - History of all stock changes
- **Project** - Solar installation projects
- **ProjectMaterial** - Materials allocated to projects
- **Purchase** - Purchase orders from suppliers
- **PurchaseItem** - Individual items in purchase orders

## Troubleshooting

### Database Locked Error

If you see "database is locked" errors, it usually means:
1. Another process is accessing the database
2. A previous connection wasn't closed properly

**Solution:**
```bash
# Stop all running instances
pkill -f uvicorn

# If the issue persists, remove WAL files
rm solarapp.db-shm solarapp.db-wal

# Restart the server
uvicorn app.main:app --reload
```

### Database Not Found

If the application can't find the database:

1. Check that `.env` file exists and contains correct `SOLARAPP_DB_URL`
2. Run `python3 init_db.py` to create the database
3. Verify the database file exists: `ls -l solarapp.db`

### Reset Database

To completely reset the database:

```bash
# Stop the server first
# Remove database files
rm solarapp.db solarapp.db-shm solarapp.db-wal

# Reinitialize
python3 init_db.py

# (Optional) Load sample data
python3 sample_data.py
```

## Production Considerations

For production deployments:

1. **Use PostgreSQL instead of SQLite** for better concurrency and performance
2. **Set proper database URL** in environment variables
3. **Regular backups** of the database file
4. **Monitor database size** and implement archival strategy
5. **Use proper secrets** for `XML_PARSER_TOKEN`

Example PostgreSQL configuration:
```bash
SOLARAPP_DB_URL=postgresql://user:password@localhost/solarapp
```
