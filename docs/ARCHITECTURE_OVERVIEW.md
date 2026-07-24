# Architecture Overview

## Fleet Management System (`fleet_management`)

This document presents the architectural design, security model, data flow, logging infrastructure, and error handling framework.

---

## 🏛️ Layered Architecture Pattern

The system enforces a clean 6-tier layered architecture:

```
[ HTTP / Desk Client ]
         │
         ▼
[ API Layer ] ──> (@api_endpoint, api/responses.py)
         │
         ▼
[ Validation Layer & Rules ] ──> (BaseValidator, common_validators.py, business_rules/)
         │
         ▼
[ Service Layer ] ──> (BaseService, SettingsService, AuditService, NotificationService)
         │
 ┌───────┴───────────────┐
 ▼                       ▼
[ Permissions & Mixins ] [ Utilities & Logging ]
(PermissionService)      (logger.py, exceptions.py, helpers.py, constants.py, enums.py)
```

---

## ⚙️ Fleet Settings Singleton & Redis Caching

`Fleet Settings` Single DocType is managed exclusively through `SettingsService`:
- Redis key: `fleet_management:settings`
- Auto-invalidation on `on_update` doc hook.
- Fallback defaults for uninitialized sites from `constants.py`.

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
