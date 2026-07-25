/*
 * Fleet Settings Form Client-Side Controller
 * Frappe Framework v15
 */

frappe.ui.form.on("Fleet Settings", {
	refresh: function (frm) {
		frm.add_custom_button(
			__("☁ Load Demo Data"),
			function () {
				frm.events.load_demo_data_button(frm);
			},
			__("Demo Actions")
		);

		frm.add_custom_button(
			__("🗑 Remove Demo Data"),
			function () {
				frm.events.remove_demo_data_button(frm);
			},
			__("Demo Actions")
		);
	},

	load_demo_data_button: function (frm) {
		frappe.confirm(
			__("Are you sure you want to load the ABC Logistics Demo Dataset?"),
			function () {
				frappe.show_alert({ message: __("Loading Demo Dataset..."), indicator: "blue" });
				frappe.call({
					method: "fleet_management.fleet_management.doctype.fleet_settings.fleet_settings.load_demo_data_button",
					freeze: true,
					freeze_message: __("Populating ABC Logistics Demo Data..."),
					callback: function (r) {
						frappe.show_alert({ message: __("Demo dataset loaded successfully! Refreshing..."), indicator: "green" });
						setTimeout(function () { window.location.reload(); }, 600);
					}
				});
			}
		);
	},

	remove_demo_data_button: function (frm) {
		frappe.confirm(
			__("Are you sure you want to remove all ABC Logistics demo records? User-created production data will not be deleted."),
			function () {
				frappe.show_alert({ message: __("Purging Demo Dataset..."), indicator: "orange" });
				frappe.call({
					method: "fleet_management.fleet_management.doctype.fleet_settings.fleet_settings.remove_demo_data_button",
					freeze: true,
					freeze_message: __("Safely purging demo records..."),
					callback: function (r) {
						frappe.show_alert({ message: __("Demo data removed successfully! Refreshing..."), indicator: "orange" });
						setTimeout(function () { window.location.reload(); }, 600);
					}
				});
			}
		);
	},
});
