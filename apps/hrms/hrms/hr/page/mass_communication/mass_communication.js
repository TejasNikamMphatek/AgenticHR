frappe.pages['mass-communication'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Mass Communication',
		single_column: true
	});
	me = frappe.mass_communication;
	frappe.mass_communication.make(page);
}

	
frappe.mass_communication = {
	start : 0,
	commuData : '',
	emp_row : '',
	make: function (page) {
		me.page = page;
		me.body = $("<div></div>").appendTo(me.page.main);
		me.create_filters();  // Create filters first
		me.run();
	},

	// Run the function to fetch initial data
	run: function () {
		frappe.call({
			method: "hrms.hr.page.mass_communication.mass_communication.getMassCommunicationData",
			args: {
				start: me.start,
				company: me.company || "",
				department: me.department || "",
				employee: me.employee || "",
				designation: me.designation || "",
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {
					me.commuData = response.message;
					me.send_data(me.commuData);
				} else {
					$('#page-mass-communication').addClass('hidden');
				}
			},
		});

		
		window.onpopstate = function(event) {
			window.location.reload();
		};
	},

	// Create filter fields
	create_filters: function () {
		let company = me.page.add_field({
			fieldtype: "Link",
			options: "Company",
			fieldname: "company",
			placeholder: __("Select Company"),
			default: frappe.defaults.get_default("company"),
			only_select: true,
			reqd: 1,
			change: () => {
				me.company = company.get_value() || "";
				me.TriggerMainData();  // Fetch data again when filter changes
			},
		});

		let employee = me.page.add_field({
			fieldtype: "Link",
			options: "Employee",
			fieldname: "employee",
			placeholder: __("Select Employee"),
			only_select: true,
			change: () => {
				me.employee = employee.get_value() || "";
				me.TriggerMainData();
			},
		});

		let department = me.page.add_field({
			fieldtype: "Link",
			options: "Department",
			fieldname: "department",
			placeholder: __("Select Department"),
			only_select: true,
			change: () => {
				me.department = department.get_value() || "";
				me.TriggerMainData();
			},
		});

		let designation = me.page.add_field({
			fieldtype: "Link",
			options: "Designation",
			fieldname: "designation",
			placeholder: __("Select Designation"),
			only_select: true,
			change: () => {
				me.designation = designation.get_value() || "";
				me.TriggerMainData();
			},
		});

		company.refresh();
		employee.refresh();
		department.refresh();
		designation.refresh();
	},

	// Fetch updated data when filters change
	TriggerMainData: function () {
		frappe.call({
			method: "hrms.hr.page.mass_communication.mass_communication.getMassCommunicationData",
			args: {
				start: me.start,
				company: me.company || "",
				department: me.department || "",
				employee: me.employee || "",
				designation: me.designation || "",
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {
					me.commuData = response.message;
					me.updateUI(me.commuData[0]['active_employee']);
				} else {
					$('#page-mass-communication').addClass('hidden');
				}
			},
		});
	},

	// Update Employee List UI
	updateUI: function (employees) {
		me.emp_row = me.CommunicationEmployeeElement(employees);
		$("#employees_data").html(me.emp_row);
	},
	send_data: function (data) {
		me.emp_row = me.CommunicationEmployeeElement(data[0]['active_employee']);
		$(frappe.render_template("mass_communication")).appendTo(me.page.main);
	},

	// Generate Employee Table Rows
	CommunicationEmployeeElement: function (employees) {
		let emp_row = "";
		let i = 0;
		employees.forEach(function(employee) {
			if (employee['user_id']) {
				employee['image'] ? employee['image'] : employee['image'] = employee['image'] = "/assets/hrms/images/user_employee.png"
				emp_row += `
				<tr class="border">
					<td class="text-bold">${++i}</td>
					<td>${employee['id']}</td>
					<td><img src="${employee['image']}" class="rounded-circle mr-3" width="25px" alt=""> ${employee['employee_name']}</td>
					<td>${employee['user_id']}</td>
				</tr>
				`;
			}
		});
		return emp_row;
	},

	SendEmailToAll(){
		frappe.call({
            method: "hrms.hr.page.mass_communication.mass_communication.sendEmailToAll",
			args: {
				start: me.start,
				company: me.company || "",
				department: me.department || "",
				employee: me.employee || "",
				designation: me.designation || "",
			},
            callback: function (response){
                if (response.message)
                {
                    frappe.show_alert({ message: response.message, indicator: "green" });
                }
            },
        });
	},
	
}
