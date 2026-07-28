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

	assignment: function(frm) {
		if (frm.doc.assignment) {
			frappe.db.get_value('Vehicle Assignment', frm.doc.assignment,
				['vehicle', 'opening_odometer'],
				function(r) {
					if (r) {
						if (r.vehicle) {
							frappe.db.get_value('Vehicle', r.vehicle, 'current_odometer', function(v_res) {
								if (v_res && v_res.current_odometer && (!frm.doc.current_odometer || frm.doc.current_odometer === 0)) {
									frm.set_value('current_odometer', v_res.current_odometer);
								} else if (r.opening_odometer && (!frm.doc.current_odometer || frm.doc.current_odometer === 0)) {
									frm.set_value('current_odometer', r.opening_odometer);
								}
								fleet_load_due_items(frm);
							});
						} else {
							fleet_load_due_items(frm);
						}
					}
				}
			);
		}
	},

	current_odometer: function(frm) {
		if (frm.doc.assignment && flt(frm.doc.current_odometer) > 0) {
			fleet_load_due_items(frm);
		}
	}
});


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
			if (!r || r.exc || !r.message) return;
			const items = r.message.data || r.message;
			if (!Array.isArray(items) || !items.length) return;

			frm.clear_table('items');
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
			frm.refresh_field('items');
		}
	});
}
