/**
 * Maintenance Template Client Script
 * Fleet Management System (Frappe Framework v15)
 */

frappe.ui.form.on('Maintenance Template', {
	setup: function(frm) {
		// Filter Vehicle link in child table:
		// Exclude vehicles belonging to other templates AND vehicles already picked in current form
		frm.set_query('vehicle', 'vehicles', function(doc) {
			let current_template = doc.name || doc.template_name || '';

			let selected_in_form = [];
			(doc.vehicles || []).forEach(function(row) {
				if (row.vehicle) {
					selected_in_form.push(row.vehicle);
				}
			});

			let filters = [
				['Vehicle', 'maintenance_template', 'in', ['', null, current_template]]
			];

			if (selected_in_form.length > 0) {
				filters.push(['Vehicle', 'name', 'not in', selected_in_form]);
			}

			return { filters: filters };
		});
	}
});
