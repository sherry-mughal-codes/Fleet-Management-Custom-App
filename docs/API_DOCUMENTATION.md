# REST API v1 Reference Specification

## Fleet Management System v1.0.0

All API endpoints require active Frappe session authentication or Token Authentication (`api_key:api_secret`).
Responses follow the standard API envelope:
```json
{
  "success": true,
  "status_code": 200,
  "message": "Operation completed successfully.",
  "data": { ... },
  "meta": {
    "endpoint": "fleet_management.api.v1...",
    "execution_time_ms": 12.4
  }
}
```

---

## 1. Vehicle Intelligence API (`/api/v1/vehicle_api`)

### `POST /api/method/fleet_management.api.v1.vehicle_api.create_vehicle_api`
Creates a new `Fleet Vehicle` record.
- **Role Required**: `Fleet Manager`, `Fleet Officer`
- **Payload**:
  ```json
  {
    "vehicle_number": "KAE-1024",
    "vehicle_name": "Corolla Executive",
    "vehicle_brand": "Toyota",
    "vehicle_category": "Sedan",
    "company": "ABC Logistics (Private) Limited",
    "initial_odometer": 12000.0,
    "maintenance_template": "Sedan Standard Maintenance Template"
  }
  ```

### `GET /api/method/fleet_management.api.v1.vehicle_api.get_vehicle_api`
Retrieves `Fleet Vehicle` document details by `vehicle_id`.

### `POST /api/method/fleet_management.api.v1.vehicle_api.change_status_api`
Executes vehicle state transition (13 lifecycle states).
- **Payload**: `{"vehicle_id": "VEH-2026-00001", "new_status": "Assigned", "reason": "Handover"}`

---

## 2. Assignment Intelligence API (`/api/v1/assignment_api`)

### `POST /api/method/fleet_management.api.v1.assignment_api.create_assignment_api`
Creates a new `Vehicle Assignment` record.

### `POST /api/method/fleet_management.api.v1.assignment_api.assign_vehicle_api`
Executes vehicle handover workflow, updates opening odometer, sets vehicle state to `Assigned`.

### `POST /api/method/fleet_management.api.v1.assignment_api.return_vehicle_api`
Executes vehicle return workflow, validates closing odometer (`closing >= opening`), calculates mileage.

---

## 3. Fuel Intelligence API (`/api/v1/fuel_api`)

### `POST /api/method/fleet_management.api.v1.fuel_api.create_fuel_entry_api`
Enforces maintenance lock check before creating `Fuel Entry`.

### `POST /api/method/fleet_management.api.v1.fuel_api.submit_fuel_entry_api`
Submits entry, calculates fuel average (KM/L), updates vehicle & assignment statistics.

---

## 4. Maintenance Intelligence API (`/api/v1/maintenance_api`)

### `POST /api/method/fleet_management.api.v1.maintenance_api.create_maintenance_entry_api`
Creates `Maintenance Entry` linked to a vehicle or maintenance template.

### `POST /api/method/fleet_management.api.v1.maintenance_api.submit_maintenance_entry_api`
Submits servicing entry, resets completed maintenance items, recalculates vehicle health score and next due odometer.

---

## 5. Fleet Cost Intelligence API (`/api/v1/cost_api`)

### `GET /api/method/fleet_management.api.v1.cost_api.get_vehicle_cost_api`
Returns total fuel spend, maintenance cost, operating spend, and Cost per KM.

### `GET /api/method/fleet_management.api.v1.cost_api.get_company_cost_api`
Returns aggregated `Fleet Company` operating spend.

---

## 6. Demo Dataset Management API (`/api/demo_api`)

### `POST /api/method/fleet_management.api.demo_api.load_demo_data`
Loads full demo dataset for *ABC Logistics (Private) Limited*.

### `POST /api/method/fleet_management.api.demo_api.remove_demo_data`
Purges transactional demo data (`Fuel Entry`, `Maintenance Entry`, `Vehicle Assignment`) while preserving master data (`Fleet Vehicle`, `Fleet Company`).

### `POST /api/method/fleet_management.api.demo_api.reload_demo_data`
Executes complete purge & reload cycle for the demo dataset.

---

## 7. Command Center & Analytics API (`/api/v1/analytics_api`)

### `GET /api/method/fleet_management.api.v1.analytics_api.get_executive_dashboard_api`
Retrieves executive command center metrics, KPI cards, and smart alerts.
Returns full data integrity and system health audit report.

### `POST /api/method/fleet_management.api.v1.automation_api.run_automation_job_api`
Manually triggers an automation subroutine (`maintenance`, `fuel`, `assignment`, `cost`, `health`, `all`). Requires `Fleet Manager` role.
