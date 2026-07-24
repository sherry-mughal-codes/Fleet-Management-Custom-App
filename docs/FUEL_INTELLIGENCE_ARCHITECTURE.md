# Fuel Intelligence Domain Architecture & Business Logic Specification

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Fuel Intelligence Domain Architecture, Engine & Business Logic** (Phase 5 – Part 3).

---

## 🏛️ Fuel Subsystem Overview

The Fuel Subsystem acts as an operational session transaction engine linking **Vehicle**, **Assignment**, **Employee**, **Fuel Station**, and **Financial Spend**.

```
                          +--------------------+
                          |      Vehicle       |
                          +--------------------+
                                    │ 1
                                    │
                                    │ N
+-------------------+     +--------------------+     +-------------------+
| VehicleAssignment | <─> |     Fuel Entry     | <─> |  Employee / User  |
+-------------------+ 1 N +--------------------+ N 1 +-------------------+
                                    │ N
                                    │
                                    │ 1 (Future)
                          +--------------------+
                          |    Fuel Station    |
                          +--------------------+
```

---

## 🔄 Fuel Intelligence Processing & Calculation Sequence

```
[ Fuel Entry Payload ] ──> 1. MaintenanceLockService (FUEL-008)
                                   │
                                   ├── Priority 1: Vehicle.maintenance_interval_km
                                   ├── Priority 2: FleetSettings.default_maintenance_interval_km
                                   └── Checks Vehicle.status == "Under Maintenance"
                                   │
                                   ▼
                           2. Odometer Integrity Engine (FUEL-004)
                                   │
                                   ├── Validates odometer >= current vehicle odometer
                                   └── Prevents mileage rollback
                                   │
                                   ▼
                           3. FuelAverageService (FUEL-007)
                                   │
                                   ├── distance_travelled = odometer - previous_fuel_odometer
                                   └── fuel_average = distance_travelled / fuel_qty (KM/L)
                                   │
                                   ▼
                           4. Vehicle & Assignment Statistics Updates (FuelService)
                                   │
                                   ├── Updates Vehicle.current_odometer & last_fuel_average
                                   └── Updates Assignment.total_fuel_qty & total_fuel_cost
                                   │
                                   ▼
                           5. Event Dispatcher & Audit Logging (FuelEventDispatcher)
```

---

## 📋 Business Rule ID Matrix (`FUEL-001` .. `FUEL-010`)

| Rule ID | Rule Name | Description & Invariant Constraint |
| :--- | :--- | :--- |
| **`FUEL-001`** | Vehicle Required | Vehicle reference is required and must exist. |
| **`FUEL-002`** | Positive Fuel Quantity | Fuel quantity (liters/gallons) must be greater than zero. |
| **`FUEL-003`** | Positive Total Cost | Total cost must be greater than zero. |
| **`FUEL-004`** | Odometer Advancement | Odometer reading must be >= current Vehicle Odometer. |
| **`FUEL-005`** | Duplicate Entry Check | Duplicate fuel entries (same vehicle, same date, same odometer, same qty) are prohibited. |
| **`FUEL-006`** | Assignment Policy Check | Vehicle must have an active assignment when assignment policy is enforced. |
| **`FUEL-007`** | System Fuel Economy | Fuel average (KM/L, L/100KM, MPG) is system-calculated automatically (`distance / qty`). |
| **`FUEL-008`** | Maintenance Lock | Fuel entry is blocked when vehicle is `Under Maintenance` or maintenance is overdue. |
| **`FUEL-009`** | Cancelled Entry Exclusion | Cancelled fuel entries cannot affect averages or odometer progression. |
| **`FUEL-010`** | Multi-Company Isolation | Fuel Entry company must match Vehicle company. |
