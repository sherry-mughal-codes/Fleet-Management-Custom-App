# Folder Structure & Architecture Reference

## Fleet Management System (`fleet_management`)

This document details every package, directory, and infrastructure file within `fleet_management`.

---

## 🌳 Comprehensive Folder Tree

```
fleet_management/
├── .devcontainer/
│   └── devcontainer.json        # VS Code Container specifications
├── .vscode/
│   ├── extensions.json          # Recommended VS Code extensions
│   ├── launch.json              # Debugging launch configurations
│   └── settings.json            # Workspace formatting & interpreter settings
├── docs/
│   ├── ARCHITECTURE_OVERVIEW.md # Enterprise layer & settings architecture
│   ├── CONTRIBUTION_GUIDE.md   # Guidelines for pull requests and code standards
│   ├── DEVELOPMENT_GUIDE.md    # Developer setup and testing workflows
│   ├── FOLDER_STRUCTURE.md     # Directory breakdown documentation
│   ├── INSTALLATION_GUIDE.md   # Bench deployment & site installation
│   └── MASTER_DATA_ARCHITECTURE.md # Master Data ER diagram, indexes & Rule IDs
├── fleet_management/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── base.py              # Whitelisted API wrapper (@api_endpoint decorator)
│   │   └── responses.py         # Standardized success, error & pagination envelopes
│   ├── business_rules/
│   │   ├── __init__.py
│   │   ├── base_rule.py         # Abstract Base Business Rule engine
│   │   ├── vehicle_rules.py     # Vehicle availability contract interface
│   │   ├── assignment_rules.py  # Assignment contract interface
│   │   ├── fuel_rules.py        # Fuel capacity contract interface
│   │   └── maintenance_rules.py # Maintenance trigger contract interface
│   ├── config/
│   │   ├── __init__.py
│   │   ├── docs.py              # Documentation configuration
│   │   └── fleet_management.py  # Desk sidebar configuration
│   ├── dashboard/
│   │   └── __init__.py          # Desk Dashboard charts placeholder
│   ├── events/
│   │   ├── __init__.py
│   │   └── registry.py          # Document Event Registry
│   ├── fixtures/
│   │   └── __init__.py          # Fixtures package
│   ├── fleet_management/
│   │   ├── doctype/
│   │   │   ├── distance_unit/
│   │   │   ├── expense_category/
│   │   │   ├── fleet_settings/
│   │   │   ├── fuel_station/
│   │   │   ├── fuel_type/
│   │   │   ├── fuel_unit/
│   │   │   ├── maintenance_type/
│   │   │   ├── maintenance_vendor/
│   │   │   ├── vehicle_brand/
│   │   │   ├── vehicle_category/
│   │   │   ├── vehicle_colour/
│   │   │   └── vehicle_model/
│   │   └── workspace/
│   │       └── fleet_management/
│   │           └── fleet_management.json # Desk Workspace fixture definition
│   ├── mixins/
│   │   ├── __init__.py
│   │   ├── audit_mixin.py       # Document mutation audit tracking mixin
│   │   ├── permission_mixin.py  # Document level permission mixin
│   │   ├── status_mixin.py      # State machine status transition mixin
│   │   └── timestamp_mixin.py   # Timestamp and date helper mixin
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── engine.py            # Notification dispatcher engine
│   │   └── service.py           # Multi-channel NotificationService
│   ├── patches/
│   │   └── __init__.py          # Database patches directory
│   ├── permissions/
│   │   ├── __init__.py
│   │   ├── audit.py             # Security audit log decorators
│   │   ├── evaluator.py         # Role-based access control (RBAC) evaluator
│   │   └── service.py           # PermissionService
│   ├── public/                  # Static web assets
│   ├── reports/
│   │   └── __init__.py          # Analytics reports directory
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audit_service.py     # AuditService
│   │   ├── base_service.py      # Abstract Base Service & Transaction management
│   │   └── settings_service.py   # SettingsService with Redis caching
│   ├── templates/               # Public Web Jinja templates
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest fixtures configuration
│   │   ├── test_business_rules.py
│   │   ├── test_constants_enums.py
│   │   ├── test_foundation.py
│   │   ├── test_helpers_mixins.py
│   │   ├── test_master_doctypes.py
│   │   ├── test_settings_service.py
│   │   └── test_validators.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── base_document.py     # BaseFleetDocument controller
│   │   ├── exceptions.py        # Domain exception hierarchy & aliases
│   │   ├── helpers.py           # Reusable date, number, string, doc & format helpers
│   │   └── logger.py            # Central logger & execution timer
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base_validator.py    # Abstract validator interface
│   │   └── common_validators.py # Global reusable validators
│   ├── constants.py             # System domain string constants
│   ├── enums.py                 # Strong Python Enum classes
│   ├── desktop.py               # Desk Module icon definition
│   ├── hooks.py                 # App registration & fixture declarations
│   └── modules.txt              # Desk module list
├── .editorconfig                # Universal indentation and whitespace rules
├── .env.example                 # Environment variables template
├── .gitignore                   # Enterprise git ignore exclusions
├── .pre-commit-config.yaml      # Code quality pre-commit pipeline
├── Dockerfile                   # Custom app container build file
├── docker-compose.override.yml  # Dev compose override settings
├── docker-compose.yml           # Full multi-container Frappe v15 stack
├── pyproject.toml               # Python toolchain specs (Ruff, Black, Pytest)
├── README.md                    # Root project documentation
├── requirements.txt             # App python dependencies
└── setup.py                     # Setuptools installer
```
