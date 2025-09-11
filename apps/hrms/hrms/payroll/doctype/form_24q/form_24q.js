// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Form 24Q", {
	// refresh(frm) {
	// },

    update_challan_details_quart_1: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Apr","May","Jun"]]
        });
    },

    update_challan_details_quart_2: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Jul","Aug","Sep"]]
        });
    },

    update_challan_details_quart_3: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Oct","Nov","Dec"]]
        });
    },

    update_challan_details_quart_4: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Jan","Feb","Mar"]]
        });
    }

});
