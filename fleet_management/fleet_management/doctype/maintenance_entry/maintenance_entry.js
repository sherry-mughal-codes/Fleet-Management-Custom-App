frappe.ui.form.on('Maintenance Entry', {
	setup: function(frm) {
		// Filter Vehicle Assignment query
		frm.set_query('assignment', function() {
			return {
				filters: {
					'docstatus': 1
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
				['vehicle', 'employee', 'company', 'opening_odometer'],
				function(r) {
					if (r) {
						if (r.vehicle) frm.set_value('vehicle', r.vehicle);
						if (r.employee) frm.set_value('employee', r.employee);
						if (r.company && !frm.doc.company) frm.set_value('company', r.company);

						if (r.vehicle) {
							frappe.db.get_value('Vehicle', r.vehicle, 'current_odometer', function(v_res) {
								if (v_res && v_res.current_odometer) {
									frm.set_value('current_odometer', v_res.current_odometer);
								} else if (r.opening_odometer) {
									frm.set_value('current_odometer', r.opening_odometer);
								}
							});
						}
					}
				}
			);
		}
	}
});
