frappe.ui.form.on('Vehicle Assignment', {
	setup: function(frm) {
		// Only Available vehicles should be selectable
		frm.set_query('vehicle', function() {
			return {
				filters: {
					'status': 'Available'
				}
			};
		});
	},

	refresh: function(frm) {
		if (!frm.is_new()) {
			let status = frm.doc.status;

			// 1. Handover Button (Draft -> Assigned)
			if (status === 'Draft' || status === 'Approved' || status === 'Pending Approval') {
				frm.add_custom_button(__('Handover Vehicle'), function() {
					let d = new frappe.ui.Dialog({
						title: __('Vehicle Handover'),
						fields: [
							{
								label: __('Opening Odometer (KM)'),
								fieldname: 'opening_odometer',
								fieldtype: 'Float',
								default: frm.doc.opening_odometer || frm.doc.current_odometer || 0,
								reqd: 1
							},
							{
								label: __('Handover Notes'),
								fieldname: 'handover_notes',
								fieldtype: 'Small Text'
							}
						],
						primary_action_label: __('Complete Handover'),
						primary_action(values) {
							frappe.call({
								method: 'fleet_management.api.assignment_api.assign_vehicle_api',
								args: {
									assignment_id: frm.doc.name,
									opening_odometer: values.opening_odometer,
									handover_notes: values.handover_notes
								},
								callback: function(r) {
									if (!r.exc) {
										frappe.show_alert({ message: __('Vehicle Handover Completed'), indicator: 'green' });
										frm.reload_doc();
										d.hide();
									}
								}
							});
						}
					});
					d.show();
				}, __('Workflow'));
			}

			// 2. Return Vehicle Button (Assigned / In Use -> Returned)
			if (status === 'Assigned' || status === 'In Use') {
				frm.add_custom_button(__('Return Vehicle'), function() {
					let d = new frappe.ui.Dialog({
						title: __('Return Vehicle'),
						fields: [
							{
								label: __('Closing Odometer (KM)'),
								fieldname: 'closing_odometer',
								fieldtype: 'Float',
								default: frm.doc.opening_odometer || 0,
								reqd: 1
							},
							{
								label: __('Return Condition'),
								fieldname: 'return_condition',
								fieldtype: 'Small Text'
							},
							{
								label: __('Return Notes'),
								fieldname: 'return_notes',
								fieldtype: 'Small Text'
							}
						],
						primary_action_label: __('Complete Return'),
						primary_action(values) {
							frappe.call({
								method: 'fleet_management.api.assignment_api.return_vehicle_api',
								args: {
									assignment_id: frm.doc.name,
									closing_odometer: values.closing_odometer,
									return_notes: values.return_notes,
									return_condition: values.return_condition
								},
								callback: function(r) {
									if (!r.exc) {
										frappe.show_alert({ message: __('Vehicle Returned Successfully'), indicator: 'green' });
										frm.reload_doc();
										d.hide();
									}
								}
							});
						}
					});
					d.show();
				}, __('Workflow'));
			}

			// 3. Close Assignment Button (Returned -> Closed)
			if (status === 'Returned') {
				frm.add_custom_button(__('Close Assignment'), function() {
					frappe.call({
						method: 'fleet_management.api.assignment_api.close_assignment_api',
						args: { assignment_id: frm.doc.name },
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Assignment Closed'), indicator: 'blue' });
								frm.reload_doc();
							}
						}
					});
				}, __('Workflow'));
			}

			// 4. Cancel Assignment Button
			if (status !== 'Closed' && status !== 'Cancelled') {
				frm.add_custom_button(__('Cancel Assignment'), function() {
					frappe.prompt({
						label: __('Cancellation Reason'),
						fieldname: 'reason',
						fieldtype: 'Small Text'
					}, function(values) {
						frappe.call({
							method: 'fleet_management.api.assignment_api.cancel_assignment_api',
							args: { assignment_id: frm.doc.name, reason: values.reason },
							callback: function(r) {
								if (!r.exc) {
									frappe.show_alert({ message: __('Assignment Cancelled'), indicator: 'red' });
									frm.reload_doc();
								}
							}
						});
					}, __('Cancel Assignment'), __('Confirm Cancellation'));
				}, __('Actions'));
			}
		}
	},

	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			frappe.db.get_value('Vehicle', frm.doc.vehicle, ['current_odometer', 'company', 'status'], function(r) {
				if (r) {
					if (r.current_odometer !== undefined && (!frm.doc.opening_odometer || frm.doc.opening_odometer === 0)) {
						frm.set_value('opening_odometer', r.current_odometer);
					}
					if (r.company && !frm.doc.company) {
						frm.set_value('company', r.company);
					}
				}
			});
		}
	}
});
