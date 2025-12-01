// Copyright (c) 2015, mPHATEK Systems Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.setup");

erpnext.setup.EmployeeController = class EmployeeController extends frappe.ui.form.Controller {
  setup() {
    this.frm.fields_dict.user_id.get_query = function (doc, cdt, cdn) {
      return {
        query: "frappe.core.doctype.user.user.user_query",
        filters: { ignore_user_type: 1 }
      };
    };
    this.frm.fields_dict.reports_to.get_query = function (doc, cdt, cdn) {
      return { query: "erpnext.controllers.queries.employee_query" };
    };
  }

  refresh() {
    erpnext.toggle_naming_series();
  }
};

frappe.ui.form.on("Employee", {

  refresh: function(frm) {
    // PAN + PF + IFSC uppercase alphanumeric typing sanitize + instant popup on lowercase
    for (let f of ["pan_number", "provident_fund_account", "ifsc_code"]) {
      frm.fields_dict[f]?.$input?.on("keypress", function(e) {
        if (/[a-z]/.test(e.key)) {
          frappe.msgprint(f.replace(/_/g, " ") + " must be uppercase letters and digits only.");
        }
      });
      frm.fields_dict[f]?.$input?.on("input", function() {
        this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
      });
    }

    // Bank Name - block digits + popup instantly
    frm.fields_dict.bank_name?.$input?.on("keypress", function(e) {
      if (/\d/.test(e.key)) {
        frappe.msgprint("Bank name should contain alphabets only.");
      }
    });
    frm.fields_dict.bank_name?.$input?.on("input", function() {
      this.value = this.value.replace(/[0-9]/g, "");
    });

    // CTC - allow digits only + popup instantly on non numeric
    frm.fields_dict.ctc?.$input?.on("keypress", function(e) {
      if (!/\d/.test(e.key)) {
        frappe.msgprint("CTC must contain only digits (0-9).");
      }
    });
    frm.fields_dict.ctc?.$input?.on("input", function() {
      this.value = this.value.replace(/[^0-9]/g, "");
    });

    // Bank Account Number - digits only + popup instantly
    frm.fields_dict.bank_ac_no?.$input?.on("keypress", function(e) {
      if (!/\d/.test(e.key)) {
        frappe.msgprint("Bank account number should contain only digits.");
      }
    });
    frm.fields_dict.bank_ac_no?.$input?.on("input", function() {
      this.value = this.value.replace(/[^0-9]/g, "");
    });

    // Emergency Contact Name - alphabets only + popup instantly on digit keypress
    frm.fields_dict.person_to_be_contacted?.$input?.on("keypress", function(e) {
      if (/\d/.test(e.key)) {
        frappe.msgprint("Emergency Contact Name should contain alphabets only.");
      }
    });
    frm.fields_dict.person_to_be_contacted?.$input?.on("input", function() {
      this.value = this.value.replace(/[0-9]/g, "");
    });
  },

  // Original logic retained

  onload: function(frm) {
    frm.set_query("department", function () {
      return {
        filters: { company: frm.doc.company }
      };
    });
  },

  prefered_contact_email: function(frm) {
    frm.events.update_contact(frm);
  },
  personal_email: function(frm) {
    frm.events.update_contact(frm);
  },
  company_email: function(frm) {
    frm.events.update_contact(frm);
  },
  user_id: function(frm) {
    frm.events.update_contact(frm);
  },

  update_contact: function(frm) {
    var prefered_email_fieldname = frappe.model.scrub(frm.doc.prefered_contact_email) || "user_id";
    frm.set_value("prefered_email", frm.fields_dict[prefered_email_fieldname].value);
  },

  reports_to: function(frm) {
    frm.events.setApprovers(frm);
  },

  setApprovers: function(frm) {
    if (!frm.doc.reports_to) return;
    frappe.call({
      method: "erpnext.setup.doctype.employee.employee.get_approvers_details",
      args: { reports_to: frm.doc.reports_to },
      callback: function(r) {
        if (r.message && r.message.user_id) {
          const approverFields = ["expense_approver","shift_request_approver","leave_approver"];
          for (let field of approverFields) {
            if (!frm.doc[field]) frm.set_value(field, r.message.user_id);
          }
          frm.refresh_fields(approverFields);
        }
      }
    });
  },

  status: function(frm) {
    return frm.call({
      method: "deactivate_sales_person",
      args: { employee: frm.doc.employee, status: frm.doc.status }
    });
  },

  employee_number: function (frm) {
    frm.events.setEmployeeDetails(frm);
  },

  setEmployeeDetails: function(frm) {
    if (frm.doc.employee_number && Number.isInteger(Number(frm.doc.employee_number))) {
      frappe.call({
        method: "erpnext.setup.doctype.employee.employee.get_user_details",
        args: { employee_number: frm.doc.employee_number },
        callback: function(r) {
          if (r.message) {
            if (r.message.first_name) frm.set_value("first_name", r.message.first_name);
            if (r.message.middle_name) frm.set_value("middle_name", r.message.middle_name);
            if (r.message.last_name) frm.set_value("last_name", r.message.last_name);
            if (r.message.email) frm.set_value("company_email", r.message.email);
            if (r.message.mobile_no) frm.set_value("cell_number", r.message.mobile_no);
            if (r.message.gender) frm.set_value("gender", r.message.gender);
            if (r.message.birth_date) frm.set_value("date_of_birth", r.message.birth_date);
            if (r.message.email) frm.set_value("user_id", r.message.email);
            if (r.message.date_of_joining) frm.set_value("date_of_joining", r.message.date_of_joining);
          }
        }
      });
    } else {
      frappe.msgprint("Please enter a valid integer employee number.");
    }
  },

  create_user: function(frm) {
    if (!frm.doc.prefered_email) {
      frappe.throw(__("Please enter Preferred Contact Email"));
    }
    frappe.call({
      method: "erpnext.setup.doctype.employee.employee.create_user",
      args: { employee: frm.doc.name, email: frm.doc.prefered_email },
      freeze: true,
      freeze_message: __("Creating User..."),
      callback: function (r) {
        frm.reload_doc();
      },
    });
  }
});

// attach controller
cur_frm.cscript = new erpnext.setup.EmployeeController({ frm: cur_frm });

// Tour
frappe.tour["Employee"] = [
  {
    fieldname: "first_name",
    title: "First Name",
    description: __("Enter Employee's first & last name for full naming.")
  },
  {
    fieldname: "company",
    title: "Company",
    description: __("Select Company for this Employee.")
  },
  {
    fieldname: "date_of_birth",
    title: "Date of Birth",
    description: __("Select DOB to validate age.")
  },
  {
    fieldname: "date_of_joining",
    title: "Date of Joining",
    description: __("Select joining date that impacts salary & leave.")
  },
  {
    fieldname: "reports_to",
    title: "Reports To",
    description: __("Select a senior Employee for org chart.")
  }
];
  
