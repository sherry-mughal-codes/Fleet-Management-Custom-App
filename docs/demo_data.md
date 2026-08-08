# Quick Demo Data Engine Documentation

## Overview

The **Quick Demo Data Engine** populates a production-grade, realistic demonstration dataset for **ABC Logistics (Private) Limited**, a logistics company operating out of Karachi, Pakistan.

It allows administrators and reviewers to immediately showcase and validate the complete feature set of the Fleet Management custom app—including Vehicle Management, Driver Assignments, Fuel Tracking, Maintenance Locks & Unlocks, Cost Aggregation, Reports, and Executive Dashboards—without manual record entry.

---

## Dataset Architecture

| Entity Domain | Record Count | Description / Details |
| :--- | :--- | :--- |
| **Fleet Company** | 1 | ABC Logistics (Private) Limited (Karachi, Pakistan, PKR currency) |
| **Departments** | 7 | Fleet Management, Operations, Administration, Finance, HR, Workshop, Logistics |
| **Employees** | 20 | Pakistani staff profiles with designations, phone numbers, and emails |
| **Fleet Vehicles** | 10 | Mixed Pakistani fleet (Corolla, Yaris, Hilux, Hiace, Civic, BR-V, Alto, Bolan, Porter, D-Max) linked to Maintenance Templates |
| **Vehicle Assignments** | 8 | 8 active submitted driver handovers (`docstatus = 1`, `status = "Assigned"`); 2 vehicles left available |
| **Fuel Entries** | ~150 | 6 months of historical fuel logs (PKR 272–289/L) with fuel average calculations |
| **Maintenance Records** | ~20 | Completed maintenance entries with child item lines, vendor invoices, and servicing baselines |

---

## Administrative Actions & Usage

Only users assigned the **System Manager**, **Fleet Manager**, or **Fleet Administrator** role (or system `Administrator`) can execute demo data management actions.

### Fleet Settings Action Center
Buttons are located in **Fleet Settings** under the **🚀 Demo Data Control Center** section (and top **Demo Actions** menu header):
- **☁ Load Demo Data** (Button): Triggers confirmation dialog, populates ABC Logistics dataset, and reloads page.
- **🗑 Remove Demo Data** (Button): Triggers confirmation dialog, purges transactional records, and reloads page.

### 1. Load Demo Data
Idempotently generates the entire ABC Logistics dataset. If master records already exist, creation is safely reused without throwing errors or creating duplicates.

**Desk Console / Python API:**
```python
import frappe
res = frappe.call("fleet_management.api.demo_api.load_demo_data")
print(res)
```

**Bench CLI:**
```bash
docker compose exec backend bench --site fleet.localhost execute fleet_management.api.demo_api.load_demo_data
```

**REST API Endpoint:**
`POST /api/method/fleet_management.api.demo_api.load_demo_data`

---

### 2. Remove Demo Data
Safely purges **transactional demo data** (`Fuel Entry`, `Maintenance Entry`, `Vehicle Assignment`) while preserving master data (`Fleet Vehicle`, `Fleet Company`, `Vehicle Brand`, `Vehicle Category`, `Vehicle Model`, Templates). All `Fleet Vehicle` records are reset to `Available` status.

**Desk Console / Python API:**
```python
import frappe
res = frappe.call("fleet_management.api.demo_api.remove_demo_data")
print(res)
```

**Bench CLI:**
```bash
docker compose exec backend bench --site fleet.localhost execute fleet_management.api.demo_api.remove_demo_data
```

**REST API Endpoint:**
`POST /api/method/fleet_management.api.demo_api.remove_demo_data`

---

### 3. Reload Demo Data
Performs a complete clean reset environment action by executing `remove_demo_data()` followed immediately by `load_demo_data()`.

**Desk Console / Python API:**
```python
import frappe
res = frappe.call("fleet_management.api.demo_api.reload_demo_data")
print(res)
```

**Bench CLI:**
```bash
docker compose exec backend bench --site fleet.localhost execute fleet_management.api.demo_api.reload_demo_data
```

**REST API Endpoint:**
`POST /api/v1/demo/reload`

---

### 4. Check Demo Status

**Desk Console / Python API:**
```python
import frappe
status = frappe.call("fleet_management.api.demo_api.get_demo_status")
print(status)
```

---

## Safety & Transaction Guarantees

1. **Idempotency**: Running `load_demo_data()` multiple times detects existing company/vehicle structures and exits gracefully.
2. **Data Scope**: All created entities are tagged under `ABC Logistics (Private) Limited` and marked with `is_demo_data: 1`. `remove_demo_data()` queries strictly by these criteria, ensuring real production records are never modified or deleted.
3. **Business Logic Enforcement**: All fuel averages, odometer progressions, maintenance lock conditions, and cost summaries are calculated using the application's underlying domain services (`FuelService`, `MaintenanceService`, `FleetCostService`).
