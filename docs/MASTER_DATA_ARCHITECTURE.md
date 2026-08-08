# Master Data Architecture Documentation

## Fleet Management System (`fleet_management`)

This document defines the production-grade **Master Data Architecture** for the Fleet Management System.

---

## 🏛️ Master Data Overview

The system provides master DocTypes (including `Fleet Company`, `Fleet Vehicle`, `Vehicle Category`, `Vehicle Brand`, `Vehicle Model`, `Fuel Type`, `Fuel Station`, `Maintenance Template`, `Maintenance Vendor`, etc.) designed for high scalability (100,000+ records) and multi-company enterprise operations.

```
+------------------+       +-------------------+       +--------------------+
|  Fleet Company   |<------|   Fleet Vehicle   |------>|Maintenance Template|
+------------------+       +-------------------+       +--------------------+
         |                           |                           |
         v                           v                           v
+------------------+       +-------------------+       +--------------------+
|  Vehicle Brand   |<------|   Vehicle Model   |------>|     Fuel Type      |
+------------------+       +-------------------+       +--------------------+
                                     |                           |
                                     v                           v
                           +-------------------+       +--------------------+
                           | Vehicle Category  |       |     Fuel Unit      |
                           +-------------------+       +--------------------+

+------------------+       +-------------------+       +--------------------+
| Maintenance Type |       | Expense Category  |       |    Fuel Station    |
+------------------+       +-------------------+       +--------------------+

+------------------+       +-------------------+       +--------------------+
|Maintenance Vendor|       |  Vehicle Colour   |       |   Distance Unit    |
+------------------+       +-------------------+       +--------------------+
```

---

## 📐 Entity Relationship (ER) Diagram (Text-Based)

```
[Vehicle Brand] (1) ───────< (N) [Vehicle Model] (N) >─────── (1) [Fuel Type] (N) >─────── (1) [Fuel Unit]
       │                                │
       v                                v
 (Search Index)                   (Search Index)

[Vehicle Category] ────> [Default Maintenance Interval (KM)]
[Maintenance Type] ────> [Default Cost Estimate & Duration]
[Expense Category] ────> [Fuel, Maintenance, Insurance, Registration, Tyres]
[Fuel Station]     ────> [Company Link, City, GPS Latitude & Longitude]
[Maintenance Vendor]───> [Rating (0.0 - 5.0), Preferred Vendor Flag]
[Vehicle Colour]   ────> [Colour Name, Hex Code Format #RRGGBB]
[Distance Unit]    ────> [Unit Name, Symbol, Conversion Multiplier to KM]
```

---

## 📋 Business Rule ID Matrix

| Rule ID | DocType | Field / Check | Description & Validation Constraint |
| :--- | :--- | :--- | :--- |
| **`MASTER-001`** | Vehicle Brand | `brand_code`, `brand_name` | Mandatory fields, unique constraint, code format. |
| **`MASTER-002`** | Vehicle Model | `vehicle_brand` + `model_name` | Brand + Model combination uniqueness constraint. |
| **`MASTER-003`** | Vehicle Model | `year` | Integer year range between 1900 and (Current Year + 1). |
| **`MASTER-004`** | Vehicle Model | `default_fuel_average` | Positive float value check (KM/L or MPG). |
| **`MASTER-005`** | Vehicle Category | `default_maintenance_interval` | Positive integer interval in KM. |
| **`MASTER-006`** | Fuel Type | `default_density` | Density positive float check (kg/L). |
| **`MASTER-007`** | Maintenance Type | `default_interval_km`, `default_cost` | Positive value constraints for intervals and cost. |
| **`MASTER-008`** | Fuel Station | `latitude`, `longitude` | GPS coordinates boundary checks (-90 to +90, -180 to +180). |
| **`MASTER-009`** | Maintenance Vendor | `rating` | Float rating boundary check between `0.0` and `5.0`. |
| **`MASTER-010`** | Vehicle Colour | `hex_code` | Hex color format regex check (`#RRGGBB` or `#RGB`). |
| **`MASTER-011`** | Distance Unit | `conversion_to_km` | Positive float multiplier relative to KM. |
| **`MASTER-012`** | Fuel Unit | `conversion_to_liters` | Positive float multiplier relative to Liters. |
| **`MASTER-013`** | Master DocTypes | `display_order` | Non-negative integer for list display order. |
| **`MASTER-014`** | Master DocTypes | `is_active` | Soft deletion / activation status toggle. |

---

## ⚡ Database Indexing Strategy (100,000+ Records)

1. **Unique Constraints & Primary Keys**:
   - `Vehicle Brand`: `brand_name`, `brand_code`
   - `Vehicle Category`, `Fuel Type`, `Maintenance Type`, `Expense Category`, `Maintenance Vendor`, `Vehicle Colour`, `Distance Unit`, `Fuel Unit`: `name`
2. **Compound Indexing**:
   - `Vehicle Model`: `(vehicle_brand, model_name)`
   - `Fuel Station`: `(company, city, is_active)`
3. **Filter Indexes**:
   - Every master table includes `is_active` in `in_standard_filter` for rapid query filtering.

---

## 🛠️ Reusable Base Document Controller (`BaseFleetDocument`)

All Master DocType Python controllers inherit from `BaseFleetDocument` (`fleet_management/utils/base_document.py`).

`BaseFleetDocument` automatically integrates:
- `TimestampMixin`
- `AuditMixin` (Silent audit log tracking on updates and submits)
- `StatusMixin`
- `PermissionMixin`
