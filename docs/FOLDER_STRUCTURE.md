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
│   ├── ASSIGNMENT_DOMAIN_ARCHITECTURE.md # Assignment domain design, Handover/Return & Rule IDs ASN-001..010
│   ├── ASSIGNMENT_PRODUCTION_READINESS_REPORT.md # Executive Assignment Domain Production Readiness Report
│   ├── CONTRIBUTION_GUIDE.md   # Guidelines for pull requests and code standards
│   ├── DEVELOPMENT_GUIDE.md    # Developer setup and testing workflows
│   ├── DIGITAL_ASSET_MANAGEMENT.md # Digital Asset & Document Subsystem, Rule IDs ASSET-001..008
│   ├── FOLDER_STRUCTURE.md     # Directory breakdown documentation
│   ├── FUEL_INTELLIGENCE_ARCHITECTURE.md # Fuel Intelligence Pipeline & Rule IDs FUEL-001..010
│   ├── FUEL_PRODUCTION_READINESS_REPORT.md # Executive Fuel Intelligence Production Readiness Report
│   ├── INSTALLATION_GUIDE.md   # Bench deployment & site installation
│   ├── MAINTENANCE_INTELLIGENCE_ARCHITECTURE.md # Maintenance Domain Design & Rule IDs MAINT-001..010
│   ├── MAINTENANCE_PRODUCTION_READINESS_REPORT.md # Executive Maintenance Production Readiness Report
│   ├── MASTER_DATA_ARCHITECTURE.md # Master Data ER diagram, indexes & Rule IDs
│   ├── PRODUCTION_READINESS_REPORT.md # Executive Vehicle Domain Production Readiness Report
│   └── VEHICLE_DOMAIN_ARCHITECTURE.md # Vehicle domain design, 13-state lifecycle & Rule IDs VEH-001..VEH-010
├── fleet_management/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── assignment_api.py    # Assignment Whitelisted API Endpoints Implementation
│   │   ├── base.py              # Whitelisted API wrapper (@api_endpoint decorator)
│   │   ├── fuel_api.py          # Fuel Whitelisted API Endpoints Implementation
│   │   ├── maintenance_api.py   # Maintenance Whitelisted API Endpoints Implementation
│   │   ├── responses.py         # Standardized success, error & pagination envelopes
│   │   └── vehicle_api.py       # Vehicle, Status & Asset Whitelisted API Endpoints
│   ├── business_rules/
│   │   ├── __init__.py
│   │   ├── assignment_rules.py  # Assignment Business Rules (ASN-001..ASN-010)
│   │   ├── base_rule.py         # Abstract Base Business Rule engine
│   │   ├── fuel_rules.py        # Fuel Business Rules (FUEL-001..FUEL-010)
│   │   ├── maintenance_rules.py # Maintenance Business Invariant Rules (MAINT-001..MAINT-010)
│   │   └── vehicle_rules.py     # Vehicle business invariant rules (VEH-001..VEH-006)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── docs.py              # Documentation configuration
│   │   └── fleet_management.py  # Desk sidebar configuration
│   ├── dashboard/
│   │   └── __init__.py          # Desk Dashboard charts placeholder
│   ├── events/
│   │   ├── __init__.py
│   │   ├── assignment_events.py # Assignment Event Dispatcher
│   │   ├── fuel_events.py       # Fuel Event Dispatcher
│   │   ├── maintenance_events.py # Maintenance Event Dispatcher
│   │   ├── registry.py          # Document Event Registry
│   │   └── vehicle_events.py    # Vehicle Event Dispatcher
│   ├── fixtures/
│   │   └── __init__.py          # Fixtures package
│   ├── fleet_management/
│   │   ├── doctype/
│   │   │   ├── distance_unit/
│   │   │   ├── expense_category/
│   │   │   ├── fleet_settings/
│   │   │   ├── fuel_entry/         # Main Fuel Entry DocType
│   │   │   ├── fuel_station/
│   │   │   ├── fuel_type/
│   │   │   ├── fuel_unit/
│   │   │   ├── maintenance_request/    # Main Maintenance Request DocType
│   │   │   ├── maintenance_task/       # Child Table DocType
│   │   │   ├── maintenance_task_template/ # Master Reference DocType
│   │   │   ├── maintenance_type/
│   │   │   ├── maintenance_vendor/
│   │   │   ├── maintenance_work_order/ # Main Maintenance Work Order DocType
│   │   │   ├── vehicle/            # Main Vehicle DocType
│   │   │   ├── vehicle_assignment/ # Main Vehicle Assignment DocType
│   │   │   ├── vehicle_brand/
│   │   │   ├── vehicle_category/
│   │   │   ├── vehicle_colour/
│   │   │   ├── vehicle_document_detail/ # Child Table DocType
│   │   │   ├── vehicle_image_detail/    # Child Table DocType
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
│   │   ├── assignment_permission.py # AssignmentPermissionEvaluator
│   │   ├── audit.py             # Security audit log decorators
│   │   ├── evaluator.py         # Role-based access control (RBAC) evaluator
│   │   ├── fuel_permission.py   # FuelPermissionEvaluator
│   │   ├── maintenance_permission.py # MaintenancePermissionEvaluator
│   │   ├── service.py           # PermissionService
│   │   └── vehicle_permission.py # VehiclePermissionEvaluator
│   ├── public/                  # Static web assets
│   ├── reports/
│   │   └── __init__.py          # Analytics reports directory
│   ├── services/
│   │   ├── __init__.py
│   │   ├── assignment_service.py # AssignmentService Implementation
│   │   ├── audit_service.py     # AuditService
│   │   ├── base_service.py      # Abstract Base Service & Transaction management
│   │   ├── fuel_average_service.py # FuelAverageService
│   │   ├── fuel_service.py      # FuelService Implementation
│   │   ├── maintenance_due_service.py # MaintenanceDueEngine
│   │   ├── maintenance_lock_service.py # MaintenanceLockService
│   │   ├── maintenance_service.py # MaintenanceService Implementation & Analytics Helpers
│   │   ├── settings_service.py   # SettingsService with Redis caching
│   │   └── vehicle_service.py   # Vehicle Single Source of Truth Service
│   ├── templates/               # Public Web Jinja templates
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest fixtures configuration
│   │   ├── test_assignment_architecture.py
│   │   ├── test_assignment_business_logic.py
│   │   ├── test_assignment_production_readiness.py
│   │   ├── test_business_rules.py
│   │   ├── test_constants_enums.py
│   │   ├── test_foundation.py
│   │   ├── test_fuel_architecture.py
│   │   ├── test_fuel_entry_doctype.py
│   │   ├── test_fuel_intelligence_engine.py
│   │   ├── test_fuel_production_readiness.py
│   │   ├── test_helpers_mixins.py
│   │   ├── test_maintenance_architecture.py
│   │   ├── test_maintenance_doctypes.py
│   │   ├── test_maintenance_intelligence_engine.py
│   │   ├── test_maintenance_production_readiness.py # Master Maintenance Production Readiness Test Suite
│   │   ├── test_master_doctypes.py
│   │   ├── test_settings_service.py
│   │   ├── test_validators.py
│   │   ├── test_vehicle_architecture.py
│   │   ├── test_vehicle_asset_management.py
│   │   ├── test_vehicle_assignment_doctype.py
│   │   ├── test_vehicle_doctype.py
│   │   ├── test_vehicle_lifecycle_services.py
│   │   └── test_vehicle_production_readiness.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── base_document.py     # BaseFleetDocument controller
│   │   ├── exceptions.py        # Domain exception hierarchy & aliases
│   │   ├── helpers.py           # Reusable date, number, string, doc & format helpers
│   │   └── logger.py            # Central logger & execution timer
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── assignment_validator.py # AssignmentValidator (ASN-001..ASN-010)
│   │   ├── base_validator.py    # Abstract validator interface
│   │   ├── common_validators.py # Global reusable validators
│   │   ├── fuel_validator.py    # FuelValidator (FUEL-001..FUEL-010)
│   │   ├── maintenance_validator.py # MaintenanceValidator (MAINT-001..MAINT-010)
│   │   ├── vehicle_asset_validator.py # VehicleAssetValidator (ASSET-001..008)
│   │   └── vehicle_validator.py # VehicleValidator (Rule IDs VEH-001..VEH-010)
│   ├── constants.py             # System domain string constants & Lifecycles
│   ├── enums.py                 # Strong Python Enum classes & Maintenance Enums
│   ├── desktop.py               # Desk Module icon definition
│   ├── hooks.py                 # App registration & fixture declarations
│   └── modules.txt              # Registered Modules List
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
