# Installation Guide

## Fleet Management System (`fleet_management`)

This guide explains how to install the `fleet_management` custom application on any target Frappe Framework v15 site.

---

## 📋 Prerequisites

- Frappe Framework v15 bench environment
- MariaDB 10.6+
- Redis Cache & Redis Queue
- Python 3.10+

---

## 📥 Step-by-Step Installation

### 1. Fetch Custom Application
From your bench directory:

```bash
bench get-app https://github.com/sherry-mughal-codes/Fleet-Management-Custom-App.git
```

### 2. Install App on Target Site
Replace `your-site.domain` with your active Frappe site name:

```bash
bench --site your-site.domain install-app fleet_management
```

### 3. Verify App Installation
Confirm app registration in site installed apps list:

```bash
bench --site your-site.domain list-apps
```

Expected output includes:
- `frappe`
- `fleet_management`

### 4. Enable Background Scheduler & Verify Workers
Ensure background jobs and scheduler are active:

```bash
bench --site your-site.domain enable-scheduler
bench doctor
```

### 5. Build Assets & Migrate
```bash
bench build --app fleet_management
bench --site your-site.domain migrate
```

---

## 🔄 Uninstallation Procedure

If you ever need to uninstall the application from a site:

```bash
bench --site your-site.domain uninstall-app fleet_management
```
