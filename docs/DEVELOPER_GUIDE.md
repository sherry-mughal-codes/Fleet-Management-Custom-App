# Enterprise Developer Guide

## Fleet Management System v1.0.0 (Frappe Framework v15)

---

## 1. Architecture Overview

The system strictly adheres to a **6-Tier Layered Architecture Pattern**:

```
[ Whitelisted REST API Layer (api/v1/) ]
                  │
                  ▼
[ Automation & Scheduler Layer (services/automation_service.py) ]
                  │
                  ▼
[ Domain Service Layer (services/vehicle_service.py, assignment_service.py, etc.) ]
                  │
                  ▼
[ Validation & Invariant Rules (validators/, business_rules/) ]
                  │
                  ▼
[ Base Layer (BaseService, BaseValidator, SettingsService, PermissionEvaluator) ]
```

### Architectural Principles
1. **Single Source of Truth**: `VehicleService` exclusively manages Vehicle state transitions and core statistics.
2. **Domain Isolation**: Business rules are encapsulated in `business_rules/` and inherit from `BaseBusinessRule`.
3. **No Logic Duplication**: Schedulers and automations delegate directly to domain services.

---

## 2. Developer Workspace Setup

### Local Development Environment
```bash
# 1. Clone repository
git clone https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git

# 2. Start Docker stack
docker compose up -d

# 3. Access backend shell
docker compose exec backend bash
```

---

## 3. Creating Custom Business Rules

To add a new invariant business rule:

1. Create a rule class inheriting from `BaseBusinessRule` in `fleet_management/business_rules/`:
```python
from fleet_management.business_rules.base_rule import BaseBusinessRule

class VehicleOdometerCheckRule(BaseBusinessRule):
    rule_id = "VEH-011"
    rule_name = "Odometer Integrity Check"

    def evaluate(self) -> bool:
        current = self.data.get("current_odometer", 0)
        initial = self.data.get("initial_odometer", 0)
        if current < initial:
            self.add_error(f"{self.rule_id}: Current odometer ({current}) cannot be less than initial ({initial}).")
            return False
        return True
```

2. Invoke the rule inside the relevant domain validator in `fleet_management/validators/`.

---

## 4. Writing Unit & Integration Tests

All tests are located in `fleet_management/tests/`.

### Test Execution Commands
- Run complete test suite:
  ```bash
  docker compose exec -T backend /home/frappe/frappe-bench/env/bin/pytest apps/fleet_management/fleet_management/tests
  ```
- Run specific test file:
  ```bash
  docker compose exec -T backend /home/frappe/frappe-bench/env/bin/pytest apps/fleet_management/fleet_management/tests/test_v1_api.py
  ```

---

## 5. Code Quality & Conventions

- **Formatter**: Black (`line-length = 100`)
- **Linter**: Ruff (`select = ["E", "F", "W", "I", "B", "C4", "UP"]`)
- **Type Hints**: Standard Python type annotations (`typing.Dict`, `typing.List`, `typing.Optional`) on all service and API methods.
