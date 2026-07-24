# Vehicle Digital Asset & Document Management Architecture

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Digital Asset & Document Management Subsystem** (Phase 3 – Part 3).

---

## 🏛️ Digital Asset Subsystem Overview

The Digital Asset Management subsystem handles unlimited vehicle documents (Registration, Insurance, Road Tax, Fitness, Warranty, Purchase Invoices, Permits, Emission, Leases) and image galleries (Front, Rear, Left, Right, Interior, Dashboard, Engine, Damage, Other).

```
                      +-------------------+
                      |      Vehicle      |
                      +-------------------+
                         |             |
           1:N (Documents)             1:N (Images)
                         |             |
                         v             v
   +-------------------------+   +----------------------+
   | Vehicle Document Detail |   | Vehicle Image Detail |
   +-------------------------+   +----------------------+
```

---

## 📋 Asset Rule ID Matrix (`ASSET-001` .. `ASSET-008`)

| Rule ID | Subsystem | Validation Constraint / Action |
| :--- | :--- | :--- |
| **`ASSET-001`** | Document | Expiry Date must be greater than or equal to Issue Date. |
| **`ASSET-002`** | Document | Reminder Days must be a non-negative integer. |
| **`ASSET-003`** | Document | Mandatory attachment file when Document status is `Active`. |
| **`ASSET-004`** | Document | Document Number must be unique per Vehicle for a given Document Category. |
| **`ASSET-005`** | Gallery Image | Single Primary Image enforcement: resets all other rows to `is_primary=0`. |
| **`ASSET-006`** | Gallery Image | Display Order must be a non-negative integer. |
| **`ASSET-007`** | Document | Remaining days calculation logic and status derivation. |
| **`ASSET-008`** | Document / Image | Validates document categories and image categories against domain Enums. |

---

## ⚡ Single Primary Image Auto-Validation

When multiple image rows in `Vehicle Image Detail` are flagged with `is_primary = 1`, `enforce_single_primary_image()` automatically retains `is_primary = 1` on the first primary selection and resets all subsequent rows to `is_primary = 0`.

---

## 🚀 Extension Points for Future Phases

1. **Future Mobile App Upload**:
   - `VehicleService.register_vehicle()` and `create_vehicle` API accept base64 or direct Frappe file attachments cleanly.
2. **Future REST APIs**:
   - `get_vehicle_documents`, `get_vehicle_images`, and `get_vehicle_asset_summary` Whitelisted APIs provide standardized JSON envelopes.
3. **Future Insurance & Registration Tracking**:
   - Child records link seamlessly to future operational Insurance policy or Vehicle Registration DocTypes.
4. **Future CAD, GPS & PDF Attachments**:
   - `attachment` field supports any mime type without database schema modifications.
