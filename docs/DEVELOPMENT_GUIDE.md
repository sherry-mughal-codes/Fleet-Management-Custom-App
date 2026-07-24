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

### Option B: Local Frappe Bench Setup
If running inside an existing local Linux bench environment:

```bash
# Get app into bench
bench get-app https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git

# Install on target site
bench --site fleet.localhost install-app fleet_management

# Start bench execution
bench start
```

---

## 🧪 Running Automated Tests

Run the infrastructure unit test suite with `pytest`:

```bash
pytest fleet_management/tests
```

Run tests using Frappe Bench runner:

```bash
bench --site fleet.localhost run-tests --app fleet_management
```

---

## 🧹 Code Quality & Formatting Pipeline

### Ruff Linter
```bash
ruff check fleet_management
```

### Black Formatter
```bash
black --check fleet_management
```

### Pre-commit Installation
```bash
pre-commit install
pre-commit run --all-files
```

---

## ⚙️ Bench Commands Cheat Sheet

| Command | Purpose |
| :--- | :--- |
| `bench start` | Start dev web server, socketio, background workers |
| `bench enable-scheduler` | Enable background scheduler on active site |
| `bench doctor` | Check background worker and Redis health |
| `bench build --app fleet_management` | Compile JS/CSS asset bundle |
| `bench migrate` | Run database schema updates and patches |
