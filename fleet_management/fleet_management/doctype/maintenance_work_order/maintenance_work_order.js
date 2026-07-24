frappe.ui.form.on('Maintenance Work Order', {
	maintenance_request: function(frm) {
		if (frm.doc.maintenance_request) {
			frappe.db.get_value('Maintenance Request', frm.doc.maintenance_request,
				['vehicle', 'company', 'workshop_name'],
				function(r) {
					if (r) {
						if (r.vehicle) frm.set_value('vehicle', r.vehicle);
						if (r.company && !frm.doc.company) frm.set_value('company', r.company);
						if (r.workshop_name && !frm.doc.workshop) frm.set_value('workshop', r.workshop_name);
					}
				}
			);
		}
	}
});
