# 🚚 Enterprise Fleet Management System (`fleet_management`)

> **Production-Grade Enterprise Fleet Management System for Frappe Framework v15**  
> *Fully Containerized, Scalable, Role-Based, Data-Isolated, and Built with Service-Oriented Architecture (SOA)*

---

## 🌟 Executive Summary

The **Fleet Management System** (`fleet_management`) is an enterprise-grade custom app for the Frappe v15 ecosystem. It empowers organizations to manage corporate vehicle fleets, driver assignments, fuel consumption logging, preventive maintenance scheduling, cost analytics, and executive dashboard monitoring with 100% data integrity and real-time validation.

---

## ⚡ Key System Features

### 🚗 1. Vehicle Lifecycle & Master Data Management
- **13-State Vehicle Engine**: `Draft`, `Available`, `Reserved`, `Assigned`, `Maintenance Due`, `Under Maintenance`, `Inspection`, `Out of Service`, `Inactive`, `Sold`, `Scrapped`, `Archived`.
- **Dynamic Odometer Engine**: Derives real-time current odometer from submitted `Fuel Entry` records (`MAX(odometer)`), falling back to `initial_odometer`.
- **Fuel Threshold Ratings**: Configurable vehicle-level threshold boundaries (`excellent_fuel_threshold`, `good_fuel_threshold`, `average_fuel_threshold`, `poor_fuel_threshold`) for automated efficiency rating.
- **Clean Master Data**: Streamlined `Vehicle Category`, `Vehicle Brand`, `Vehicle Model`, `Vehicle Colour`, `Fuel Type`, `Distance Unit`, `Fuel Unit`, and `Expense Category` DocTypes.

### 📋 2. Maintenance Template Engine & 2-Way Auto Sync
- **Flexible Maintenance Templates**: Define preventive maintenance schedule lines with interval distances (KM), mandatory flags, and priority tiers.
- **Optional Bulk Vehicle Assignment**: Attach vehicles directly on the template form or link templates on individual vehicle records.
- **Smart 2-Way Auto Sync**: Saving a Maintenance Template automatically updates `Vehicle.maintenance_template` for all listed vehicles and unlinks removed vehicles.
- **Real-Time Duplicate Filter**: Client-side script (`maintenance_template.js`) dynamically excludes vehicles assigned to other templates AND vehicles already selected in previous form rows.

### 🔒 3. Maintenance Lock Engine & Automated Status Updates (`FUEL-008`)
- **Automated Fueling Lock**: Blocks fuel entry submissions if mandatory maintenance items exceed schedule line intervals.
- **Immediate Status Commit**: When a fuel lock triggers, the system force-commits `Vehicle.status = "Maintenance Due"` and clears Redis document cache so fleet managers see overdue status instantly.
- **Automatic Reversion**: Submitting a valid fuel entry below interval thresholds or completing a maintenance entry automatically reverts `Vehicle.status` back to `Assigned` or `Available`.

### 👥 4. Vehicle Assignment Subsystem
- **8-State Assignment Lifecycle**: Handover and return date tracking.
- **Overdue Return Integrity**: Keeps vehicle status as `Assigned` (not `Available`) while return is overdue (`Return Overdue`).

### 📊 5. Production Script Reports
1. **Vehicle Summary Report**: Real-time odometer aggregation, fuel/maintenance cost breakdown, next service due calculation, and color-matched status charts.
2. **Fuel Efficiency Report**: Calculates exact `Distance Travelled (KM)`, `Fuel Average (KM/L)`, `Cost per KM`, and dynamic `Efficiency Rating` (*Excellent*, *Good*, *Average*, *Poor*, *Critical*).
3. **Maintenance Summary Report**: Itemized servicing breakdown from child table lines showing individual maintenance activities and costs.
4. **Vehicle Activity Log**: Chronological audit trail of all fleet events and lifecycle transitions.

### 🔐 6. Role-Based Access Control (RBAC) & Data Isolation
- **Configured Roles**: `System Manager`, `Fleet Manager`, `Fleet Officer`, `Fleet User`, `Fleet Driver`, `Guest`.
- **User Permission Isolation**: Restricts drivers/staff so they only view their assigned vehicle and submit fuel/maintenance entries.

---

## 🏗️ Technical Architecture & Directory Structure

