/**
 * Fuel Entry Client Script
 * Fleet Management System (Frappe Framework v15)
 *
 * Architecture:
 * - Vehicle Assignment is the ONLY user-facing reference
 * - No "vehicle" field exists on Fuel Entry; no set_value('vehicle', ...) calls
 * - Odometer is MANUALLY entered by the user (not auto-set)
 * - A helper hint shows the previous reading below the odometer field
 * - Inline client-side validation blocks odometer values below the previous entry
 * - Total Cost is read-only and auto-calculated from qty x price
 * - Fuel Intelligence fields are auto-populated live via server API
 */

frappe.ui.form.on('Fuel Entry', {

	// -----------------------------------------------------------------------
	// Form Load / Refresh
	// -----------------------------------------------------------------------

	refresh: function(frm) {
		// Total cost is always computed — never manually editable
		frm.set_df_property('total_cost', 'read_only', 1);

		// Odometer is editable — user enters it manually
		frm.set_df_property('odometer', 'read_only', 0);

		// Lock all intelligence fields — server-computed only
		const intel_fields = [
			'previous_odometer', 'previous_fuel_date', 'days_since_last_fuel',
			'distance_travelled', 'fuel_average', 'cost_per_km',
			'fuel_efficiency_rating', 'is_first_entry'
		];
		intel_fields.forEach(f => frm.set_df_property(f, 'read_only', 1));

		// Restore the odometer hint if previous context is already stored
		const prev_odo = frm._prev_odo || flt(frm.doc.previous_odometer);
		fleet_show_odometer_hint(frm, prev_odo, frm.doc.is_first_entry);

		// Dashboard: Fuel Economy indicator
		if (frm.doc.fuel_average && frm.doc.fuel_average > 0) {
			const rating = frm.doc.fuel_efficiency_rating || '---';
			const color =
				rating === 'Excellent' ? 'green' :
				rating === 'Good'      ? 'blue'  :
				rating === 'Average'   ? 'yellow' : 'red';
			frm.dashboard.add_indicator(
				__('Fuel Economy: {0} KM/L - {1}', [flt(frm.doc.fuel_average, 2), rating]),
				color
			);
		}

		if (frm.doc.is_first_entry) {
			frm.dashboard.add_indicator(__('First Fuel Entry for this Vehicle'), 'blue');
		}
	},

	// -----------------------------------------------------------------------
	// Vehicle Assignment — Fetch previous fuel context only
	// -----------------------------------------------------------------------

	assignment: function(frm) {
		if (!frm.doc.assignment) {
			// Clear all intelligence when assignment removed
			fleet_clear_intelligence(frm);
			frm._prev_odo = 0;
			fleet_show_odometer_hint(frm, 0, false);
			return;
		}

		frm.call({
			method: 'fleet_management.api.fuel_api.get_assignment_fuel_context',
			args: { assignment: frm.doc.assignment },
			callback: function(r) {
				if (!r || r.exc || !r.message) return;
				const data = r.message.data || r.message;
				if (!data) return;

				const prev = data.previous_fuel_record;
				const is_first = data.is_first_entry;

				if (prev) {
					// Store previous odometer for inline validation
					frm._prev_odo = flt(prev.odometer);

					// Pre-populate intelligence header fields
					frm.set_value('previous_odometer', flt(prev.odometer));
					frm.set_value('previous_fuel_date', prev.fuel_date || null);
					frm.set_value('is_first_entry', 0);
				} else {
					// First entry for this vehicle
					frm._prev_odo = 0;
					frm.set_value('previous_odometer', 0);
					frm.set_value('previous_fuel_date', null);
					frm.set_value('is_first_entry', 1);
				}

				// Show descriptive hint below odometer field
				fleet_show_odometer_hint(frm, frm._prev_odo, is_first);

				// If odometer already filled, revalidate and recalculate
				if (flt(frm.doc.odometer) > 0) {
					fleet_validate_odometer(frm);
					fleet_recalculate_intelligence(frm);
				}
			}
		});
	},

	// -----------------------------------------------------------------------
	// Odometer — Manual entry with inline validation
	// -----------------------------------------------------------------------

	odometer: function(frm) {
		if (!fleet_validate_odometer(frm)) return;
		fleet_recalculate_intelligence(frm);
	},

	// -----------------------------------------------------------------------
	// Core Input Fields — Recalculate on every change
	// -----------------------------------------------------------------------

	fuel_qty: function(frm) {
		fleet_calculate_total(frm);
		fleet_recalculate_intelligence(frm);
	},

	fuel_price: function(frm) {
		fleet_calculate_total(frm);
		fleet_recalculate_intelligence(frm);
	},

	fuel_date: function(frm) {
		fleet_recalculate_intelligence(frm);
	},

});


// ---------------------------------------------------------------------------
// Helper: Show descriptive hint below odometer field
// ---------------------------------------------------------------------------

