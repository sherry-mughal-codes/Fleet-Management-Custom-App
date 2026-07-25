# Architecture Overview

## Fleet Management System (`fleet_management`)

This document presents the architectural design, security model, data flow, logging infrastructure, and error handling framework.

---

## 🏛️ Layered Architecture Pattern

[ HTTP / Desk Client ] <---> [ Whitelisted REST API Layer (automation_api.py, analytics_api.py) ]
         │
         ▼
[ Automation & Scheduler Layer ] ──> (FleetAutomationService, FleetHealthService, scheduler.py)
         │
         ▼
[ Domain Service Layer ] ──> (VehicleService, AssignmentService, FuelService, MaintenanceService, FleetCostService)
         │
         ▼
[ Validation & Business Rules ] ──> (BaseValidator, business_rules/)
         │
 ┌───────┴───────────────┐
 ▼                       ▼
[ Notifications & Logs ]  [ Settings & Security ]
(FleetNotificationService) (SettingsService, PermissionEvaluator)
```

---

## ⚙️ Fleet Settings Singleton & Redis Caching

`Fleet Settings` Single DocType is managed exclusively through `SettingsService`:
- Redis key: `fleet_management:settings`
- Auto-invalidation on `on_update` doc hook.
- Fallback defaults for uninitialized sites from `constants.py`.
- Configurable automation controls: scheduler toggles, notification channel toggles, maintenance lead time, fuel anomaly thresholds, health check schedules, escalation recipients.

---

## 🔐 Security & Permission Architecture

1. **Role-Based Access Control (`fleet_management.permissions.service`)**:
   - `PermissionService` & `PermissionEvaluator` verify user roles (`Fleet Manager`, `Fleet Officer`, `Fleet Driver`, etc.).
   - Methods: `require_role(role_name)` and `require_any_role([roles])`.

2. **Operations & Audit Logging (`fleet_management.services.audit_service`)**:
   - `AuditService` records document changes, user actions, IP addresses, and old/new value diffs.

---

## 🪵 Central Logging & Execution Timing

- Class `FleetLogger` wraps `frappe.logger` with structured JSON payloads.
- Log levels: `debug`, `info`, `warning`, `error`, `critical`.
- Context manager `logger.log_execution_time("action_name")` measures duration.
- Automatic masking of sensitive dictionary keys (`password`, `secret`, `token`, `auth_header`, `jwt`).

---

## 🛑 Domain Exception Hierarchy

All domain exceptions inherit from `FleetManagementError`:

| Exception Class | HTTP Status | Description |
| :--- | :--- | :--- |
| `FleetValidationError` / `ValidationError` | 422 | Input parameter or entity validation failure |
| `FleetPermissionError` / `PermissionError` | 403 | Missing required user role or scope |
| `FleetNotFoundError` / `NotFoundError` | 404 | Requested entity or document not found |
| `FleetBusinessLogicError` / `BusinessRuleError` | 409 | Invariant or state violation |
| `FleetConfigurationError` / `ConfigurationError` | 500 | Application setup error |
| `FleetDuplicateEntryError` / `DuplicateEntryError` | 409 | Duplicate record detected |
| `FleetExternalServiceError` | 502 | Integration connection failure |
| `FleetRateLimitError` | 429 | Endpoint rate limit exceeded |
