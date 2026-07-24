# Fleet Management System (`fleet_management`)

> **Production-Grade Enterprise Fleet Management System built for Frappe Framework Version 15.**

---

## 🚗 Project Overview

The **Fleet Management System** is a reusable, enterprise-ready Frappe application designed for multi-tenant and multi-company fleet management. It provides complete infrastructure for scalability, security, rate limiting, role-based access control (RBAC), central logging, service-oriented architecture, master data management, vehicle domain foundation, digital asset management, 13-state lifecycle engine, and containerized deployment.

---

## 🏗️ Architecture & Production Readiness (Phase 3 Completed)

This app strictly follows enterprise software engineering principles:
- **SOLID & DRY Architecture**: Zero magic strings. Centralized `constants.py` and strongly typed Python `enums.py`.
- **Single Source of Truth Status Engine**: All status mutations occur strictly through `VehicleService.change_status()`.
- **13-State Lifecycle Engine**: State machine governing transitions across `Draft`, `Available`, `Reserved`, `Assigned`, `Maintenance Due`, `Under Maintenance`, `Inspection`, `Out of Service`, `Inactive`, `Sold`, `Scrapped`, `Archived`.
- **Digital Asset Subsystem**: Unlimited vehicle document attachments (`Vehicle Document Detail`) and professional photo galleries (`Vehicle Image Detail`) with single primary image auto-reset (`ASSET-005`).
- **Asset & Domain Validators**: Cataloged Rule IDs (`VEH-001` .. `VEH-010`, `ASSET-001` .. `ASSET-008`, `MASTER-001` .. `MASTER-013`).
- **Enterprise UX & Minimum Data Entry Policy**: Under 2-minute registration policy classifying fields into Category A (Mandatory registration), Category B (Optional info), and Category C (Read-only System Managed).
- **Master Data Architecture**: 11 production-ready reusable Master DocTypes.
- **Production Readiness Certified**: Fully documented in `docs/PRODUCTION_READINESS_REPORT.md`.

---

## 📁 Repository Structure Overview

```
fleet_management/
├── fleet_management/        # Python Application Package
│   ├── api/                 # Enterprise Whitelisted API Wrappers & Vehicle Asset API
│   ├── business_rules/      # Decoupled Business Invariant Rule Engine & Vehicle Rules
│   ├── config/              # Desk Sidebar & Module Configurations
│   ├── dashboard/           # Desk Dashboard Charts & Analytics Definitions
│   ├── events/              # Document Event Registry & VehicleEventDispatcher
│   ├── fleet_management/    # Desk Workspace, Master DocTypes & Vehicle Child DocTypes
│   ├── mixins/              # Reusable Document Mixins
│   ├── notifications/       # Multi-Channel Notification Engine & Service
│   ├── permissions/         # Security Evaluators & VehiclePermissionEvaluator
│   ├── services/            # Base Service, SettingsService, AuditService, VehicleService
│   ├── tests/               # Pytest Integration & Production Readiness Test Suite
│   ├── utils/               # BaseFleetDocument, Logger, Exception Hierarchy, Helpers
│   ├── validators/          # Input, Entity, Common, Vehicle & VehicleAssetValidator
│   ├── constants.py         # Shared Domain String Constants & 13-State Lifecycle
│   ├── enums.py             # Python Strong Enum Definitions & Asset Enums
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
