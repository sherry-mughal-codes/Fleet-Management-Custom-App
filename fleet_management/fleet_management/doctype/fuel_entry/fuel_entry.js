frappe.ui.form.on('Fuel Entry', {
	vehicle: function(frm) {
		if (frm.doc.vehicle) {
			frappe.db.get_value('Vehicle', frm.doc.vehicle, 
				['vehicle_number', 'vehicle_name', 'vehicle_brand', 'vehicle_model', 'fuel_type', 'current_odometer', 'company', 'status'], 
				function(r) {
					if (r) {
						if (r.vehicle_number) frm.set_value('vehicle_number', r.vehicle_number);
						if (r.vehicle_name) frm.set_value('vehicle_name', r.vehicle_name);
						if (r.vehicle_brand) frm.set_value('vehicle_brand', r.vehicle_brand);
						if (r.vehicle_model) frm.set_value('vehicle_model', r.vehicle_model);
						if (r.fuel_type) frm.set_value('fuel_type', r.fuel_type);
						if (r.current_odometer !== undefined) {
							frm.set_value('current_vehicle_odometer', r.current_odometer);
							if (!frm.doc.odometer) {
								frm.set_value('odometer', r.current_odometer);
							}
						}
						if (r.company && !frm.doc.company) frm.set_value('company', r.company);
						if (r.status) frm.set_value('current_vehicle_status', r.status);
					}
				}
			);

			// Auto-lookup active assignment
			frappe.db.get_list('Vehicle Assignment', {
				filters: { 'vehicle': frm.doc.vehicle, 'status': ['in', ['Assigned', 'In Use']] },
				fields: ['name', 'employee', 'employee_name', 'department', 'status', 'opening_odometer'],
				limit: 1
			}).then(records => {
				if (records && records.length > 0) {
					let a = records[0];
					frm.set_value('assignment', a.name);
					frm.set_value('assignment_id', a.name);
					frm.set_value('employee', a.employee);
					frm.set_value('assigned_employee', a.employee_name);
					frm.set_value('department', a.department);
					frm.set_value('assignment_status', a.status);
					frm.set_value('opening_odometer', a.opening_odometer);
				}
			});
		}
	},

	assignment: function(frm) {
		if (frm.doc.assignment) {
			frappe.db.get_value('Vehicle Assignment', frm.doc.assignment,
				['name', 'employee', 'employee_name', 'department', 'status', 'opening_odometer'],
				function(r) {
					if (r) {
						frm.set_value('assignment_id', r.name);
						frm.set_value('employee', r.employee);
						frm.set_value('assigned_employee', r.employee_name);
						frm.set_value('department', r.department);
						frm.set_value('assignment_status', r.status);
						frm.set_value('opening_odometer', r.opening_odometer);
					}
				}
			);
		}
	}
});