function fleet_show_odometer_hint(frm, prev_odo, is_first) {
	let hint = '';
	if (is_first || !prev_odo || prev_odo <= 0) {
		hint = 'First fuel entry for this vehicle - enter the current odometer reading';
	} else {
		hint = 'Previous entry: ' + format_number(prev_odo, null, 1) + ' KM - enter a value at or above this';
	}
	frm.get_field('odometer').set_description(hint);
}


// ---------------------------------------------------------------------------
// Helper: Inline odometer validation
// Returns true if valid, false if blocked
// ---------------------------------------------------------------------------

function fleet_validate_odometer(frm) {
	const entered  = flt(frm.doc.odometer);
	const prev_odo = frm._prev_odo || flt(frm.doc.previous_odometer);

	if (entered <= 0) {
		// Empty — nothing to validate yet
		return false;
	}

	if (prev_odo > 0 && entered < prev_odo) {
		// Inline red error
		frm.get_field('odometer').set_description(
			'Odometer reading (' + format_number(entered, null, 1) +
			' KM) cannot be less than the previous entry (' +
			format_number(prev_odo, null, 1) + ' KM).'
		);
		frappe.show_alert({
			message: __('Odometer cannot be less than previous entry ({0} KM)', [format_number(prev_odo, null, 1)]),
			indicator: 'red'
		}, 5);
		return false;
	}

	// Valid — restore normal hint
	fleet_show_odometer_hint(frm, prev_odo, frm.doc.is_first_entry);
	return true;
}


// ---------------------------------------------------------------------------
// Helper: Calculate total cost (client-side, instant)
// ---------------------------------------------------------------------------

function fleet_calculate_total(frm) {
	const qty   = flt(frm.doc.fuel_qty);
	const price = flt(frm.doc.fuel_price);
	if (qty > 0 && price > 0) {
		frm.set_value('total_cost', flt(qty * price, 2));
	}
}


// ---------------------------------------------------------------------------
// Helper: Recalculate Fuel Intelligence via server API
// ---------------------------------------------------------------------------

function fleet_recalculate_intelligence(frm) {
	if (!frm.doc.assignment) return;

	const odo      = flt(frm.doc.odometer);
	const qty      = flt(frm.doc.fuel_qty);
	const price    = flt(frm.doc.fuel_price);
	const fuel_date = frm.doc.fuel_date;
	const prev_odo = frm._prev_odo || flt(frm.doc.previous_odometer);

	// Need a valid odometer above previous to calculate anything meaningful
	if (odo <= 0) return;
	if (prev_odo > 0 && odo < prev_odo) return;  // blocked — skip API call

	// Need qty and price for intelligence
	if (qty <= 0 || price <= 0) return;

	frm.call({
		method: 'fleet_management.api.fuel_api.calculate_fuel_intelligence_api',
		args: {
			assignment:       frm.doc.assignment,
			current_odometer: odo,
			fuel_qty:         qty,
			fuel_price:       price,
			fuel_date:        fuel_date || frappe.datetime.get_today(),
			exclude_entry:    frm.doc.name || null,
		},
		callback: function(r) {
			if (!r || r.exc || !r.message) return;
			const intel = r.message.data || r.message;
			if (!intel) return;

			// Populate all intelligence fields
			frm.set_value('distance_travelled',     flt(intel.distance_travelled, 2));
			frm.set_value('days_since_last_fuel',   cint(intel.days_since_last_fuel));
			frm.set_value('fuel_average',           flt(intel.fuel_average, 2));
			frm.set_value('cost_per_km',            flt(intel.cost_per_km, 4));
			frm.set_value('fuel_efficiency_rating', intel.fuel_efficiency_rating || '---');
			frm.set_value('is_first_entry',         intel.is_first_entry ? 1 : 0);

			if (intel.previous_odometer !== undefined) {
				frm.set_value('previous_odometer', flt(intel.previous_odometer, 2));
			}
			if (intel.previous_fuel_date) {
				frm.set_value('previous_fuel_date', intel.previous_fuel_date);
			}

			// Refresh dashboard indicator with new rating
			const rating = intel.fuel_efficiency_rating || '---';
			const color  =
				rating === 'Excellent' ? 'green' :
				rating === 'Good'      ? 'blue'  :
				rating === 'Average'   ? 'yellow' : 'red';

			if (flt(intel.fuel_average) > 0) {
				frappe.show_alert({
					message: __('Fuel Economy: {0} KM/L - {1}', [flt(intel.fuel_average, 2), rating]),
					indicator: color
				}, 4);
			}
		}
	});
}


// ---------------------------------------------------------------------------
// Helper: Clear all intelligence fields (NOT odometer - user-entered)
// ---------------------------------------------------------------------------

function fleet_clear_intelligence(frm) {
	frm.set_value('previous_odometer',    0);
	frm.set_value('previous_fuel_date',   null);
	frm.set_value('distance_travelled',   0);
	frm.set_value('days_since_last_fuel', 0);
	frm.set_value('fuel_average',         0);
	frm.set_value('cost_per_km',          0);
	frm.set_value('fuel_efficiency_rating', '');
	frm.set_value('is_first_entry',       0);
	// Note: odometer is NOT cleared - user has manually entered a value
}


