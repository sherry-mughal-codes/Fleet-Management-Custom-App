# Fleet Automation & Notification Engine Architecture

## Overview

The **Fleet Automation & Notification Engine** is Phase 9 of the enterprise Fleet Management System built on Frappe Framework v15. It coordinates automated background routines, data integrity monitoring, notification routing, and policy enforcement across all fleet domains without duplicating business logic.

---

## Key Principles

1. **Service-Driven Automation**: All scheduled tasks and automation routines strictly invoke existing domain services (`VehicleService`, `AssignmentService`, `FuelService`, `MaintenanceService`, `MaintenanceDueEngine`, `FleetCostService`, `FleetHealthService`).
2. **Zero Business Logic Duplication**: Domain rules and calculations remain isolated within their respective business rule classes and domain services.
3. **Configurable Policies**: No thresholds, schedules, or notification flags are hardcoded. All settings are controlled via the `Fleet Settings` single DocType.
4. **Role-Based Notifications**: Administrative alerts and health reports strictly target authorized roles (`Fleet Manager`, `System Manager`, `Fleet Officer`) or configured escalation recipients.

---

## 1. Automation Engine (`FleetAutomationService`)

Located in `fleet_management/services/automation_service.py`.

### Responsibilities
- Coordinates multi-domain background automation routines.
- Executes maintenance checks, fuel anomaly detection, assignment expiration tracking, cost summary refreshes, and system health checks.

### Routines
- `run_maintenance_automation()`:
  - Detects upcoming maintenance within configurable lead distance (`default_reminder_distance_km`) or days (`maintenance_reminder_days`).
  - Detects overdue maintenance using `MaintenanceDueEngine`.
  - Dispatches maintenance due notifications to Fleet Managers.
- `run_fuel_automation()`:
  - Compares recent fuel entry averages against vehicle lifetime averages.
  - Flags fuel efficiency drops exceeding `fuel_anomaly_threshold` (default 20%).
  - Identifies active assigned vehicles with no fuel entries in over 30 days.
- `run_assignment_automation()`:
  - Flags assignments nearing `expected_return_date` (within 3 days).
  - Identifies overdue assignments past their return date.
- `run_cost_automation()`:
  - Triggers aggregated operating cost summary refreshes via `FleetCostService`.
- `run_health_monitoring_automation()`:
  - Invokes `FleetHealthService` and alerts System Managers / Escalation recipients if status is `Degraded` or `Critical`.

---

## 2. Scheduler Architecture

Located in `fleet_management/services/scheduler.py` and registered in `fleet_management/hooks.py`.

### Registered Scheduler Events
- **Daily**:
  - `scheduled_maintenance_check`
  - `scheduled_fuel_anomaly_check`
  - `scheduled_assignment_expiry_check`
  - `scheduled_fleet_automation_daily`
- **Hourly**:
  - `scheduled_maintenance_check`
- **Weekly**:
  - `scheduled_cost_refresh`
  - `scheduled_health_check`

### Enablement Guard
Every scheduler handler verifies `SettingsService.is_scheduler_enabled()` before proceeding. If disabled via `Fleet Settings`, execution is skipped safely.

---

## 3. Data Integrity & Health Monitoring (`FleetHealthService`)

Located in `fleet_management/services/health_service.py`.

### Verifications
1. **Odometer Consistency**:
   - Current odometer vs initial odometer checks (`current_odometer >= initial_odometer`).
   - Chronological fuel entry odometer and distance progression.
2. **Broken References**:
   - Orphaned assignments, fuel entries, or work orders referencing non-existent Vehicles, Employees, or Requests.
3. **Invalid Assignments**:
   - Detection of concurrent active assignments on the same vehicle (enforcing ASSIGN-001).
   - Active assignments on vehicles in maintenance or decommissioned state.
4. **Maintenance Links**:
   - Work order status and total cost sanity checks.
5. **Fuel Relationships**:
   - Fuel quantity vs maximum capacity limit (`max_fuel_capacity_validation`).
   - Non-positive fuel quantities or negative costs.

### Health Report Payload
```json
{
  "status": "Healthy | Degraded | Critical",
  "timestamp": "2026-07-25 12:00:00",
  "health_score": 95.0,
  "total_checks": 5,
  "total_issues": 1,
  "critical_issues": 0,
  "warning_issues": 1,
  "issues": [
    {
      "category": "Odometer Consistency",
      "severity": "Warning",
      "reference_doctype": "Fuel Entry",
      "reference_name": "FE-0001",
      "description": "Fuel Entry FE-0001 has negative distance since last fuel (-5.0)."
    }
  ]
}
```

---

## 4. Notification Engine (`FleetNotificationService`)

Located in `fleet_management/notifications/service.py`.

### Channels
- **Email Notifications**: Uses `frappe.sendmail` (respects `enable_email_notifications`).
- **In-App (Desk) Notifications**: Creates `Notification Log` records for target users (respects `enable_system_notifications`).

### Extension Hooks (Out of Scope for Active Transport)
Standardized handler methods prepared for future integration:
- `send_sms(recipients, message)` -> returns `{"status": "skipped", "channel": "sms"}`
- `send_whatsapp(recipients, message)` -> returns `{"status": "skipped", "channel": "whatsapp"}`
- `send_push(recipients, message)` -> returns `{"status": "skipped", "channel": "push"}`

---

## 5. Configuration Guide (`Fleet Settings`)

Managed via `Fleet Settings` DocType and accessed via cached `SettingsService`.

| Field Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enable_scheduler` | Check | `1` | Master toggle for background scheduler events |
| `enable_notifications` | Check | `1` | Master toggle for system & email notifications |
| `maintenance_reminder_days` | Int | `7` | Days prior to scheduled due date to generate reminders |
| `fuel_anomaly_threshold` | Float | `20.0` | Percentage drop in fuel efficiency triggering anomaly alerts |
| `health_check_schedule` | Select | `"Daily"` | Schedule frequency for system health checks (`Daily`, `Hourly`, `Weekly`) |
| `escalation_recipient` | Data | `""` | Escalation email address for critical health and system alerts |

---

## 6. Whitelisted REST APIs

Exposed in `fleet_management/api/automation_api.py`.

- `GET /api/method/fleet_management.api.automation_api.get_automation_status_api`
- `GET /api/method/fleet_management.api.automation_api.get_notification_status_api`
- `GET /api/method/fleet_management.api.automation_api.get_health_report_api`
- `GET /api/method/fleet_management.api.automation_api.get_scheduler_history_api`
- `POST /api/method/fleet_management.api.automation_api.run_automation_job_api` (Requires `Fleet Manager` or `System Manager` role)
