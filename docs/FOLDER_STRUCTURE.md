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
│   ├── ARCHITECTURE_OVERVIEW.md # Enterprise layer explanations
│   ├── CONTRIBUTION_GUIDE.md   # Guidelines for pull requests and code standards
│   ├── DEVELOPMENT_GUIDE.md    # Developer setup and testing workflows
│   ├── FOLDER_STRUCTURE.md     # Directory breakdown documentation
│   └── INSTALLATION_GUIDE.md   # Bench deployment & site installation
├── fleet_management/
│   ├── api/
│   │   ├── __init__.py
│   │   └── base.py              # Whitelisted API wrapper (@api_endpoint decorator)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── docs.py              # Documentation configuration
│   │   └── fleet_management.py  # Desk sidebar configuration
│   ├── dashboard/
│   │   └── __init__.py          # Desk Dashboard charts placeholder
│   ├── fixtures/
│   │   └── __init__.py          # Fixtures package
│   ├── fleet_management/
│   │   ├── __init__.py
│   │   └── workspace/
│   │       ├── __init__.py
│   │       └── fleet_management/
│   │           ├── __init__.py
│   │           └── fleet_management.json  # Desk Workspace fixture definition
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── engine.py            # Reusable Notification Engine
│   ├── patches/
│   │   └── __init__.py          # Database patches directory
│   ├── permissions/
│   │   ├── __init__.py
│   │   ├── audit.py             # Security audit log decorators
│   │   └── evaluator.py         # Role-based access control (RBAC) evaluator
│   ├── public/                  # Static web assets
│   ├── reports/
│   │   └── __init__.py          # Analytics reports directory
│   ├── services/
│   │   ├── __init__.py
│   │   └── base_service.py      # Abstract Base Service & Transaction management
│   ├── templates/               # Public Web Jinja templates
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest fixtures configuration
│   │   └── test_foundation.py   # Infrastructure unit tests
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── exceptions.py        # Domain exception hierarchy
│   │   ├── helpers.py           # Reusable helpers & caching decorators
│   │   └── logger.py            # Central logging architecture
│   ├── validators/
│   │   ├── __init__.py
│   │   └── base_validator.py    # Abstract validator interface
│   ├── __init__.py              # App version metadata
│   ├── desktop.py               # Desk Module icon definition
│   ├── hooks.py                 # App registration & lifecycle hooks
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

---

## 🔑 Core Design Patterns

1. **Separation of Concerns**: Business logic lives strictly in `services/`, input validation in `validators/`, security evaluation in `permissions/`, and whitelisted endpoints in `api/`.
2. **Standard API Envelope**: Every API endpoint decorated with `@api_endpoint` returns a predictable JSON envelope with `success`, `status_code`, `message`, `data`, and `meta`.
3. **Domain Exception Safety**: All errors inherit from `FleetManagementError`, producing structured HTTP status responses instead of uncaught 500 HTML tracebacks.
