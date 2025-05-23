// frappe.pages['who-is-in'].on_page_load = function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'Who Is In ?',
// 		single_column: true
// 	});
// }

frappe.pages['who-is-in'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Who Is In ?',
		single_column: true
	});
	me = frappe.who_is_in;
	frappe.who_is_in.make(page);
}

	
frappe.who_is_in = {
	start : 0,
	who_is_in_data:"",
	notYetInRows:"",
	statTable:'',
	leaveModal:'',
	lateCheckEmpRow:'',
	make: function (page) {
		me.page = page;
		me.body = $("<div></div>").appendTo(me.page.main);
		me.run();
	},
	run: function () {
		var me = frappe.who_is_in;
		frappe.call({
			method: "hrms.hr.page.who_is_in.who_is_in.getWhoIsInData",
			args: {
				start: me.start,
			},
			callback: function (response){
				if (response.message && response.message.length > 0)
				{	
					me.who_is_in_data = response.message;
					me.send_data(me.who_is_in_data)
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
					$('#page-who-is-in').addClass('hidden')
				}
			},
		});

		window.onpopstate = function(event) {
			window.location.reload();
		};
	},

	send_data: function (data) 
	{
		// console.log(data)
		me.statTable = this.statisticsTable(data[0])
		me.notYetInRows = this.NotYetInRow(data[0]['checkin_statistics'])
		me.leave_rows = this.leaveRows(data[0]['leave_applies'])
		me.lateCheckEmpRow = this.lateCheckinEmployee(data[0]['checkin_statistics']['late_checkin_employee'])
		$(frappe.render_template("who_is_in")).appendTo(me.page.main);

		$('#NotYetIn').text(`Not Yet In (${data[0]['checkin_statistics']['not_checked_in']})`);
		$('#lateArrival').text(`Late Arrivals (${data[0]['checkin_statistics']['late_checkins']})`);
		$('#LeaveCount').text(`On Leave (${data[0]['leave_applies']['todays_ttl_leave_app']})`);

	},
	NotYetInRow: function (data){
		let returnRow = "";
		let not_checking_employees = data['not_checking_employees'];


		not_checking_employees.forEach((employee,index) => {
			returnRow += `<div class="d-flex justify-content-between align-items-center border-bottom">
				<div>
					<p class="my-1">${employee['employee_name']}</p> 
					<a class="font-weight-bold" href="/app/employee/${employee['emp_id']}"><small>#${employee['emp_id']}</small></a>
				</div>
				<div>
					${employee['expected_checkin_time']}
				</div>
			</div>
			`
		});

		return returnRow;
	},

	lateCheckinEmployee: function(late_emp_data) {
		let returnRow = "";
		late_emp_data.forEach((employee, index) => {
			// Extract time part (HH:mm:ss) from employee['time']
			let checkinTime = employee['time'].split(" ")[1].split(".")[0]; // Splits and removes the milliseconds
	
			returnRow += `
				<div class="d-flex justify-content-between align-items-center border-bottom">
					<div>
						<p class="my-1">${employee['employee_name']}</p> 
						<a class="font-weight-bold" href="/app/employee/${employee['emp_id']}"><small>#${employee['emp_id']}</small></a>
					</div>
					<div>
						${checkinTime}  <!-- Display the formatted time here -->
					</div>
				</div>
			`;
		});
	
		return returnRow;
	},
	
	leaveRows: function (data){
		let returnRow = "";
		let leave_applications = data['leave_application'];
		// console.log(leave_applications);

	
		leave_applications.forEach((leave, index) => {
			let statusClass = leave['status'] === 'Approved' ? 'text-success' : 'text-info';
			// console.log(leave['emp_id']);
	
			// Safely store the leave data in a data attribute
			let leaveDataString = JSON.stringify(leave).replace(/"/g, '&quot;'); 
	
			returnRow += `
				<div class="d-flex justify-content-between border-bottom">
					<div>
						<p class="my-1">${leave['employee_name']}</p> 
						<a class="font-weight-bold" href="/app/employee/${leave['emp_id']}"><small>#${leave['emp_id']}</small></a>
					</div>
					<div class='text-right'>
						<p class="my-1">${leave['total_leave_days']} Day(s)</p>
						<span class="leave_status">Status : <span class="${statusClass}">${leave['status']}</span></span>
	
						<p>
							<span data-leave-info="${leaveDataString}" data-emp-id="${leave['emp_id']}" 
								data-toggle="modal" data-target="#leaveInfo" class="toggle-icon"
								onclick="me.OpenLeaveModal(this)">
								<i class="fa fa-chevron-down"></i>
							</span>
						</p>
					</div>
				</div>
			`;
		});
	
		return returnRow;
	},
	

	statisticsTable :function(s_data){
		stat_data = s_data['checkin_statistics'];
		leave_data = s_data['leave_applies'];

		let statTable = 	`
			<table class="table table-bordered bg-white text-dark">
				<tr class="table-bordered">
					<th colspan="4">
						<span class="h5">Employees Information for ${stat_data['data_date']} </span>
					</th>
				</tr>
				<tr>
					<td>
						<b class="">${parseFloat(stat_data['not_checked_in_percentage'].toFixed(2))}%</b>
						<p>${stat_data['not_checked_in']} Employees Are Not Yet In</p> 
					</td>
					<td>
						<b class="">${parseFloat(stat_data['late_checkins_percentage'].toFixed(2))}%</b>
						<p>${stat_data['late_checkins']} Employees Are Late In</p> 
					</td>
					<td>
						<b class="">${parseFloat(stat_data['on_time_checkins_percentage'].toFixed(2))}%</b>
						<p>${stat_data['on_time_checkins']} Employees Are On Time</p> 
					</td>
					<td>
						<b class="">${parseFloat(leave_data['leave_application_percent_only_for_today'].toFixed(2))}%</b>
						<p>${leave_data['todays_ttl_leave_app']} Employees Are On Leave</p> 
					</td>
				</tr>
			</table>
			`
		return statTable;
	},
	OpenLeaveModal: function(element) {
		let leaveData = element.getAttribute('data-leave-info');
		let modal_data = '';
	
		let decodedLeaveData = leaveData.replace(/&quot;/g, '"');
	
		try {
			// Parse the leave data string back to a JSON object
			let leaveApplication = JSON.parse(decodedLeaveData);
			
			modal_data = `
			<div class="modal fade" id="leaveInfo" tabindex="-1" aria-labelledby="leaveInfoLabel" aria-hidden="true">
				<div class="modal-dialog">
					<div class="modal-content">
						<div class="modal-header">
							<h5 class="modal-title" id="leaveInfoLabel">Leave Info</h5>
							<button type="button" class="close" data-dismiss="modal" aria-label="Close">
								<span aria-hidden="true">&times;</span>
							</button>
						</div>
						<div class="modal-body">
							<table class="table table-bordered">
								<tr>
									<th>Emp ID</th>
									<td>${leaveApplication['emp_id']}</td>
								</tr>
								<tr>
									<th>Emp Name</th>
									<td>${leaveApplication['employee_name']}</td>
								</tr>
								<tr>
									<th>Leave Start Date</th>
									<td>${leaveApplication['from_date']}</td>
								</tr>
								<tr>
									<th>Leave End Date</th>
									<td>${leaveApplication['to_date']}</td>
								</tr>
								<tr>
									<th>Leave Days</th>
									<td>${leaveApplication['total_leave_days']}</td>
								</tr>
								<tr>
									<th>Leave Approver</th>
									<td>${leaveApplication['leave_approver']}</td>
								</tr>
								<tr>
									<th>Leave Type</th>
									<td>${leaveApplication['leave_type']}</td>
								</tr>
							</table>
						</div>
						<div class="modal-footer text-right">
							<button type="button" class="btn btn-primary" data-dismiss="modal">Close</button>
						</div>
					</div>
				</div>
			</div>`;
	
			// Remove existing modal if it exists
			$('#leaveInfo').remove(); 
	
			// Append the modal to the body
			document.body.insertAdjacentHTML('beforeend', modal_data);
	
			// Show the modal using Bootstrap's modal method
			$('#leaveInfo').modal('show');
	
		} catch (error) {
			console.error('Error parsing leave data:', error);
			alert('Failed to open modal: ' + error.message); // Optional alert for user feedback
		}
	},
	
	

	
	
}
