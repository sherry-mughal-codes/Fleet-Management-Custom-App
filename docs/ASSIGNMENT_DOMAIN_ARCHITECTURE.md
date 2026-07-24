# Assignment Domain Architecture & Business Logic Specification

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Assignment Domain Architecture, Handover & Return Business Logic** (Phase 4 – Part 3).

---

## 🏛️ Assignment Domain Overview

The Assignment Subsystem represents the central operational session linking **Vehicle** to **Employee**, **Handover**, **Usage**, and **Return**.

```
                           +-------------------+
                           |      Vehicle      |
                           +-------------------+
                                     | 1
                                     |
                                     | N
+------------------+       +--------------------+       +-----------------------+
|     Employee     | <───> | Vehicle Assignment | <───> |  Handover Inspection  |
+------------------+ 1   N +--------------------+ 1   1 +-----------------------+
                                 │   │   │
                  ┌──────────────┼───┼───┼──────────────┐
                  │              │   │   │              │
                  v              v   v   v              v
           [Fuel Entries] [Maintenance] [Expenses] [Trip Logs] [GPS Tracks]
           (Future Phase) (Future Phase)(Future Phase)(Future Phase)(Future Phase)
```

---

## 🔄 Sequence Diagrams (Handover & Return Workflows)

### Vehicle Handover Sequence
```
[ User / Desk UI ] ──( Handover Action )──> [ AssignmentService.assign_vehicle() ]
                                                    │
                                                    ├── 1. Validate ASSIGN-001 (Vehicle Available)
                                                    ├── 2. Validate ASSIGN-004 (Opening Odometer >= Vehicle Odometer)
                                                    ├── 3. Set status = "Assigned"
                                                    │
                                                    ▼
                                    [ VehicleService.change_status() ]
                                                    │
                                                    ├── Set Vehicle.status = "Assigned"
                                                    └── Set Vehicle.current_employee = Employee
```

### Vehicle Return Sequence
```
[ User / Desk UI ] ──( Return Action )───> [ AssignmentService.return_vehicle() ]
                                                    │
                                                    ├── 1. Validate ASSIGN-005 (Closing Odometer >= Opening Odometer)
                                                    ├── 2. Calculate distance_travelled = Closing - Opening
                                                    ├── 3. Update Vehicle.current_odometer = Closing Odometer
                                                    ├── 4. Set Vehicle.current_employee = None
                                                    ├── 5. Set status = "Returned"
                                                    │
                                                    ▼
                                    [ VehicleService.change_status() ]
                                                    │
                                                    └── Set Vehicle.status = "Available"
```

---

## 📋 Business Rule ID Matrix (`ASSIGN-001` .. `ASSIGN-010`)

| Rule ID | Rule Name | Description & Invariant Constraint |
| :--- | :--- | :--- |
| **`ASSIGN-001`** | Single Active Assignment | A Vehicle may have only one active Assignment (`Assigned` or `In Use`). |
| **`ASSIGN-002`** | Valid Vehicle | An Assignment requires a valid Vehicle reference. |
| **`ASSIGN-003`** | Valid Employee | An Assignment requires a valid Employee reference. |
| **`ASSIGN-004`** | Opening Odometer | Opening Odometer must be non-negative and >= current Vehicle Odometer. |
| **`ASSIGN-005`** | Closing Odometer | Closing Odometer must be >= Opening Odometer. Prevents mileage rollback. |
| **`ASSIGN-006`** | Service Status Mutation | Vehicle status changes occur strictly via `VehicleService.change_status()`. |
| **`ASSIGN-007`** | Cancellation Lock | Cancelled Assignments cannot be re-activated. |
| **`ASSIGN-008`** | Read-Only Closed Lock | Closed Assignments are read-only except for authorized administrative audit edits. |
| **`ASSIGN-009`** | Session Closure | Returned / Closed Assignments cannot receive additional operational entries. |
| **`ASSIGN-010`** | Company Isolation | Vehicle company and Assignment company must match. |
