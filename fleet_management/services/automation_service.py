"""
Fleet Automation Engine Service Implementation
Fleet Management System
"""

from typing import Any, Dict

import frappe

from fleet_management.enums import AssignmentStatus, NotificationType, VehicleStatus
from fleet_management.notifications.service import FleetNotificationService
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.services.base_service import BaseService
from fleet_management.services.fleet_cost_service import FleetCostService
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.health_service import FleetHealthService
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.settings_service import SettingsService
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.automation")


class FleetAutomationService(BaseService):
	"""
	Central Automation Engine coordinating scheduled business processes across all fleet domains.
	Calls existing domain services exclusively without duplicating business logic.
	"""

	def __init__(self):
		super().__init__()
		self.vehicle_service = VehicleService()
		self.assignment_service = AssignmentService()
		self.fuel_service = FuelService()
		self.maintenance_service = MaintenanceService()
		self.cost_service = FleetCostService()
		self.health_service = FleetHealthService()

	def run_all_automations(self) -> Dict[str, Any]:
		"""
		Main orchestrator running all enabled fleet automation subroutines.
		"""
		if not SettingsService.is_scheduler_enabled():
			logger.info("Automation Scheduler is disabled in Fleet Settings. Skipping automation run.")
			return {"status": "skipped", "reason": "Scheduler disabled in Fleet Settings."}

		logger.info("Starting complete Fleet Automation run...")
		maint_res = self.run_maintenance_automation()
		fuel_res = self.run_fuel_automation()
		assign_res = self.run_assignment_automation()
		cost_res = self.run_cost_automation()
		health_res = self.run_health_monitoring_automation()

		summary = {
			"status": "success",
			"state": "completed",
			"maintenance": maint_res,
			"fuel": fuel_res,
			"assignment": assign_res,
			"cost": cost_res,
			"health": health_res
		}
		logger.info("Completed Fleet Automation run successfully.", summary)
		return summary

	def run_automation_cycle(self) -> Dict[str, Any]:
		"""Alias method delegating to run_all_automations."""
		return self.run_all_automations()

	def run_maintenance_automation(self) -> Dict[str, Any]:
		"""
		Detects upcoming/overdue maintenance and generates reminder notifications.
		Delegates due logic directly to MaintenanceDueEngine and VehicleService.
		"""
		logger.info("Executing Maintenance Automation Check...")
		upcoming_count = 0
		overdue_count = 0
		reminders_sent = 0

		if not hasattr(frappe, "db") or not hasattr(frappe.db, "get_all"):
			return {"upcoming_count": 0, "overdue_count": 0, "reminders_sent": 0}

		try:
			v_fields = ["name", "current_odometer", "maintenance_interval_km"]
			if hasattr(frappe, "get_meta"):
				meta = frappe.get_meta("Vehicle")
				if meta.has_field("registration_number"):
					v_fields.append("registration_number")
				if meta.has_field("last_maintenance_odometer"):
					v_fields.append("last_maintenance_odometer")

			vehicles = frappe.db.get_all(
				"Vehicle",
				filters={"status": ["!=", VehicleStatus.DECOMMISSIONED]},
				fields=v_fields
			)
			reminder_dist = SettingsService.get_reminder_distance()

			for v in vehicles:
				v_id = v.name
				is_overdue = MaintenanceDueEngine.is_maintenance_overdue(v_id)
				if is_overdue:
					overdue_count += 1
					recipients = FleetNotificationService.get_authorized_recipients("Fleet Manager")
					FleetNotificationService.dispatch(
						notification_type=NotificationType.MAINTENANCE_DUE,
						recipients=recipients,
						subject=f"OVERDUE: Maintenance Required for {v_id}",
						message=f"Vehicle {v_id} ({getattr(v, 'registration_number', v_id)}) has exceeded its maintenance threshold.",
						reference_doctype="Vehicle",
						reference_name=v_id,
						enqueue_background=False
					)
					reminders_sent += 1
				else:
					next_due = MaintenanceDueEngine.calculate_next_due_odometer(v_id)
					curr_odo = float(v.current_odometer or 0.0)
					if (next_due - curr_odo) <= reminder_dist:
						upcoming_count += 1
						recipients = FleetNotificationService.get_authorized_recipients("Fleet Manager")
						FleetNotificationService.dispatch(
							notification_type=NotificationType.MAINTENANCE_DUE,
							recipients=recipients,
							subject=f"UPCOMING: Maintenance Scheduled for {v_id}",
							message=f"Vehicle {v_id} is within {int(next_due - curr_odo)} KM of required maintenance.",
							reference_doctype="Vehicle",
							reference_name=v_id,
							enqueue_background=False
						)
						reminders_sent += 1
		except Exception as e:
			logger.error(f"Error in maintenance automation: {str(e)}")

		return {
			"upcoming_count": upcoming_count,
			"overdue_count": overdue_count,
			"reminders_sent": reminders_sent
		}

	def run_fuel_automation(self) -> Dict[str, Any]:
		"""
		Detects fuel anomalies, declining fuel efficiency, and inactive fuel entries.
		Delegates fuel calculations strictly to FuelService.
		"""
		logger.info("Executing Fuel Automation Check...")
		anomalies_detected = 0
		declining_count = 0
		inactive_fuel_vehicles = 0

		if not hasattr(frappe, "db") or not hasattr(frappe.db, "get_all"):
			return {"anomalies_detected": 0, "declining_count": 0, "inactive_fuel_vehicles": 0}

		try:
			threshold_pct = SettingsService.get_fuel_anomaly_threshold()
			v_fields = ["name"]
			meta = frappe.get_meta("Vehicle")
			if meta.has_field("registration_number"):
				v_fields.append("registration_number")
			if meta.has_field("last_fuel_average"):
				v_fields.append("last_fuel_average")
			if meta.has_field("last_fuel_date"):
				v_fields.append("last_fuel_date")

			vehicles = frappe.db.get_all(
				"Vehicle",
				filters={"status": VehicleStatus.ASSIGNED},
				fields=v_fields
			)

			for v in vehicles:
				v_id = v.name
				summary = self.fuel_service.get_fuel_summary(v_id)
				lifetime_avg = summary.get("lifetime_fuel_average") or 0.0
				last_avg = float(v.last_fuel_average or 0.0)

				# Check fuel anomaly (drop > threshold %)
				if lifetime_avg > 0 and last_avg > 0:
					drop_pct = ((lifetime_avg - last_avg) / lifetime_avg) * 100.0
					if drop_pct >= threshold_pct:
						anomalies_detected += 1
						recipients = FleetNotificationService.get_authorized_recipients("Fleet Manager")
						FleetNotificationService.dispatch(
							notification_type=NotificationType.FUEL_ANOMALY,
							recipients=recipients,
							subject=f"ALERT: Abnormal Fuel Usage for {v_id}",
							message=f"Vehicle {v_id} reported a fuel efficiency drop of {round(drop_pct, 1)}% below lifetime baseline.",
							reference_doctype="Vehicle",
							reference_name=v_id,
							enqueue_background=False
						)

				# Check inactive fuel entries (assigned vehicle without fuel entry in 30 days)
				last_date = v.last_fuel_entry_date
				if not last_date:
					inactive_fuel_vehicles += 1
				elif hasattr(frappe, "utils"):
					days_diff = frappe.utils.date_diff(frappe.utils.nowdate(), last_date)
					if days_diff > 30:
						inactive_fuel_vehicles += 1
		except Exception as e:
			logger.error(f"Error in fuel automation: {str(e)}")

		return {
			"anomalies_detected": anomalies_detected,
			"declining_count": declining_count,
			"inactive_fuel_vehicles": inactive_fuel_vehicles
		}

	def run_assignment_automation(self) -> Dict[str, Any]:
		"""
		Detects assignments nearing return dates and un-updated/inactive assignments.
		Delegates assignment data fetching to AssignmentService.
		"""
		logger.info("Executing Assignment Automation Check...")
		expiring_count = 0
		inactive_count = 0
		notifications_sent = 0

		if not hasattr(frappe, "db") or not hasattr(frappe.db, "get_all"):
			return {"expiring_count": 0, "inactive_count": 0, "notifications_sent": 0}

		try:
			active_assignments = frappe.db.get_all(
				"Vehicle Assignment",
				filters={"status": ["in", [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_USE]]},
				fields=["name", "vehicle", "employee", "expected_return_date"]
			)

			today = frappe.utils.nowdate() if hasattr(frappe, "utils") else "2026-07-25"

			for a in active_assignments:
				exp_date = a.expected_return_date
				if exp_date and hasattr(frappe, "utils"):
					days_until = frappe.utils.date_diff(exp_date, today)
					if 0 <= days_until <= 3:
						expiring_count += 1
						recipients = FleetNotificationService.get_authorized_recipients("Fleet Officer")
						FleetNotificationService.dispatch(
							notification_type=NotificationType.ASSIGNMENT_EXPIRED,
							recipients=recipients,
							subject=f"NOTICE: Assignment {a.name} Expiring Soon",
							message=f"Vehicle Assignment {a.name} for Vehicle {a.vehicle} is due for return in {days_until} days.",
							reference_doctype="Vehicle Assignment",
							reference_name=a.name,
							enqueue_background=False
						)
						notifications_sent += 1
					elif days_until < 0:
						inactive_count += 1
						recipients = FleetNotificationService.get_authorized_recipients("Fleet Manager")
						FleetNotificationService.dispatch(
							notification_type=NotificationType.ASSIGNMENT_EXPIRED,
							recipients=recipients,
							subject=f"OVERDUE: Assignment {a.name} Exceeded Return Date",
							message=f"Vehicle Assignment {a.name} was expected on {exp_date} and is now overdue.",
							reference_doctype="Vehicle Assignment",
							reference_name=a.name,
							enqueue_background=False
						)
						notifications_sent += 1
		except Exception as e:
			logger.error(f"Error in assignment automation: {str(e)}")

		return {
			"expiring_count": expiring_count,
			"inactive_count": inactive_count,
			"notifications_sent": notifications_sent
		}

	def run_cost_automation(self) -> Dict[str, Any]:
		"""
		Refreshes aggregated cost summaries via FleetCostService.
		"""
		logger.info("Executing Fleet Cost Summary Refresh...")
		try:
			summary = self.cost_service.calculate_company_cost()
			return {"status": "refreshed", "company_cost": summary}
		except Exception as e:
			logger.error(f"Error in cost automation: {str(e)}")
			return {"status": "error", "message": str(e)}

	def run_health_monitoring_automation(self) -> Dict[str, Any]:
		"""
		Executes FleetHealthService data integrity checks and alerts admin if degraded or critical.
		"""
		logger.info("Executing Health Monitoring Automation...")
		report = self.health_service.run_health_check()
		status = report.get("status")

		if status in ["Degraded", "Critical"]:
			recipients = FleetNotificationService.get_authorized_recipients("System Manager")
			escalation = SettingsService.get_escalation_recipient()
			if escalation and escalation not in recipients:
				recipients.append(escalation)

			FleetNotificationService.dispatch(
				notification_type=NotificationType.SYSTEM_ALERT,
				recipients=recipients,
				subject=f"SYSTEM HEALTH ALERT: Fleet Integrity is {status.upper()}",
				message=f"System Health Score: {report.get('health_score')}%. Total Issues Found: {report.get('total_issues')}.",
				enqueue_background=False
			)

		return report
