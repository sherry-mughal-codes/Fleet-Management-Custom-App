/**
 * Fuel Entry Client Script
 * Fleet Management System (Frappe Framework v15)
 */

frappe.ui.form.on('Fuel Entry', {

	setup: function(frm) {
		// Filter Vehicle field to show assigned/active vehicles (including those with Maintenance Due or Return Overdue)
		frm.set_query('vehicle', function() {
			return {
				filters: [
					['Vehicle', 'status', 'in', ['Assigned', 'Maintenance Due', 'Inspection', 'Reserved', 'Return Overdue']]
				]
			};
		});
	},

	refresh: function(frm) {
		frm.set_df_property('total_cost', 'read_only', 0);
		frm.set_df_property('fuel_price', 'read_only', 0);
		frm.set_df_property('fuel_qty', 'read_only', 0);
		frm.set_df_property('odometer', 'read_only', 0);

		if (frm.doc.vehicle) {
			fetch_previous_odometer(frm);
		}
	},

	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			if (!frm.doc.fuel_type) {
				frappe.db.get_value('Vehicle', frm.doc.vehicle, 'fuel_type', function(r) {
					if (r && r.fuel_type) {
						frm.set_value('fuel_type', r.fuel_type);
					}
				});
			}
			fetch_previous_odometer(frm);
		}
	},

	odometer: function(frm) {
		let current_odo = flt(frm.doc.odometer);
		let prev_odo = flt(frm.previous_odometer || 0);

		if (current_odo > 0 && prev_odo > 0 && current_odo < prev_odo) {
			frappe.msgprint({
				title: __('Validation Error'),
				message: __('This is not allowed! Entered Odometer ({0} KM) is below previous odometer ({1} KM).', [current_odo, prev_odo]),
				indicator: 'red'
			});
		}
	},

	fuel_qty: function(frm) {
		fleet_calculate_three_way_fuel(frm, 'fuel_qty');
	},

	fuel_price: function(frm) {
		fleet_calculate_three_way_fuel(frm, 'fuel_price');
	},

	total_cost: function(frm) {
		fleet_calculate_three_way_fuel(frm, 'total_cost');
	}
});

function fetch_previous_odometer(frm) {
	if (!frm.doc.vehicle) return;
	frappe.call({
		method: 'fleet_management.api.fuel_api.get_vehicle_previous_odometer_api',
		args: {
			vehicle: frm.doc.vehicle,
			exclude_entry: frm.doc.name
		},
		callback: function(r) {
			if (r && r.message && r.message.data) {
				let prev_odo = flt(r.message.data.previous_odometer) || 0;
				frm.previous_odometer = prev_odo;
				if (prev_odo > 0) {
					frm.set_df_property(
						'odometer',
						'description',
						__('Previous odometer is {0} KM. Please enter an odometer reading at this or above.', [prev_odo])
					);
				} else {
					frm.set_df_property('odometer', 'description', __('Please enter current odometer reading.'));
				}
			}
		}
	});
}

function fleet_calculate_three_way_fuel(frm, last_changed) {
	const rate  = flt(frm.doc.fuel_price);
	const qty   = flt(frm.doc.fuel_qty);
	const total = flt(frm.doc.total_cost);

	if (last_changed === 'fuel_qty' || last_changed === 'fuel_price') {
		if (rate > 0 && qty > 0) {
			frm.set_value('total_cost', flt(rate * qty, 2));
		} else if (rate > 0 && total > 0) {
			frm.set_value('fuel_qty', flt(total / rate, 4));
		} else if (qty > 0 && total > 0) {
			frm.set_value('fuel_price', flt(total / qty, 4));
		}
	} else if (last_changed === 'total_cost') {
		if (rate > 0 && total > 0) {
			frm.set_value('fuel_qty', flt(total / rate, 4));
		} else if (qty > 0 && total > 0) {
			frm.set_value('fuel_price', flt(total / qty, 4));
		}
	}
}
