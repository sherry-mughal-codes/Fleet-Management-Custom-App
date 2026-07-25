# Business Rules Catalogue

## Fleet Management System v1.0.0

Complete directory of codified business invariants enforced across all domain modules.

---

## 1. Vehicle Intelligence Domain Rules (`VEH-001..010`)

| Rule ID | Rule Name | Description | Enforced In |
| :--- | :--- | :--- | :--- |
| **VEH-001** | Initial Odometer Non-Negative | Initial odometer reading must be >= 0.0 | `VehicleValidator` |
| **VEH-002** | Current Odometer Progression | Current odometer must be >= initial odometer | `VehicleValidator` |
| **VEH-003** | Tank Capacity Bound | Tank capacity must be within (0, Max Allowed Capacity] | `VehicleValidator` |
| **VEH-004** | Valid State Transition | Vehicle status transition must follow 13-state lifecycle graph | `VehicleStatusTransitionRule` |
| **VEH-005** | Unique License Plate | License plate must be unique per company | `VehicleValidator` |
| **VEH-006** | Mandatory Category & Fuel Type | Category and fuel type must be active reference records | `VehicleValidator` |

---

## 2. Assignment Intelligence Domain Rules (`ASN-001..010`)

| Rule ID | Rule Name | Description | Enforced In |
| :--- | :--- | :--- | :--- |
| **ASN-001** | Vehicle Availability Guard | Cannot assign vehicle already assigned, reserved, or in maintenance | `AssignmentVehicleAvailabilityRule` |
| **ASN-002** | Active Duplicate Guard | Vehicle cannot have multiple active assignments simultaneously | `AssignmentActiveDuplicateRule` |
| **ASN-003** | Handover Opening Odometer | Handover opening odometer must be >= current vehicle odometer | `AssignmentOdometerIntegrityRule` |
| **ASN-004** | Expected Return Date Sequence | Expected return date must be on or after assignment start date | `AssignmentValidator` |
| **ASN-005** | Closing Odometer Integrity | Return closing odometer must be >= opening odometer | `AssignmentService.return_vehicle` |

---

## 3. Fuel Intelligence Domain Rules (`FUEL-001..010`)

| Rule ID | Rule Name | Description | Enforced In |
| :--- | :--- | :--- | :--- |
| **FUEL-001** | Positive Fuel Quantity | Fuel quantity must be strictly > 0.0 | `FuelValidator` |
| **FUEL-002** | Positive Fuel Price & Cost | Price per unit and total cost must be > 0.0 | `FuelValidator` |
| **FUEL-003** | Odometer Progression | Fuel entry odometer reading must be >= vehicle current odometer | `FuelValidator` |
| **FUEL-004** | Fuel Capacity Upper Bound | Fuel quantity cannot exceed vehicle max tank capacity | `FuelValidator` |
| **FUEL-007** | Automated Average Calculation | Fuel average (KM/L) is calculated automatically upon submission | `FuelAverageService` |
| **FUEL-008** | Maintenance Lock Enforcement | Cannot submit fuel entry if vehicle maintenance is overdue | `MaintenanceLockService` |

---

## 4. Maintenance Intelligence Domain Rules (`MAINT-001..010`)

| Rule ID | Rule Name | Description | Enforced In |
| :--- | :--- | :--- | :--- |
| **MAINT-001** | Non-Negative Work Order Cost | Labor, parts, and total cost must be >= 0.0 | `MaintenanceValidator` |
| **MAINT-002** | Maintenance Due Calculation | Due odometer calculated via 4-tier policy hierarchy | `MaintenanceDueEngine` |
| **MAINT-003** | Work Order Completion Lock | Maintenance lock cleared only upon work order completion | `MaintenanceLockService` |
| **MAINT-004** | Scheduled Date Sequence | Completion date must be on or after creation/start date | `MaintenanceValidator` |

---

## 5. Fleet Cost Domain Rules (`COST-001..006`)

| Rule ID | Rule Name | Description | Enforced In |
| :--- | :--- | :--- | :--- |
| **COST-001** | Fuel Cost Aggregation | Sum of non-cancelled submitted fuel entry costs | `FleetCostService` |
| **COST-002** | Maintenance Cost Aggregation | Sum of completed maintenance work order costs | `FleetCostService` |
| **COST-003** | Total Operating Cost Equation | Total Operating Cost = Fuel Cost + Maintenance Cost | `FleetCostService` |
| **COST-006** | Cost Per KM Calculation | Cost Per KM = Total Operating Cost / Distance Travelled | `FleetCostService` |

---

## 6. Digital Asset Domain Rules (`ASSET-001..008`)

| Rule ID | Rule Name | Description | Enforced In |
| :--- | :--- | :--- | :--- |
| **ASSET-001** | Unique Document Reference | Document detail must be uniquely identified per vehicle | `VehicleAssetValidator` |
| **ASSET-002** | Document Expiry Date Warning | Warning generated when document expiry date is within 30 days | `VehicleAssetValidator` |
| **ASSET-003** | Max Image Count Limit | Maximum 10 images allowed per vehicle | `VehicleAssetValidator` |
