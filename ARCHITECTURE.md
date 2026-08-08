# Fleet Management System - Enterprise System Architecture (Frappe v15)

## Overview & Architectural Principles

The **Fleet Management System** is built on top of **Frappe Framework v15** following SOLID principles, Clean Architecture, and Domain-Driven Design (DDD). Business logic, state calculations, availability checks, cost aggregations, and notifications are fully decoupled from document controllers into single-responsibility **Service Managers**.

---

## 1. Domain Service Layer (`fleet_management/services/`)

The application is governed by dedicated domain service managers:

1. **`VehicleService`** (`vehicle_service.py`):
   - Single source of truth for dynamic `Fleet Vehicle` registration, status management, and operational summary sync.
   - `Fleet Vehicle.status` is managed deterministically via single state-machine transition handlers.

2. **`AssignmentService`** (`assignment_service.py`):
   - Manages vehicle assignment availability, handover, return, and historical tracking (`Vehicle Assignment`).
   - Enforces submittable assignment workflows (`docstatus = 1`, `status = "Assigned"`).

3. **`FuelService`** (`fuel_service.py`):
   - Handles automated fuel entry creation, submission, and validation (`Rate Per Litre × Litres`).
   - Enforces Mandatory Maintenance Fuel Locks (`FUEL-008`).

4. **`MaintenanceManager`** (`maintenance_manager.py`):
   - Central engine for template-driven `Maintenance Entry` records.
   - Dynamic template auto-resolution via `Fleet Vehicle.maintenance_template` or category mapping.
   - Calculates due, overdue, and remaining distance per template schedule line.
   - Resets ONLY completed maintenance items upon servicing.

5. **`FleetCostService`** (`fleet_cost_service.py`):
   - Calculates aggregated fuel spend, maintenance costs, and fleet Cost Per KM.

6. **`SettingsService`** (`settings_service.py`):
   - Resolves global settings defaults from `Fleet Settings` and default `Fleet Company`.

7. **`NotificationManager`** (`notification_manager.py`):
   - Handles role-based notification dispatches for assignment handovers, returns, maintenance due/overdue, and fuel locks.

8. **`DemoDataService`** (`demo_data_service.py`):
   - Generates realistic Pakistani logistics datasets for *ABC Logistics (Private) Limited*.
   - Safely removes transactional data (`Fuel Entry`, `Maintenance Entry`, `Vehicle Assignment`) while preserving master data (`Fleet Vehicle`, `Fleet Company`, Templates).

---

## 2. Dynamic Vehicle State Calculation Order

Vehicle operational status is evaluated deterministically by `VehicleStateManager`:

1. **Terminal Statuses**: `Retired`, `Scrapped`, `Sold`, `Out of Service`, `Archived`.
2. **Under Maintenance**: Active submitted work order or vehicle flagged under servicing.
3. **Fuel Locked / Overdue Maintenance**: Mandatory template line interval + grace distance exceeded by odometer.
4. **Maintenance Due**: `current_odometer >= next_maintenance_due_odometer`.
5. **Assigned**: Active submitted `Vehicle Assignment` without return date.
6. **Available**: Passed all checks and ready for deployment.

---

## 3. Mandatory Fuel Lock Engine

Submitting a `Fuel Entry` evaluates active template schedule lines. If any mandatory item is overdue:
```
Fuel Entry cannot be submitted.
The following maintenance items are overdue:
• Engine Oil Change (Last Done: 12,000 KM | Current: 17,350 KM | Interval: 5,000 KM | Exceeded by: 350 KM)
Complete the required maintenance before recording additional fuel.
```
