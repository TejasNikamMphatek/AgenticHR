frappe.pages['data-drive'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Data Drive',
		single_column: true
	});
	me = frappe.data_drive;
	frappe.data_drive.make(page);
}

	
frappe.data_drive = {
	start : 0,
	drive_data : "",
	DriveRow : "",
	make: function (page) {
		me.page = page;
		me.body = $("<div></div>").appendTo(me.page.main);
		me.run();
	},
	run: function () {
		var me = frappe.data_drive;
		frappe.call({
			method: "hrms.hr.page.data_drive.data_drive.getDataDrive",
			args: {
				start: me.start,
			},
			callback: function (response){
				if (response.message && response.message.length > 0)
				{	
					me.drive_data = response.message;
					me.send_data(me.drive_data)
					response.message.forEach(function (data) {
						if (data) {
							// ...................
						}else{
							frappe.show_alert({ message: __("Data Not Found ! "), indicator: "gray" });
						}
					});
				}
				else
				{
					$('#page-data-drive').addClass('hidden')
				}
			},
		});
		//reload back
		window.onpopstate = function(event) {
			window.location.reload();
		};
	},

	send_data: function (data) 
	{
		// console.log(data)
		me.create_filters()
		me.DriveRow = me.dataDriveRow(data[0]['drive_data']);
		$(frappe.render_template("data_drive")).appendTo(me.page.main);
	},

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

		let aadhar_verified = me.page.add_field({
			fieldtype: "Check",
			fieldname: "aadhar_verified",
			label:"Aadhar Verified",
			change: () => {
				me.aadhar_verified = aadhar_verified.get_value(); // Returns 1 (checked) or 0 (unchecked)
				me.TriggerMainData();  // Fetch data again when filter changes
			},
		});

		company.refresh();
		employee.refresh();
		aadhar_verified.refresh();
	},

	TriggerMainData: function(){
		frappe.call({
			method: "hrms.hr.page.data_drive.data_drive.getDataDrive",
			args: {
				start: me.start,
				employee: me.employee || "",
				company: me.company || "",
				aadhar_verified: me.aadhar_verified || "",
			},
			callback: function (response){
				if (response.message && response.message.length > 0){	
					me.drive_data = response.message;
					me.updateUI(me.drive_data);

				}else{
					$('#page-data-drive').addClass('hidden')
				}
			},
		});
	},
	// Update Employee List UI
	updateUI: function (data_drive) {
		me.DriveRow = this.dataDriveRow(data_drive[0]['drive_data'])
		$("#data_drive").html(me.DriveRow);
	},

	dataDriveRow: function (data){
		let row = "";
		data.forEach(function(item, index) {
			item['aadhar_verified'] = item['aadhar_verified'] ? "Verified" : "Not verified";
			item['name_on_aadhar'] = item['name_on_aadhar'] ? item['name_on_aadhar'] : " ";
			let verifyClass = item['aadhar_verified'] == "Verified" ? 'text-success' : 'text-danger';
			
			row += `
			<tr class="border">
				<td>${index + 1}</td>
				<td><a href="/app/employee/${item['id']}">${item['id']}</a></td>
				<td>${item['employee_name']}</td>
				<td>${item['name_on_aadhar']}</td>
				<td>${item['aadhar_number']}</td>
				<td class="${verifyClass}">${item['aadhar_verified']}</td>
			</tr>
			`;
		});
		return row;
	},

	
}
