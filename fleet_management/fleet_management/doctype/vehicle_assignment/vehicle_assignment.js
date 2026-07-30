frappe.ui.form.on('Vehicle Assignment', {
	setup: function(frm) {
		// Only Available vehicles should be selectable for new assignments
		frm.set_query('vehicle', function() {
			return {
				filters: {
					'status': 'Available'
				}
			};
		});
	},

	refresh: function(frm) {
		// Hide status field from form (shown in outer header indicator)
		frm.set_df_property('status', 'hidden', 1);

		// Hide Return Information section on new forms or if vehicle return date is not set
		let has_return_data = Boolean(frm.doc.return_date || frm.doc.closing_odometer);
		frm.set_df_property('return_info_section', 'hidden', has_return_data ? 0 : 1);

		if (!frm.is_new() && frm.doc.docstatus === 1) {
			// Show Return Vehicle Button if assignment is submitted and not yet returned
			if (frm.doc.status !== 'Returned' && !frm.doc.return_date) {
				frm.add_custom_button(__('Return Vehicle'), function() {
					let default_closing = flt(frm.doc.opening_odometer) || 0;
					let d = new frappe.ui.Dialog({
						title: __('Return Vehicle'),
						fields: [
							{
								label: __('Return Date'),
								fieldname: 'return_date',
								fieldtype: 'Date',
								default: frappe.datetime.nowdate(),
								reqd: 1
							},
							{
								label: __('Closing Odometer (KM)'),
								fieldname: 'closing_odometer',
								fieldtype: 'Float',
								default: default_closing,
								reqd: 1,
								onchange: function() {
									let closing = flt(d.get_value('closing_odometer'));
									let opening = flt(frm.doc.opening_odometer) || 0;
									if (closing >= opening) {
										d.set_value('distance_travelled', flt(closing - opening, 2));
									}
								}
							},
							{
								label: __('Distance Travelled (KM)'),
								fieldname: 'distance_travelled',
								fieldtype: 'Float',
								read_only: 1,
								default: 0
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
							if (flt(values.closing_odometer) < flt(frm.doc.opening_odometer)) {
								frappe.msgprint({
									title: __('Validation Error'),
									message: __('Closing Odometer ({0} KM) cannot be less than Opening Odometer ({1} KM).', [values.closing_odometer, frm.doc.opening_odometer]),
									indicator: 'red'
								});
								return;
							}

							frappe.call({
								method: 'fleet_management.api.assignment_api.return_vehicle_api',
								args: {
									assignment_id: frm.doc.name,
									closing_odometer: values.closing_odometer,
									return_date: values.return_date,
									return_notes: values.return_notes,
									return_condition: values.return_condition
								},
								callback: function(r) {
									if (!r.exc) {
										frappe.show_alert({ message: __('Vehicle Returned Successfully. Status set to Available.'), indicator: 'green' });
										frm.reload_doc();
										d.hide();
									}
								}
							});
						}
					});
					d.show();
				}, __('Actions')).addClass('btn-primary');
			}
		}
	},

	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			// Auto-fetch latest fuel entry odometer for selected vehicle
			frappe.call({
				method: 'fleet_management.api.assignment_api.get_vehicle_opening_odometer_api',
				args: { vehicle: frm.doc.vehicle },
				callback: function(r) {
					if (r && r.message && r.message.data) {
						let data = r.message.data;
						if (data.company && !frm.doc.company) {
							frm.set_value('company', data.company);
						}
						let odo = flt(data.opening_odometer) || 0;
						frm.set_value('opening_odometer', odo);
					}
				}
			});
		}
	},

	closing_odometer: function(frm) {
		let opening = flt(frm.doc.opening_odometer) || 0;
		let closing = flt(frm.doc.closing_odometer) || 0;
		if (closing > opening) {
			frm.set_value('distance_travelled', flt(closing - opening, 2));
		}
	}
});
