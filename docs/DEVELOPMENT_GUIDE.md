# Development Guide

## Fleet Management System (`fleet_management`)

This guide covers daily development practices, running background workers, testing, and managing code quality tools.

---

## 💻 Environment Options

### Option A: Docker Compose (Recommended)
Launch the entire Frappe stack including MariaDB, Redis, workers, socketio, and backend:

```bash
# Start all services in background
docker compose up -d

# View real-time logs
docker compose logs -f backend

# Stop all services
docker compose down
```

---

## 🧪 Running Automated Unit Tests

Run the complete test suite (constants, enums, settings service, validators, helpers, mixins, business rules):

```bash
pytest fleet_management/tests
```

Run tests using Frappe Bench runner:

```bash
bench --site fleet.localhost run-tests --app fleet_management
```

---

## ⚙️ How to Access Fleet Settings

Never call `frappe.get_single("Fleet Settings")` directly inside business modules. Always use `SettingsService`:

```python
from fleet_management.services.settings_service import SettingsService

# Get cached settings value
maintenance_interval = SettingsService.get_maintenance_interval()
currency = SettingsService.get_value("default_currency", "USD")
```

---

## 🧹 Code Quality & Formatting Pipeline

```bash
# Ruff Linter
ruff check fleet_management

# Black Formatter
black --check fleet_management

# Pre-commit hooks
pre-commit run --all-files
```
