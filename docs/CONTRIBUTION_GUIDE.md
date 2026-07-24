# Contribution Guide

## Fleet Management System (`fleet_management`)

Thank you for contributing to the **Fleet Management System**. Please follow these conventions and standards.

---

## 📜 Coding Conventions

1. **SOLID & DRY**: Always encapsulate business rules within `services/`. Never place database transactions directly inside UI controllers or Whitelisted API methods.
2. **Type Annotations**: Use Python type hints (`str`, `int`, `Dict[str, Any]`, `Optional[T]`) on public method signatures.
3. **Docstrings**: Document classes and public functions with clear docstrings explaining arguments and returns.
4. **Formatting**: Code must pass `ruff check` and `black --check`.
5. **No Shortcuts**: Do not bypass permission checks or leave hardcoded IDs in business logic.

---

## 🌿 Git Workflow

1. Create a feature or fix branch from `main`:
   ```bash
   git checkout -b feature/vehicle-tracking-service
   ```
2. Commit your changes following Conventional Commits:
   ```bash
   git commit -m "feat(service): implement vehicle status calculation service"
   ```
3. Run tests before pushing:
   ```bash
   pytest fleet_management/tests
   ```
4. Push branch and open a Pull Request.
