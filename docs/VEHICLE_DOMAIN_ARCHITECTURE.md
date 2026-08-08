# Vehicle Domain Architecture & Implementation Specification

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Vehicle Domain Architecture, Vehicle DocType Implementation & Lifecycle Engine** (Phase 3 – Part 4).

---

## 🏛️ Vehicle Domain Architecture & Single Source of Truth

The Vehicle Domain strictly decouples DocType definition from business logic, validation, event dispatching, and security:

```
[ Client / Desk Screen ] ──> Form Script (fleet_vehicle.js: Quick actions & brand filtering)
         │
         ▼
[ API Layer ] ──> (fleet_management.api.vehicle_api: change_vehicle_status, search_vehicles, get_vehicle_summary)
         │
         ▼
[ Validation Layer ] ──> (fleet_management.validators.vehicle_validator: Rule IDs VEH-001..VEH-010)
         │
         ▼
[ VehicleService (Single Source of Truth) ] ──> change_status(vehicle_id, new_status)
         │
 ┌───────┴────────────────────────┬─────────────────────────┐
 ▼                                ▼                         ▼
[ Event Dispatcher ]      [ Business Invariants ]   [ Security & Permissions ]
(vehicle_events.py)       (vehicle_rules.py)        (vehicle_permission.py)
```

> **Single Source of Truth Rule**: All status mutations must occur strictly via `VehicleService.change_status()`. Direct field overrides bypass validation and are restricted.

---

## 🔄 13-State Vehicle Lifecycle State Machine

```
                                ┌─────────────────────────────────────────────────────────────────┐
                                │                                                                 │
                                ▼                                                                 │
[Draft] ──> [Available] ──────> [Assigned]                                                        │
                │                  │                                                              │
                ├───> [Reserved] ──┘                                                              │
                │                                                                                 │
                ├───> [Maintenance Due] ──> [Under Maintenance] ──> [Inspection] ──> [Available]   │
                │                                                                                 │
                └───> [Out of Service] ───────────────────────────────────────────────────────────┤
                           │                                                                      │
                           ├───> [Inactive] ──> [Archived] ───────────────────────────────────────┘
                           ├───> [Sold]     ──> [Archived]
                           └───> [Scrapped] ──> [Archived]
```

### Complete 13 Lifecycle States
1. `Draft`
2. `Available`
3. `Reserved`
4. `Assigned`
5. `Maintenance Due`
6. `Under Maintenance`
7. `Inspection`
8. `Out of Service`
9. `Inactive`
10. `Sold`
11. `Scrapped`
12. `Archived`

---

## 📋 Business Invariant Rule ID Catalog (`VEH-001` .. `VEH-010`)

| Rule ID | Rule Name | Description & Invariant Constraint |
| :--- | :--- | :--- |
| **`VEH-001`** | Assignment Eligibility | Vehicle cannot be assigned unless status is `Available`. |
| **`VEH-002`** | Fueling Maintenance | Vehicle cannot receive fuel while `Under Maintenance`. |
| **`VEH-003`** | Maintenance Due Lock | Vehicle cannot receive fuel if Maintenance Due lock is enabled. |
| **`VEH-004`** | Archival Assignment | Vehicle cannot be Archived while currently `Assigned`. |
| **`VEH-005`** | Scrap Assignment | Vehicle cannot be Scrapped while currently `Assigned`. |
| **`VEH-006`** | Service Mutation | Status changes must occur strictly through `VehicleService.change_status()`. |
| **`VEH-007`** | Registration Uniqueness | Registration / License Plate number must be unique per Company. |
| **`VEH-008`** | VIN Format | VIN must contain exactly 17 uppercase alphanumeric characters (excluding I, O, Q). |
| **`VEH-009`** | Initial Odometer | Initial Odometer reading must be non-negative. |
| **`VEH-010`** | Calculation Safety | Aggregated financial and odometer totals use safe float and zero-division helpers. |

---

## 🎯 Quick Actions & Desk Button Architecture

- **Assign Vehicle**: Triggers vehicle assignment dialog (Subsystem integration point).
- **Record Fuel**: Opens fuel entry dialog (Subsystem integration point).
- **Record Maintenance**: Opens service log dialog (Subsystem integration point).
- **View Timeline**: Displays chronological activity log timeline for target vehicle.
- **Change Status**: Opens state-machine compliant status transition modal.
