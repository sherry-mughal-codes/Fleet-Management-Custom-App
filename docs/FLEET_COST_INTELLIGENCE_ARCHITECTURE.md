# Fleet Cost Intelligence Domain Architecture & Design Specification

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Fleet Cost Intelligence Domain Architecture & Design Specification** (Phase 7).

---

## 🏛️ Cost Intelligence Overview

The Fleet Cost Intelligence Subsystem acts as a non-redundant financial aggregation engine. It derives all operating costs directly from primary operational transaction logs (`Fuel Entry` and `Maintenance Entry`).

> **Key Architectural Mandates**:
> - **NO Generic Expense DocType**: Prevents duplicate data entry.
> - **System-Calculated & Read-Only**: Costs are reproducible and read-only (`COST-003`).
> - **Strict Exclusion of Invalid Records**: Draft, Cancelled, or rejected entries are excluded (`COST-004`, `COST-005`).

```
                       +-----------------------------+
                       |      Fuel Entry             |
                       | (docstatus == 1)            |
                       +-----------------------------+
                                      │
                                      ├── Total Fuel Cost
                                      │
                                      ▼
+---------------------+     +-----------------------------+     +------------------------+
|    Fleet Vehicle    | <── |      FleetCostService       | ──> |  Vehicle Assignment    |
| (Financial Summary) |     |  (System-Calculated Engine) |     | (Period Operating Cost)|
+---------------------+     +-----------------------------+     +------------------------+
                                      ▲
                                      │
                                      ├── Total Maintenance Cost
                                      │
                       +-----------------------------+
                       |     Maintenance Entry       |
                       | (docstatus == 1)            |
                       +-----------------------------+
```

---

## 📋 Business Rule ID Matrix (`COST-001` .. `COST-006`)

| Rule ID | Rule Name | Description & Invariant Constraint |
| :--- | :--- | :--- |
| **`COST-001`** | Primary Fuel Cost Source | Fuel costs originate only from `Fuel Entry` records (`docstatus == 1`). |
| **`COST-002`** | Primary Maintenance Cost Source | Maintenance costs originate only from submitted `Maintenance Entry` records. |
| **`COST-003`** | System-Calculated Read-Only | All cost summaries are read-only and calculated automatically by `FleetCostService`. |
| **`COST-004`** | Cancelled Document Exclusion | Cancelled documents (`docstatus == 2`) are strictly excluded from calculations. |
| **`COST-005`** | Submitted / Confirmed Only | Only submitted or confirmed records contribute to cost calculations. |
| **`COST-006`** | Validated Cost Per KM | Cost per kilometre is calculated using validated odometer progression (`operating_cost / distance`). |
