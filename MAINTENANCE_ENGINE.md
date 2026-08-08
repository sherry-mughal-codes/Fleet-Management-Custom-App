# Template-Driven Maintenance Engine Documentation

## Overview

Phase 11 Part 2 simplifies maintenance management by introducing a **single transactional document (`Maintenance Entry`)** and a **Template Master (`Maintenance Template`)**, replacing legacy multi-step workflows.

---

## 1. Document Architecture

### Maintenance Template (Master DocType)
- Defines preventive maintenance schedules mapped to **Vehicle Categories**.
- Contains child tables:
  - **`Maintenance Template Category`**: Vehicle categories (e.g., Sedan, Commercial, Pickup, SUV, Van).
  - **`Maintenance Schedule Line`**: Activity details:
    - `maintenance_type` (Link to `Maintenance Type`)
    - `interval_km` (Frequency in KM)
    - `priority` (Low, Medium, High, Critical)
    - `is_mandatory` (1 = Fuel Lock Enforced)
    - `grace_distance` (Allowed overrun in KM)

### Maintenance Entry (Submittable Transaction)
- Fields: `assignment`, `vehicle`, `employee`, `maintenance_date`, `current_odometer`, `maintenance_template`, `maintenance_type`, `vendor`, `invoice_number`, `rate`, `qty`, `total_cost`, `remarks`, `attachments`.
- `total_cost` is read-only and automatically calculated as `rate × qty`.

---

## 2. Category & Vehicle Level Template Auto-Resolution

When creating a `Maintenance Entry` or evaluating Maintenance Locks on `Fuel Entry`:
$$\text{Fleet Vehicle} \longrightarrow \text{Fleet Vehicle.maintenance\_template} \longrightarrow \text{Category Fallback} \longrightarrow \text{Maintenance Template}$$

The system resolves the active template directly linked on `Fleet Vehicle.maintenance_template` (e.g. `Sedan Standard Maintenance Template` or `Commercial Heavy Maintenance Template`) or falls back to category-mapped templates.

---

## 3. Servicing Completion & Partial Reset

When a `Maintenance Entry` is submitted:
1. Permanent history record is created.
2. **ONLY the completed maintenance items** in the child table are reset.
3. Unrelated maintenance activities retain their previous servicing baselines.
4. Next due maintenance odometer and vehicle health scores are recalculated.
5. If all mandatory items are clear, **Fuel Lock is automatically released**.
