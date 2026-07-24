# Fleet Management System (`fleet_management`)

> **Production-Grade Enterprise Fleet Management System built for Frappe Framework Version 15.**

---

## 🚗 Project Overview

The **Fleet Management System** is a reusable, enterprise-ready Frappe application designed for multi-tenant and multi-company fleet management. It provides complete infrastructure for scalability, security, rate limiting, role-based access control (RBAC), central logging, service-oriented architecture, and containerized deployment.

---

## 🏗️ Core Foundation & Architecture (Phase 2 Completed)

This app strictly follows enterprise software engineering principles:
- **SOLID & DRY Architecture**: Zero magic strings. Centralized `constants.py` and strongly typed Python `enums.py`.
- **Fleet Settings Singleton**: Centralized system configuration via `Fleet Settings` single DocType with Redis caching via `SettingsService`.
- **Global Validation Framework**: Reusable validators for positive numbers, date ranges, odometer progression, required fields, unique duplicates, and state machine status transitions.
- **Common Mixins**: `TimestampMixin`, `AuditMixin`, `StatusMixin`, `PermissionMixin`.
- **Business Rules Architecture**: Decoupled rule engine (`BaseBusinessRule`) separating business invariants from controllers.
- **Services Architecture**: `SettingsService`, `AuditService`, `NotificationService`, `PermissionService`.
- **API Envelope & Standard Responses**: Whitelisted API endpoints utilize `@api_endpoint` and `api/responses.py` envelopes.

---

## 🛠️ Stack & Infrastructure

- **Framework**: Frappe Framework v15
- **Language**: Python 3.10+
- **Database**: MariaDB 10.6+
- **Cache**: Redis Cache
- **Queue**: Redis Queue (Default, Short, Long workers)
- **WebSockets**: Redis SocketIO & Frappe Socket.io
- **Orchestration**: Docker Compose & VS Code DevContainers

---

## 📁 Repository Structure Overview

```
fleet_management/
├── fleet_management/        # Python Application Package
│   ├── api/                 # Enterprise Whitelisted API Wrappers & Standard Responses
│   ├── business_rules/      # Decoupled Business Invariant Rule Engine
│   ├── config/              # Desk Sidebar & Module Configurations
│   ├── dashboard/           # Desk Dashboard Charts & Analytics Definitions
│   ├── fleet_management/    # Desk Workspace & Fleet Settings Single DocType
│   │   └── doctype/
│   │       └── fleet_settings/ # Fleet Settings Singleton DocType
│   ├── mixins/              # Reusable Document Mixins (Timestamp, Audit, Status, Permission)
│   ├── notifications/       # Multi-Channel Notification Engine & Service
│   ├── patches/             # Database Migration & Patch Scripts
│   ├── permissions/         # Security Evaluators, Audit Logging & Permission Service
│   ├── public/              # Static Frontend Assets (JS, CSS)
│   ├── reports/             # Analytics Reports Placeholders
│   ├── services/            # Base Service, SettingsService, AuditService
│   ├── templates/           # Web Templates & Pages
│   ├── tests/               # Pytest Unit Test Suite
│   ├── utils/               # Central Logger, Exception Hierarchy, Shared Helpers
│   ├── validators/          # Input, Entity & Common Validation Framework
│   ├── constants.py         # Shared Domain String Constants & Defaults
│   ├── enums.py             # Python Strong Enum Definitions
│   ├── desktop.py           # Desk Icon Definition
│   ├── hooks.py             # Frappe App Registration Hooks
│   └── modules.txt          # Registered Modules List
├── docs/                    # Complete Enterprise Documentation Suite
├── .devcontainer/           # DevContainer Environment Specs
├── .editorconfig            # Code Formatting Standards
├── .gitignore               # Strict Enterprise Git Exclusions
├── .pre-commit-config.yaml  # Pre-commit Quality Pipeline
├── Dockerfile               # Multi-stage Docker Build
├── docker-compose.yml       # Production/Dev Docker Stack
├── pyproject.toml           # Ruff, Black, Pytest Configuration
├── requirements.txt         # App Python Dependencies
├── setup.py                 # Setuptools Package Builder
└── README.md                # Main System Overview
```

---

## 🚀 Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git
cd Fleet-Management-Custom-App

# 2. Copy environment template
cp .env.example .env

# 3. Launch Docker Compose Stack
docker compose up -d

# 4. Create Frappe Site & Install App (inside backend container)
docker compose exec backend bench new-site fleet.localhost --admin-password admin
docker compose exec backend bench --site fleet.localhost install-app fleet_management
```

For full setup, manual bench steps, and development workflows, see the documentation inside `docs/`.
