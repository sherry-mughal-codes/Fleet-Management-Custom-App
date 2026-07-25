# Backup & Disaster Recovery Guide

## Fleet Management System v1.0.0

---

## 1. Overview

This document outlines backup procedures, site restoration steps, server migration workflows, and disaster recovery strategies for production deployments of the Fleet Management System.

---

## 2. Automated Backup Strategy

### A. Database Backup
Frappe Bench provides built-in tools for database backups:

```bash
# Take immediate database & files backup
bench --site site1.local backup --with-files
```

Backups are generated in `sites/site1.local/private/backups/`:
- `[timestamp]-[site]-database.sql.gz`
- `[timestamp]-[site]-files.tar`
- `[timestamp]-[site]-private-files.tar`

### B. Automated Cron Backup Job
Add a daily cron backup task to the server crontab:
```bash
0 2 * * * cd /home/frappe/frappe-bench && /usr/local/bin/bench --site site1.local backup --with-files >> /var/log/frappe_backup.log 2>&1
```

---

## 3. Disaster Recovery & Restoration

### A. Restoring Database on Fresh Instance
```bash
# 1. Create fresh bench site
bench new-site site1.local --mariadb-root-password secret

# 2. Install fleet_management app
bench --site site1.local install-app fleet_management

# 3. Restore database from backup payload
bench --site site1.local restore /path/to/[timestamp]-database.sql.gz --with-public-files /path/to/[timestamp]-files.tar --with-private-files /path/to/[timestamp]-private-files.tar

# 4. Run site migration to execute patches
bench --site site1.local migrate
```

---

## 4. Server & Environment Migration

To migrate an active production instance to a new server:

1. Put source site in maintenance mode:
   ```bash
   bench --site site1.local set-maintenance-mode on
   ```
2. Run final backup:
   ```bash
   bench --site site1.local backup --with-files
   ```
3. Transfer backup files securely via rsync / scp to target server.
4. Restore on target server using procedure in Section 3.
5. Disable maintenance mode:
   ```bash
   bench --site site1.local set-maintenance-mode off
   ```