```
fleet_management/
├── fleet_management/        # Core Python Application Package
│   ├── api/                 # Whitelisted API Endpoints (Vehicle, Assignment, Fuel, Maintenance, Cost APIs)
│   ├── business_rules/      # Decoupled Business Invariant Engine (VEH, ASSIGN, FUEL, MAINT, COST rules)
│   ├── config/              # Desk Navigation & Sidebar Configuration
│   ├── dashboard/           # Desk Dashboard Charts & Analytics Definitions
│   ├── events/              # Event Registry & Signal Dispatchers
│   ├── fleet_management/    # Desk Workspaces, DocTypes, Child Tables & Script Reports
│   │   ├── doctype/         # Master & Transactional DocTypes (Vehicle, Fuel Entry, Maintenance Entry, etc.)
│   │   ├── report/          # Script Reports (Vehicle Summary, Fuel Efficiency, Maintenance Summary, Activity Log)
│   │   └── workspace/       # Executive Desk Workspace Homepage
│   ├── mixins/              # Reusable Document Mixins (Audit, Status, Permission, Timestamp)
│   ├── notifications/       # Multi-Channel Notification Engine
│   ├── permissions/         # Security Evaluators & Query Condition Hooks
│   ├── services/            # Base Service, VehicleService, AssignmentService, FuelService, MaintenanceManager, FleetCostService
│   ├── tests/               # Pytest Unit & Integration Test Suites
│   ├── utils/               # BaseFleetDocument, Logger, Exception Hierarchy, Helpers
│   ├── validators/          # Domain Validators (FUEL-001..010, MAINT-001..010, etc.)
│   ├── constants.py         # Centralized System Constants
│   ├── enums.py             # Strongly-Typed Python Enums
│   ├── hooks.py             # App Event Hooks & Fixture Registrations
│   └── modules.txt          # Registered App Modules
├── docs/                    # Complete 27-Document Enterprise Documentation Suite
├── Dockerfile               # Multi-Stage Docker Container Build
├── docker-compose.yml       # Production Container Stack Specifications
├── pyproject.toml           # Toolchain & Package Metadata
└── README.md                # Main System Documentation
```

---

## 🛠️ Installation & Setup Guide (Docker)

### 1. Clone Repository
```bash
git clone https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git
cd Fleet-Management-Custom-App
```

### 2. Build & Launch Docker Stack
```bash
docker compose up -d --build
```

### 3. Initialize Site & Install App (Inside Container)
```bash
# Enter container shell
docker exec -it fleet_backend bash

# Inside container:
cd /home/frappe/frappe-bench
bench new-site fleet.localhost --admin-password admin --mariadb-root-password root
bench --site fleet.localhost install-app fleet_management
bench --site fleet.localhost migrate
bench build --app fleet_management
bench --site fleet.localhost clear-cache
```

### 4. Access Application
- **URL**: `http://localhost:8000` or `http://fleet.localhost:8000`
- **Username**: `Administrator`
- **Password**: `admin`

---

## 📚 Complete Documentation Suite (`docs/`)

Explore detailed technical specifications in the `docs/` directory:

| Document | Description |
| :--- | :--- |
| [ARCHITECTURE_OVERVIEW.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/ARCHITECTURE_OVERVIEW.md) | High-level system design and SOA framework architecture |
| [INSTALLATION_GUIDE.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/INSTALLATION_GUIDE.md) | Manual & containerized installation walkthrough |
| [ADMINISTRATOR_GUIDE.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/ADMINISTRATOR_GUIDE.md) | Admin portal setup, role profile configuration & permissions |
| [API_DOCUMENTATION.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/API_DOCUMENTATION.md) | REST API endpoints for vehicle, fuel, assignment & maintenance |
| [BUSINESS_RULES_CATALOGUE.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/BUSINESS_RULES_CATALOGUE.md) | Complete catalog of validation rules (`VEH`, `FUEL`, `MAINT`, `COST`) |
| [FOLDER_STRUCTURE.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/FOLDER_STRUCTURE.md) | Detailed directory breakdown and file responsibilities |
| [FLEET_AUTOMATION_NOTIFICATION_ENGINE.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/FLEET_AUTOMATION_NOTIFICATION_ENGINE.md) | Automated background jobs, cron scheduling & notification engine |
| [RELEASE_NOTES_v1.0.0.md](file:///c:/Users/Sherry%20Mughal/Desktop/Fleet%20Management%20App/Fleet-Management-Custom-App/docs/RELEASE_NOTES_v1.0.0.md) | Version 1.0.0 features, improvements, and certification specs |

---

## ⚖️ License & Credits

Built with ❤️ by the Fleet Management Team using **Frappe Framework v15**.  
Licensed under the [MIT License](LICENSE).
