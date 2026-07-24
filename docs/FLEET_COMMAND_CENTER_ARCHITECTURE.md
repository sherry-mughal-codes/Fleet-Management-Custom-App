# Fleet Command Center, Analytics & Reporting Architecture Specification

## Fleet Management System (`fleet_management`)

This document defines the enterprise **Fleet Command Center, Analytics & Reporting Architecture Specification** (Phase 8).

---

## 🏛️ Command Center Overview

The **Fleet Command Center** acts as the central executive landing page and operational dashboard for the Fleet Management application. It provides complete fleet visibility in **under 30 seconds**.

```
[ User / Desk Workspace Landing Page ] ──> Custom Fleet Workspace & Dashboard Page
                                                       │
                                                       ▼
[ Whitelisted Analytics APIs ] ──> analytics_api.py (@api_endpoint)
                                                       │
                                                       ▼
[ FleetAnalyticsService ] ──> Aggregates Domain Metrics & Generates Alerts
             │
 ┌───────────┼────────────────────┬────────────────────┬───────────────────┐
 ▼           ▼                    ▼                    ▼                   ▼
[Vehicle]  [Assignment]      [Fuel Service]       [Maintenance]      [FleetCost]
Service    Service           (Average Engine)     (Due Engine)       Service
```

> **Key Design Mandates**:
> - **Zero Calculation Duplication**: All KPIs, smart alerts, charts, and report metrics consume existing service layer methods (`VehicleService`, `AssignmentService`, `FuelService`, `MaintenanceService`, `FleetCostService`).
> - **Multi-Company & Multi-Tenant**: Full filtering by `company`, date range, vehicle, driver, brand, and model.

---

## 📊 Workspace 7 Form Sections

1. **Section 1 – Header**: Company selector, Date range selector, Refresh button.
2. **Section 2 – KPI Cards**: Total Vehicles, Active Vehicles, Assigned Vehicles, Available Vehicles, Vehicles Under Maintenance, Overdue Maintenance, Monthly Fuel Cost, Monthly Maintenance Cost, Monthly Operating Cost.
3. **Section 3 – Smart Severity Alerts**:
   - `Critical`: Maintenance Overdue warnings.
   - `Warning`: Fuel-Locked vehicles.
   - `Information`: Available fleet capacity.
4. **Section 4 – Interactive Analytics Charts**:
   - Fuel vs. Maintenance Spend Breakdown.
   - Vehicle Status Distribution.
5. **Section 5 – Vehicle Health Table**:
   - Vehicle Number, Brand/Model, Current Odometer, Status, Fuel Average (KM/L), Fuel Spend, Maintenance Spend, Operating Cost, Cost per KM.
6. **Section 6 – Quick Action Buttons**:
   - Assign Vehicle, Add Fuel Entry, Create Maintenance Request, View Fuel History, View Maintenance History.
7. **Section 7 – Recent Activity Timeline**:
   - Aggregated activity feed from Fuel and Maintenance events.

---

## 📑 Production Script Reports

1. **`Vehicle Summary Report`**: Vehicle health, odometer, fuel average, and operating cost per KM.
2. **`Fuel Efficiency Report`**: Fuel entry history, fuel quantity, total cost, and calculated fuel economy (KM/L).
3. **`Maintenance Summary Report`**: Maintenance request history, type, priority, and status.
4. **`Fleet Cost Summary Report`**: Monthly and yearly company fleet operating spend (Fuel vs. Maintenance).
