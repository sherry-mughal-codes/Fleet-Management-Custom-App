frappe.ui.form.on('Maintenance Request', {
	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			frappe.db.get_value('Vehicle', frm.doc.vehicle, 
				['vehicle_number', 'vehicle_name', 'vehicle_brand', 'vehicle_model', 'current_odometer', 'company', 'status', 'last_maintenance_date', 'last_maintenance_odometer'], 
				function(r) {
					if (r) {
						if (r.vehicle_number) frm.set_value('vehicle_number', r.vehicle_number);
						if (r.vehicle_name) frm.set_value('vehicle_name', r.vehicle_name);
						if (r.vehicle_brand) frm.set_value('vehicle_brand', r.vehicle_brand);
						if (r.vehicle_model) frm.set_value('vehicle_model', r.vehicle_model);
						if (r.current_odometer !== undefined) frm.set_value('current_odometer', r.current_odometer);
						if (r.company && !frm.doc.company) frm.set_value('company', r.company);
						if (r.status) frm.set_value('current_vehicle_status', r.status);
						if (r.last_maintenance_date) frm.set_value('last_maintenance_date', r.last_maintenance_date);
						if (r.last_maintenance_odometer !== undefined) frm.set_value('last_maintenance_odometer', r.last_maintenance_odometer);
					}
				}
			);

			// Auto-lookup active assignment
			frappe.db.get_list('Vehicle Assignment', {
				filters: { 'vehicle': frm.doc.vehicle, 'status': ['in', ['Assigned', 'In Use']] },
				fields: ['name', 'employee_name'],
				limit: 1
			}).then(records => {
				if (records && records.length > 0) {
					frm.set_value('current_assignment', records[0].name);
					frm.set_value('assigned_employee', records[0].employee_name);
				}
			});
		}
	}
});
