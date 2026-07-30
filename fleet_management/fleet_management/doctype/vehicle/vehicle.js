frappe.ui.form.on('Vehicle', {
	setup: function(frm) {
		// Filter Vehicle Model based on selected Brand
		frm.set_query('vehicle_model', function() {
			return {
				filters: {
					'vehicle_brand': frm.doc.vehicle_brand || ''
				}
			};
		});
	},

	refresh: function(frm) {
		if (!frm.is_new()) {
			if (frm.doc.status === 'Available') {
				frm.add_custom_button(__('Assign Vehicle'), function() {
					frappe.route_options = { "vehicle": frm.doc.name };
					frappe.new_doc("Vehicle Assignment");
				}, __('Actions'));
			}

			frm.add_custom_button(__('Record Fuel'), function() {
				frappe.route_options = { "vehicle": frm.doc.name };
				frappe.new_doc("Fuel Entry");
			}, __('Actions'));

			frm.add_custom_button(__('Record Maintenance'), function() {
				frappe.route_options = { "vehicle": frm.doc.name };
				frappe.new_doc("Maintenance Entry");
			}, __('Actions'));
		}
	},

	vehicle_brand: function(frm) {
		if (frm.doc.vehicle_brand && frm.doc.vehicle_model) {
			frappe.db.get_value('Vehicle Model', frm.doc.vehicle_model, 'vehicle_brand', function(r) {
				if (r && r.vehicle_brand !== frm.doc.vehicle_brand) {
					frm.set_value('vehicle_model', '');
				}
			});
		}
	},

	vehicle_model: function(frm) {
		if (frm.doc.vehicle_model) {
			frappe.db.get_value('Vehicle Model', frm.doc.vehicle_model, 
				['fuel_type', 'default_fuel_average', 'engine_capacity', 'transmission'], 
				function(r) {
					if (r) {
						if (r.fuel_type && !frm.doc.fuel_type) frm.set_value('fuel_type', r.fuel_type);
						if (r.default_fuel_average && !frm.doc.expected_fuel_average) frm.set_value('expected_fuel_average', r.default_fuel_average);
						if (r.engine_capacity && !frm.doc.engine_capacity) frm.set_value('engine_capacity', r.engine_capacity);
						if (r.transmission && !frm.doc.transmission) frm.set_value('transmission', r.transmission);
					}
				}
			);
		}
	},

	fuel_type: function(frm) {
		if (frm.doc.fuel_type && !frm.doc.fuel_unit) {
			frappe.db.get_value('Fuel Type', frm.doc.fuel_type, 'unit', function(r) {
				if (r && r.unit) {
					frm.set_value('fuel_unit', r.unit);
				}
			});
		}
	}
});
