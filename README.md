# Fleet Management System (`fleet_management`)

> **Production-Grade Enterprise Fleet Management System built for Frappe Framework Version 15.**

---

## 🚗 Project Overview

The **Fleet Management System** is a reusable, enterprise-ready Frappe application designed for multi-tenant and multi-company fleet management. It provides complete infrastructure for scalability, security, rate limiting, role-based access control (RBAC), central logging, service-oriented architecture, master data management, and containerized deployment.

---

## 🏗️ Architecture & Master Data (Phase 3 Completed)

This app strictly follows enterprise software engineering principles:
- **SOLID & DRY Architecture**: Zero magic strings. Centralized `constants.py` and strongly typed Python `enums.py`.
- **Master Data Architecture**: 11 production-ready reusable Master DocTypes (`Vehicle Brand`, `Vehicle Model`, `Vehicle Category`, `Fuel Type`, `Maintenance Type`, `Expense Category`, `Fuel Station`, `Maintenance Vendor`, `Vehicle Colour`, `Distance Unit`, `Fuel Unit`).
- **Base Document Controller (`BaseFleetDocument`)**: Subclasses inherit timestamp, audit tracking, state machine status, and permission mixins.
- **Business Rule ID Catalog (`MASTER-001` .. `MASTER-020`)**: All validations tied to documented Rule IDs.
- **Fleet Settings Singleton**: Centralized system configuration via `Fleet Settings` single DocType with Redis caching via `SettingsService`.
- **Services Architecture**: `SettingsService`, `AuditService`, `NotificationService`, `PermissionService`.

---

## 📁 Repository Structure Overview

```
fleet_management/
├── fleet_management/        # Python Application Package
│   ├── api/                 # Enterprise Whitelisted API Wrappers & Standard Responses
│   ├── business_rules/      # Decoupled Business Invariant Rule Engine
│   ├── config/              # Desk Sidebar & Module Configurations
│   ├── dashboard/           # Desk Dashboard Charts & Analytics Definitions
│   ├── events/              # Document Event Registry & Dispatcher
│   ├── fleet_management/    # Desk Workspace & Master DocTypes
│   │   └── doctype/
│   │       ├── distance_unit/      # Distance Unit Master
│   │       ├── expense_category/   # Expense Category Master
│   │       ├── fleet_settings/     # Fleet Settings Singleton
│   │       ├── fuel_station/       # Fuel Station Master
│   │       ├── fuel_type/          # Fuel Type Master
│   │       ├── fuel_unit/          # Fuel Unit Master
│   │       ├── maintenance_type/   # Maintenance Type Master
│   │       ├── maintenance_vendor/ # Maintenance Vendor Master
│   │       ├── vehicle_brand/      # Vehicle Brand Master
│   │       ├── vehicle_category/   # Vehicle Category Master
│   │       ├── vehicle_colour/     # Vehicle Colour Master
│   │       └── vehicle_model/      # Vehicle Model Master
│   ├── mixins/              # Reusable Document Mixins
│   ├── notifications/       # Multi-Channel Notification Engine & Service
│   ├── permissions/         # Security Evaluators, Audit Logging & Permission Service
│   ├── services/            # Base Service, SettingsService, AuditService
│   ├── tests/               # Pytest Unit Test Suite
│   ├── utils/               # BaseFleetDocument, Logger, Exception Hierarchy, Helpers
│   ├── validators/          # Input, Entity & Common Validation Framework
│   ├── constants.py         # Shared Domain String Constants & Defaults
│   ├── enums.py             # Python Strong Enum Definitions & Audit Events
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

For full setup, manual bench steps, and development workflows, see the documentation inside `docs/`.
