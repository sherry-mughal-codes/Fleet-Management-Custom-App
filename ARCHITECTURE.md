# Fleet Management System - Enterprise System Architecture (Frappe v15)

## Overview & Architectural Principles

The **Fleet Management System** is built on top of **Frappe Framework v15** following SOLID principles, Clean Architecture, and Domain-Driven Design (DDD). Business logic, state calculations, availability checks, cost aggregations, and notifications are fully decoupled from document controllers into single-responsibility **Service Managers**.

---

## 1. Domain Service Layer (`fleet_management/services/`)

The application is governed by 10 dedicated domain service managers:

1. **`VehicleStateManager`** (`vehicle_state_manager.py`):
   - Single source of truth for dynamic vehicle status calculation (`Available`, `Assigned`, `Maintenance Due`, `Under Maintenance`, `Retired`).
   - `Vehicle.status` is strictly read-only in the UI.

2. **`AssignmentManager`** (`assignment_manager.py`):
   - Manages vehicle assignment availability, handover, return, and historical tracking.
   - Enforces atomic database row locks (`SELECT ... FOR UPDATE`) to prevent race conditions during concurrent assignment submissions.

3. **`FuelManager`** (`fuel_manager.py`):
   - Handles automated fuel entry creation (`Rate Per Litre × Litres`).
   - Enforces Mandatory Maintenance Fuel Locks.
   - Handles total transaction reversal on document cancellation.

4. **`MaintenanceManager`** (`maintenance_manager.py`):
   - Central engine for template-driven `Maintenance Entry` records.
   - Category-based maintenance template auto-resolution.
   - Calculates due, overdue, and remaining distance per template schedule line.
   - Resets ONLY completed maintenance items upon servicing.

5. **`MaintenanceTemplateManager`** (`maintenance_template_manager.py`):
   - Manages maintenance template master definitions and activity schedules.

6. **`CostManager`** (`cost_manager.py`):
   - Calculates aggregated fuel spend, maintenance costs, and fleet Cost Per KM.

7. **`DashboardManager`** (`dashboard_manager.py`):
   - Centralized refresh engine for Desk Workspace Number Cards, Charts, and Quick Links.

8. **`NotificationManager`** (`notification_manager.py`):
   - Handles role-based notification dispatches for assignment handovers, returns, maintenance due/overdue, and fuel locks.

9. **`ValidationManager`** (`validation_manager.py`):
   - Centralized validation rules for duplicate registrations, VINs, and odometer readings.

10. **`DemoDataManager`** (`demo_data_manager.py` / `demo_data_service.py`):
    - Generates realistic Pakistani logistics datasets for *ABC Logistics (Private) Limited*.

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
