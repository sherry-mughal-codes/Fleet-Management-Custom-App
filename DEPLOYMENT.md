# Deployment & Operation Guide

## Overview

This guide outlines deployment, site installation, data migration, and unit test execution for the Fleet Management App on Frappe v15.

---

## 1. Docker Compose Deployment

Launch the backend, database, redis, and frontend containers:

```bash
docker compose up -d
```

---

## 2. Bench Site Migration & App Installation

Run site migration to register new DocTypes and execute patch scripts:

```bash
docker compose exec backend bench --site fleet.localhost migrate
```

---

## 3. Automated Test Verification

Execute full pytest suite across all 42 test modules:

```bash
docker compose exec backend /home/frappe/frappe-bench/env/bin/pytest apps/fleet_management/fleet_management/tests
```

---

## 4. Demo Data Management APIs

Administrators can invoke whitelisted demo management tools:

- **Load Demo Data**: `/api/method/fleet_management.api.demo_api.load_demo_data`
- **Remove Demo Data**: `/api/method/fleet_management.api.demo_api.remove_demo_data`
- **Reload Demo Data**: `/api/method/fleet_management.api.demo_api.reload_demo_data`
- **System Health Check**: `/api/method/fleet_management.api.demo_api.system_health_check`
- **Recalculate Fleet Statistics**: `/api/method/fleet_management.api.demo_api.recalculate_fleet_statistics`
