frappe.ui.form.on('Maintenance Entry', {
	setup: function(frm) {
		// Filter Vehicle Assignment query
		frm.set_query('assignment', function() {
			return {
				filters: {
					'docstatus': 1,
					'status': 'Assigned'
				}
			};
		});
	},

	rate: function(frm) {
		frm.trigger('calculate_total_cost');
	},

	qty: function(frm) {
		frm.trigger('calculate_total_cost');
	},

	calculate_total_cost: function(frm) {
		let rate = flt(frm.doc.rate);
		let qty = flt(frm.doc.qty) || 1.0;
		frm.set_value('total_cost', flt(rate * qty, 2));
	},

	refresh: function(frm) {
		const prev_odo = frm._prev_odo || 0;
		fleet_show_maintenance_odometer_hint(frm, prev_odo);
	},

	assignment: function(frm) {
		if (frm.doc.assignment) {
			frappe.db.get_value('Vehicle Assignment', frm.doc.assignment,
				['vehicle', 'opening_odometer'],
				function(r) {
					if (r) {
						if (r.vehicle) {
							frappe.db.get_value('Vehicle', r.vehicle, ['current_odometer', 'initial_odometer'], function(v_res) {
								let last_odo = 0;
								if (v_res) {
									last_odo = flt(v_res.current_odometer) || flt(v_res.initial_odometer) || 0;
								}
								if (last_odo === 0 && r.opening_odometer) {
									last_odo = flt(r.opening_odometer);
								}
								frm._prev_odo = last_odo;

								if (last_odo > 0 && (!frm.doc.current_odometer || frm.doc.current_odometer === 0)) {
									frm.set_value('current_odometer', last_odo);
								}
								fleet_show_maintenance_odometer_hint(frm, last_odo);
								fleet_load_due_items(frm);
							});
						} else {
							fleet_load_due_items(frm);
						}
					}
				}
			);
		} else {
			frm._prev_odo = 0;
			fleet_show_maintenance_odometer_hint(frm, 0);
		}
	},

	current_odometer: function(frm) {
		if (!fleet_validate_maintenance_odometer(frm)) return;
		if (frm.doc.assignment && flt(frm.doc.current_odometer) > 0) {
			fleet_load_due_items(frm);
		}
	},

	before_submit: function(frm) {
		const odo = flt(frm.doc.current_odometer);
		const prev_odo = frm._prev_odo || 0;

		if (prev_odo > 0 && odo < prev_odo) {
			frappe.msgprint({
				title: __('Validation Error'),
				message: __('Odometer reading ({0} KM) is below the previous recorded vehicle odometer ({1} KM). Please correct the odometer reading before submitting.', [format_number(odo, null, 1), format_number(prev_odo, null, 1)]),
				indicator: 'red'
			});
			frappe.validated = false;
			return false;
		}
	}
});


// ---------------------------------------------------------------------------
// Helper: Show descriptive hint below current_odometer field
// ---------------------------------------------------------------------------

function fleet_show_maintenance_odometer_hint(frm, prev_odo) {
	let hint = '';
	if (!prev_odo || prev_odo <= 0) {
		hint = 'First maintenance entry for this vehicle - enter the current odometer reading';
	} else {
		hint = 'Previous reading: ' + format_number(prev_odo, null, 1) + ' KM - enter a value at or above this';
	}
	if (frm.fields_dict['current_odometer']) {
		frm.get_field('current_odometer').set_description(hint);
	}
}


// ---------------------------------------------------------------------------
// Helper: Inline odometer validation
// ---------------------------------------------------------------------------

function fleet_validate_maintenance_odometer(frm) {
	const entered = flt(frm.doc.current_odometer);
	const prev_odo = frm._prev_odo || 0;

	if (entered <= 0) {
		return false;
	}

	if (prev_odo > 0 && entered < prev_odo) {
		if (frm.fields_dict['current_odometer']) {
			frm.get_field('current_odometer').set_description(
				'Odometer reading (' + format_number(entered, null, 1) +
				' KM) cannot be less than the previous reading (' +
				format_number(prev_odo, null, 1) + ' KM).'
			);
		}
		frappe.show_alert({
			message: __('Odometer cannot be less than previous reading ({0} KM)', [format_number(prev_odo, null, 1)]),
			indicator: 'red'
		}, 5);
		return false;
	}

	fleet_show_maintenance_odometer_hint(frm, prev_odo);
	return true;
}


// ---------------------------------------------------------------------------
// Helper: Auto-load due maintenance items based on template intervals & odometer
// ---------------------------------------------------------------------------

function fleet_load_due_items(frm) {
	if (!frm.doc.assignment) return;
	const odo = flt(frm.doc.current_odometer);

	frm.call({
		method: 'fleet_management.api.maintenance_api.get_due_maintenance_items_api',
		args: {
			assignment: frm.doc.assignment,
			current_odometer: odo > 0 ? odo : null
		},
		callback: function(r) {
			if (!r || r.exc) return;
			const items = r.message.data || r.message || [];
			frm.clear_table('items');
			if (Array.isArray(items) && items.length > 0) {
				items.forEach(function(item) {
					let row = frm.add_child('items');
					row.item_name = item.item_name;
					row.interval_km = item.interval_km;
					row.is_mandatory = item.is_mandatory;
					row.priority = item.priority;
					row.grace_distance = item.grace_distance;
					row.description = item.description;
					row.is_completed = 1;
					row.cost = item.cost || 0.0;
				});
				frappe.show_alert({
					message: __('Loaded {0} due maintenance item(s).', [items.length]),
					indicator: 'green'
				});
			} else {
				frappe.show_alert({
					message: __('No maintenance items are currently due for this vehicle.'),
					indicator: 'blue'
				});
			}
			frm.refresh_field('items');
		}
	});
}
