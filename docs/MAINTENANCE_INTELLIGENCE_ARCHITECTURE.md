# Maintenance Intelligence Domain Architecture & Engine Specification

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Maintenance Intelligence Domain Architecture, Engine & Business Logic** (Phase 6 – Part 3).

---

## 🏛️ Maintenance Subsystem Overview

The Maintenance Subsystem manages scheduled preventive maintenance, unscheduled corrective repairs, emergency work orders, and recurring service plans.

```
                                  +--------------------+
                                  |      Vehicle       |
                                  +--------------------+
                                            │ 1
                                            │
                                            │ N
+-------------------------+       +--------------------+       +------------------------+
| Maintenance Task        | <───> | Maintenance        | <───> |  Handover / Assignment |
| Template (Master)       | 1   N | Request / Order    | 1  0..1+------------------------+
+-------------------------+       +--------------------+
                                            │ 1
                                            │ N
                                            ▼
                                  [ Maintenance Task ]
                                     (Child Table)
```

---

## 🔄 Maintenance Completion & Fuel Lock Removal Sequence

```
[ Maintenance Work Order Completed ]
                 │
                 ├── 1. Financial Cost Calculation Engine
                 │      (labour + parts + external + tax - discount = total_cost)
                 │
                 ├── 2. MaintenanceDueEngine (Priority Hierarchy: Vehicle -> Override -> Plan -> Settings)
                 │      (next_due_odometer = completion_odometer + interval_km)
                 │      (next_due_date = completion_date + interval_days)
                 │
                 ├── 3. Central Odometer Verification Engine
                 │      (completion_odometer >= vehicle.current_odometer)
                 │
                 ├── 4. Vehicle Statistics & Status Update (VehicleService)
                 │      (Vehicle.last_maintenance_date, Vehicle.last_maintenance_odometer)
                 │      (VehicleService.change_status(vehicle_id, VehicleStatus.AVAILABLE)) ──> Removes Fuel Lock!
                 │
                 ├── 5. Assignment Statistics Update
                 │      (Assignment.latest_maintenance_date, Assignment.maintenance_count)
                 │
                 └── 6. Event Dispatcher & Audit Logging (MaintenanceEventDispatcher)
```

---

## 📋 Business Rule ID Matrix (`MAINT-001` .. `MAINT-010`)

| Rule ID | Rule Name | Description & Invariant Constraint |
| :--- | :--- | :--- |
| **`MAINT-001`** | Vehicle Required | Vehicle reference is required and must exist. |
| **`MAINT-002`** | Interval Required | Maintenance interval (distance or time) is required for scheduled service plans. |
| **`MAINT-003`** | Completion Odometer Check | Completion odometer cannot be lower than current vehicle odometer (`completion_odometer >= vehicle.current_odometer`). |
| **`MAINT-004`** | Automated Next Due | Next due distance and date are calculated automatically by `MaintenanceDueEngine`. |
| **`MAINT-005`** | Fuel Entry Lock | Fuel Entry is blocked when Maintenance Lock is active (`VehicleStatus.UNDER_MAINTENANCE` or overdue). |
| **`MAINT-006`** | Lock Removal | Maintenance completion removes Maintenance Lock (updates `Vehicle.status` back to `Available` via `VehicleService.change_status()`). |
| **`MAINT-007`** | Non-Decreasing Odometer | Completion odometer reading cannot be less than previous odometer reading. |
| **`MAINT-008`** | Read-Only Completed | Completed maintenance records are read-only except for authorized administrative audits. |
| **`MAINT-009`** | Status Mutation | Starting a work order transitions `Vehicle.status` to `Under Maintenance` via `VehicleService.change_status()`. |
| **`MAINT-010`** | Multi-Company Isolation | Maintenance record company must match Vehicle company. |
