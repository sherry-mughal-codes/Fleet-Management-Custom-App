# Enterprise Administrator Guide

## Fleet Management System v1.0.0 (Frappe Framework v15)

---

## 1. System Requirements & Overview

The **Fleet Management System** is an enterprise-grade custom app built on Frappe Framework v15. It provides end-to-end operational governance across Vehicle Lifecycles, Driver Assignments, Fuel Intelligence, Maintenance Work Orders, Operating Costs, Command Center Analytics, and Automated Background Jobs.

### Server Requirements
- **OS**: Linux (Ubuntu 22.04 LTS recommended) / Docker Containers
- **Python**: 3.10+
- **Database**: MariaDB 10.6+
- **In-Memory Cache**: Redis 7.0+
- **Frappe Bench**: v15.0.0+

---

## 2. Installation & Site Deployment

### A. Docker Compose Deployment (Recommended)
```bash
git clone https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git
cd Fleet-Management-Custom-App
docker compose up -d --build
```

### B. Standard Frappe Bench Installation
```bash
cd ~/frappe-bench
bench get-app fleet_management https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git
bench --site site1.local install-app fleet_management
bench --site site1.local migrate
```

---

## 3. Role-Based Access Control (RBAC) & Permissions

The system defines 7 production security roles out of the box:

| Role Name | Scope & Responsibilities |
| :--- | :--- |
| **Fleet Manager** | Full operational control: approve assignments, manage vehicles, override locks, view costs, trigger manual automations |
| **Fleet Officer** | Day-to-day operations: manage assignments, submit fuel entries, inspect requests |
| **Fleet Dispatcher** | Driver & vehicle dispatching, handover/return verification |
| **Fleet Driver** | Self-service view: active vehicle assignment, submit fuel receipts |
| **Fleet Mechanic** | Vendor & Work Order updates, task completions |
| **Fleet Auditor** | Read-only access to audit logs, costs, and compliance reports |
| **Fleet User** | Basic viewing permissions |

---

## 4. Configuring Global Fleet Settings

Access **Fleet Settings** via Desk search or `Fleet Management > Fleet Settings`.

- **Maintenance Interval (KM)**: Default odometer distance between required services (default `5000 KM`).
- **Reminder Distance (KM)**: Lead distance triggering maintenance warnings (default `500 KM`).
- **Fuel Lock Enforcement**: Lock fuel entry submissions when vehicle maintenance is overdue.
- **Max Fuel Capacity**: Upper threshold validation on fuel entry submissions (default `500 L`).
- **Automation Scheduler Toggle**: Global toggle to enable/disable background scheduler jobs.
- **Notification Toggles**: Toggles for Email, In-App System Logs, and Escalation recipients.

---

## 5. Scheduler & Background Operations

Scheduled tasks run automatically via Frappe background workers:

- **Daily**:
  - `scheduled_maintenance_check`: Detects upcoming and overdue maintenance.
  - `scheduled_fuel_anomaly_check`: Flags fuel efficiency drops.
  - `scheduled_assignment_expiry_check`: Warns on expiring assignments.
  - `scheduled_fleet_automation_daily`: Executes master automation suite.
- **Hourly**:
  - `scheduled_maintenance_check`: Rapid maintenance lock refresh.
- **Weekly**:
  - `scheduled_cost_refresh`: Refreshes aggregated fleet operating spend.
  - `scheduled_health_check`: Runs data integrity audit via `FleetHealthService`.

To manually trigger scheduler background workers:
```bash
bench --site site1.local doctor
bench --site site1.local trigger-scheduler-event daily
```

---

## 6. Troubleshooting & Diagnostics

- **Redis Cache Clearing**:
  ```bash
  bench --site site1.local clear-cache
  ```
- **System Health Report**:
  Execute `FleetHealthService().run_health_check()` or invoke `GET /api/method/fleet_management.api.v1.automation_api.get_health_report_api`.
- **Log Locations**:
  - Application logs: `logs/fleet_management.log`
  - Scheduler logs: `logs/scheduler.log`
