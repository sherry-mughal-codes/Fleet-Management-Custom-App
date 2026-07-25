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
Creates a new Vehicle record.
- **Role Required**: `Fleet Manager`, `Fleet Officer`
- **Payload**:
  ```json
  {
    "make": "Toyota",
    "model": "Hilux",
    "vehicle_category": "Pickup",
    "license_plate": "KAA-123A",
    "initial_odometer": 1000.0,
    "company": "Fleet Corp"
  }
  ```

### `GET /api/method/fleet_management.api.v1.vehicle_api.get_vehicle_api`
Retrieves vehicle document details by `vehicle_id`.

### `POST /api/method/fleet_management.api.v1.vehicle_api.change_status_api`
Executes vehicle state transition (13 lifecycle states).
- **Payload**: `{"vehicle_id": "VEH-001", "new_status": "Assigned", "reason": "Handover"}`

---

## 2. Assignment Intelligence API (`/api/v1/assignment_api`)

### `POST /api/method/fleet_management.api.v1.assignment_api.create_assignment_api`
Creates a new Vehicle Assignment request.

### `POST /api/method/fleet_management.api.v1.assignment_api.assign_vehicle_api`
Executes vehicle handover workflow, updates opening odometer, sets vehicle state to `Assigned`.

### `POST /api/method/fleet_management.api.v1.assignment_api.return_vehicle_api`
Executes vehicle return workflow, validates closing odometer (`closing >= opening`), calculates mileage.

---

## 3. Fuel Intelligence API (`/api/v1/fuel_api`)

### `POST /api/method/fleet_management.api.v1.fuel_api.create_fuel_entry_api`
Enforces maintenance lock check before creating fuel entry.

### `POST /api/method/fleet_management.api.v1.fuel_api.submit_fuel_entry_api`
Submits entry, calculates fuel average (KM/L), updates vehicle & assignment statistics.

---

## 4. Maintenance Intelligence API (`/api/v1/maintenance_api`)

### `POST /api/method/fleet_management.api.v1.maintenance_api.create_work_order_api`
Creates Maintenance Work Order linked to a request or template.

### `POST /api/method/fleet_management.api.v1.maintenance_api.complete_work_order_api`
Completes work order, updates vehicle last maintenance odometer, clears maintenance lock.

---

## 5. Fleet Cost Intelligence API (`/api/v1/cost_api`)

### `GET /api/method/fleet_management.api.v1.cost_api.get_vehicle_cost_api`
Returns total fuel spend, maintenance cost, operating spend, and Cost per KM.

### `GET /api/method/fleet_management.api.v1.cost_api.get_company_cost_api`
Returns aggregated company fleet operating spend.

---

## 6. Command Center & Analytics API (`/api/v1/analytics_api`)

### `GET /api/method/fleet_management.api.v1.analytics_api.get_executive_dashboard_api`
Retrieves executive command center metrics, KPI cards, and smart alerts.

---

## 7. Automation & Health API (`/api/v1/automation_api`)

### `GET /api/method/fleet_management.api.v1.automation_api.get_health_report_api`
Returns full data integrity and system health audit report.

### `POST /api/method/fleet_management.api.v1.automation_api.run_automation_job_api`
Manually triggers an automation subroutine (`maintenance`, `fuel`, `assignment`, `cost`, `health`, `all`). Requires `Fleet Manager` role.
