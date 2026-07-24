# Architecture Overview

## Fleet Management System (`fleet_management`)

This document presents the architectural design, security model, data flow, logging infrastructure, and error handling framework.

---

## 🏛️ Layered Architecture Pattern

The system enforces a clean 5-tier layered architecture:

```
[ HTTP / Desk Client ]
         │
         ▼
[ API Layer ] ──> (@api_endpoint in fleet_management.api.base)
         │
         ▼
[ Validation Layer ] ──> (BaseValidator in fleet_management.validators.base_validator)
         │
         ▼
[ Service Layer ] ──> (BaseService in fleet_management.services.base_service)
         │
 ┌───────┴───────┐
 ▼               ▼
[ Permissions ]  [ Utilities & Logging ]
(evaluator.py)   (logger.py, exceptions.py)
```

---

## 🔐 Security & Permission Architecture

1. **Role-Based Access Control (`fleet_management.permissions.evaluator`)**:
   - Central `PermissionEvaluator` evaluates user roles dynamically using `frappe.get_roles()`.
   - Methods: `require_role(role_name)` and `require_any_role([roles])`.

2. **Operations & Audit Logging (`fleet_management.permissions.audit`)**:
   - Decorator `@audit_log("ACTION_NAME")` tracks execution of administrative procedures.
   - Document modification hook `audit_document_change` records doc updates silently in application log streams.

---

## 🪵 Central Logging Architecture

- Class `FleetLogger` wraps `frappe.logger` with structured JSON payloads.
- Automatic masking of sensitive dictionary keys (`password`, `secret`, `token`, `auth_header`, `jwt`).
- Exception backtraces logged automatically when exceptions occur.

---

## 🛑 Exception & Error Handling

All domain exceptions inherit from `FleetManagementError`:

| Exception Class | Default HTTP Status | Description |
| :--- | :--- | :--- |
| `FleetValidationError` | 422 Unprocessable Entity | Input parameter or entity validation failure |
| `FleetPermissionError` | 403 Forbidden | Missing required user role or scope |
| `FleetNotFoundError` | 404 Not Found | Requested entity or document not found |
| `FleetBusinessLogicError` | 409 Conflict | Invariant or state violation |
| `FleetExternalServiceError` | 502 Bad Gateway | Integration connection failure |
| `FleetRateLimitError` | 429 Too Many Requests | Endpoint rate limit exceeded |
