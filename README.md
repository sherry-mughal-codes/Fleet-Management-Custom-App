# Fleet Management System (`fleet_management`)

> **Production-Grade Enterprise Fleet Management System built for Frappe Framework Version 15.**

---

## 🚗 Project Overview

The **Fleet Management System** is a reusable, enterprise-ready Frappe application designed for multi-tenant and multi-company fleet management. It provides complete infrastructure for scalability, security, rate limiting, role-based access control (RBAC), central logging, service-oriented architecture, master data management, vehicle domain foundation, digital asset management, 13-state vehicle lifecycle engine, assignment domain subsystem, fuel intelligence engine, maintenance intelligence engine, maintenance lock engine, and containerized deployment.

---

## 🏗️ Architecture & Production Readiness (Phases 0 through 6 Completed)

This app strictly follows enterprise software engineering principles:
- **SOLID & DRY Architecture**: Zero magic strings. Centralized `constants.py` and strongly typed Python `enums.py`.
- **Single Source of Truth Alignment**: All vehicle status transitions occur strictly through `VehicleService.change_status()`.
- **Vehicle Domain Subsystem**: 13-state vehicle lifecycle engine (`Draft` .. `Archived`) certified production ready (`docs/PRODUCTION_READINESS_REPORT.md`).
- **Assignment Domain Subsystem**: 8-state assignment lifecycle (`Draft` .. `Cancelled`), Handover & Return workflows, Odometer Integrity Engine (`ASSIGN-004`, `ASSIGN-005`), and `Vehicle Assignment` DocType certified production ready (`docs/ASSIGNMENT_PRODUCTION_READINESS_REPORT.md`).
- **Fuel Intelligence Subsystem**: Fuel Average Engine (`FuelAverageService`), Maintenance Lock Engine (`MaintenanceLockService`), Rule IDs (`FUEL-001` .. `FUEL-010`), and `Fuel Entry` DocType certified production ready (`docs/FUEL_PRODUCTION_READINESS_REPORT.md`).
- **Maintenance Intelligence Subsystem**: Maintenance Due Engine 4-tier hierarchy (`MaintenanceDueEngine`), Maintenance Completion & Fuel Lock Unlocking Engine, `Maintenance Request` & `Maintenance Work Order` DocTypes, Rule IDs (`MAINT-001` .. `MAINT-010`) certified production ready (`docs/MAINTENANCE_PRODUCTION_READINESS_REPORT.md`).
- **Digital Asset Subsystem**: Unlimited vehicle document attachments (`Vehicle Document Detail`) and professional photo galleries (`Vehicle Image Detail`).
- **Cataloged Validation Rules**: Rule IDs (`VEH-001` .. `VEH-010`, `ASSET-001` .. `ASSET-008`, `ASSIGN-001` .. `ASSIGN-010`, `FUEL-001` .. `FUEL-010`, `MAINT-001` .. `MAINT-010`, `MASTER-001` .. `MASTER-013`).

---

## 📁 Repository Structure Overview

```
fleet_management/
├── fleet_management/        # Python Application Package
│   ├── api/                 # Enterprise Whitelisted API Wrappers (Vehicle, Assignment, Fuel, Maintenance APIs)
│   ├── business_rules/      # Decoupled Business Invariant Engine (Vehicle, Assignment, Fuel, Maintenance Rules)
│   ├── config/              # Desk Sidebar & Module Configurations
│   ├── dashboard/           # Desk Dashboard Charts & Analytics Definitions
│   ├── events/              # Event Registry, Vehicle, Assignment, Fuel & Maintenance Event Dispatchers
│   ├── fleet_management/    # Desk Workspace, Master DocTypes, Vehicle, Assignment, Fuel & Maintenance DocTypes
│   ├── mixins/              # Reusable Document Mixins
│   ├── notifications/       # Multi-Channel Notification Engine & Service
│   ├── permissions/         # Security Evaluators (Vehicle, Assignment, Fuel & Maintenance Permissions)
│   ├── services/            # Base Service, SettingsService, VehicleService, AssignmentService, FuelService, MaintenanceService, MaintenanceDueEngine
│   ├── tests/               # Pytest Unit & Integration Test Suites
│   ├── utils/               # BaseFleetDocument, Logger, Exception Hierarchy, Helpers
│   ├── validators/          # Input, Entity, Vehicle, Asset, Assignment, Fuel & Maintenance Validators
│   ├── constants.py         # Shared Domain String Constants & Lifecycles
│   ├── enums.py             # Strong Python Enum Classes
│   ├── hooks.py             # App Registration & Fixture Declarations
│   └── modules.txt          # Registered Modules List
├── docs/                    # Complete Enterprise Documentation Suite
├── Dockerfile               # Multi-stage Docker Build
├── docker-compose.yml       # Production/Dev Docker Stack
├── pyproject.toml           # Toolchain Specs
└── README.md                # Main System Overview
```

---

## 🚀 Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git
cd Fleet-Management-Custom-App

# 2. Launch Docker Compose Stack
docker compose up -d

# 3. Create Frappe Site & Install App (inside backend container)
docker compose exec backend bench new-site fleet.localhost --admin-password admin
docker compose exec backend bench --site fleet.localhost install-app fleet_management
```

For full setup, manual bench steps, and production readiness certification, see the documentation inside `docs/`.
