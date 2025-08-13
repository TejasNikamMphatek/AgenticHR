
frappe.pages['confirmation-list'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Confirmation List',
		single_column: true
	});
	me = frappe.confirmation_list;
	frappe.confirmation_list.make(page);
}

	frappe.pages['confirmation-list'].on_page_show = function(wrapper) {
		$('.standard-actions.flex').addClass('hide');
		$('.standard-actions.flex').remove();
	};


frappe.confirmation_list = {
	confirmed_emp_element : "",
	upcoming_confirmation_element : "",
	employee_id : "",
	
	make: function (page) {
		me.page = page;
		me.body = $("<div></div>").appendTo(me.page.main);
		me.run();

	},
	run: function () {
		frappe.call({
			method: "hrms.hr.page.confirmation_list.confirmation_list.getConfirmationData",
			args: {
				start: me.start,
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {
					me.dashboard_user_data = response.message;
					me.send_data(me.dashboard_user_data);
					response.message.forEach(function (d) {
						if (d) {
							// console.log(d);
						} else {
							frappe.show_alert({ message: __("Data Not Found ! "), indicator: "gray" });
						}
					});
				} else {
					frappe.show_alert({ message: __("No more updates"), indicator: "gray" });
					me.more.parent().addClass("hidden");
				}
			},
		});
		// $('.page-head').addClass('hide');
		window.onpopstate = function(event) {
			window.location.reload();
		};

	},

	send_data: function (data) {
		console.log("Main Data",data)
		me.confirmed_emp_element = this.confirmedEmployee(data[0]['confirmed_employee'])
		me.upcoming_confirmation_element = this.upComingConfirmation(data[0]['probation_employee'])
		$(frappe.render_template("confirmation_list")).appendTo(me.page.main);

		this.Sidebar()
	},

	confirmedEmployee: function(confirmedEmployee){
		let confirmed_emp_ele ="";
		if (confirmedEmployee.length > 0) {
			for (let i = 0; i < confirmedEmployee.length; i++) 
			{	confirmedEmployee[i]['image'] = confirmedEmployee[i]['image'] ? confirmedEmployee[i]['image'] : "/assets/hrms/images/user_employee.png"
				confirmed_emp_ele +=
					`<div class="row p-2 border confirm_list" onclick="me.openConfirmedEmployee(${confirmedEmployee[i]['id']})">
						<div class="col-md-1 d-none d-md-block">
							<img src="${confirmedEmployee[i]['image']}"
								alt="employee image" />
						</div>
						<div class="col-md-4 col-sm-4 col-xs-4">
							<b>${confirmedEmployee[i]['employee_name']}</b> <br>
							<span>${confirmedEmployee[i]['id']}</span>
						</div>
						<div class="col-md-4 col-sm-5 col-xs-5">
							<span>Joining Date :</span> <b>${confirmedEmployee[i]['date_of_joining']}</b> <br>
							<span>Confirmation Date :</span> <b>${confirmedEmployee[i]['final_confirmation_date']}</b>
						</div>
						<div class="col-3">
							<span>Currently With : HR</span>
						</div>
					</div>
					`
			}
		} else {
			confirmed_emp_ele = `<div class="row my-2">
										<div class="col-md-12 text-center p-3 bg-white">
											<strong>Confirmed Employees Not Available</strong>
										</div>
									</div>`;
		}

		me.confirmed_emp_element = confirmed_emp_ele
		return confirmed_emp_ele

	},
	
	openConfirmedEmployee: function(confirmed_emp_id) {
		let ttl_confirmed_employee = me.dashboard_user_data[0]['confirmed_employee'];
		let employee = ttl_confirmed_employee.find(emp => emp.id == confirmed_emp_id);
		employee_name = employee['employee_name']

		if (employee) {
			$('.confirmation-list-section').addClass('hide');
			$('.sigle_employee_confirm_extend').removeClass('hide');

			me.employee_id = employee['id'];
			reports_to = employee['reports_to'];
			branch = employee['branch'];
			image = employee['image'];
			department = employee['department'];
			designation = employee['designation'];
			date_of_joining = employee['date_of_joining'];
			final_confirmation_date = employee['final_confirmation_date'];
			confirmation_initiate_on_date = employee['confirmation_initiate_on_date'];
			today = new Date();  // Get the current date
			privious_experience = employee['total_work_experience']
			current_experience = (today - new Date(date_of_joining)) / (1000 * 3600 * 24 * 365); 
			total_work_experience = current_experience + privious_experience
			total_work_experience = Math.round(total_work_experience * 10) / 10;
			confirmation_status = employee['confirmation_status'];
			confirmation_extend_date = employee['confirmation_extend_date'];
			confirmation_extend_reason = employee['confirmation_extend_reason'];
			recommanded_date = confirmation_extend_date || final_confirmation_date;
			confirmation_status_feedback = employee['confirmation_status_feedback'];
			if (confirmation_status === "Confirmed") {
				$('input[name="toggleStatus"][value="confirm"]').prop('checked', true);
				me.showHideByRadio('confirm');
			}

			$('#confirm_emp_title_name').text(employee_name)
			$('#branch').text(branch)
			$('#date_of_joining').text(date_of_joining)
			$('.final_confirmation_date').text(final_confirmation_date)
			$('.confirmation_extend_date').text(confirmation_extend_date)
			$('#reports_to').text(reports_to)
			$('#image').text(image)
			$('#department').text(department)
			$('#designation').text(designation)
			$('#confirmation_initiate_on_date').text(confirmation_initiate_on_date)
			$('#total_work_experience').text(total_work_experience);
			$('#confirmation_status').text(confirmation_status);
			$('#confirmation_extend_reason').text(confirmation_extend_reason);
			$('.recommanded_date').text(recommanded_date)
			$('#c_feedback_for_employee').text(confirmation_status_feedback);
			
		} else {
			console.log("Confirmed Employee not found");
		}
	},
	openConfirmedList:function(){
		me.confirmed_emp_element = "";
		frappe.call({
			method: "hrms.hr.page.confirmation_list.confirmation_list.getConfirmationData",
			args: {
				start: me.start,
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {
					me.cnfmd_emply = response.message[0].confirmed_employee
					me.confirmedEmployee(me.cnfmd_emply)
				} else {
					frappe.show_alert({ message: __("No more updates"), indicator: "gray" });
					me.more.parent().addClass("hidden");
				}
			},
		});
		$('.confirmation-list-section, .confirm_list, .conf_emp_title').removeClass('hide');
		$('.sigle_employee_confirm_extend, .pending_confirm_list, .prob_emp_title').addClass('hide')
	},
	openProbationList:function(){
		me.upcoming_confirmation_element = "";
		frappe.call({
			method: "hrms.hr.page.confirmation_list.confirmation_list.getConfirmationData",
			args: {
				start: me.start,
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {
					me.cnfmd_emply = response.message[0].confirmed_employee
					me.confirmedEmployee(me.cnfmd_emply)
				} else {
					frappe.show_alert({ message: __("No more updates"), indicator: "gray" });
					me.more.parent().addClass("hidden");
				}
			},
		});
		$('.sigle_employee_confirm_extend, .confirm_list, .conf_emp_title').addClass('hide')
		$('.pending_confirm_list, .prob_emp_title, .confirmation-list-section').removeClass('hide')
		
	},
	showHideByRadio:function(radio_value){
		if (radio_value == "confirm") {
			$('.show_by_confirm_radio').removeClass('hide');
			$('.show_by_extend_radio').addClass('hide');
		}else if(radio_value == "extend"){
			$('.show_by_confirm_radio').addClass('hide');
			$('.show_by_extend_radio').removeClass('hide');
		}
		
		
	},
	confirmEmpVal:function(btnVal){
		let selectedRadio = $('input[type="radio"]:checked').val();
		let feedbackForEmployee = $('#c_feedback_for_employee').val();
		// let shareRemark = $('#c_share_remark').val();
		// let fileAttachment = $('#c_file_attachment')[0].files[0]; 

		if (btnVal == "c_submit" && selectedRadio == "confirm") 
		{
			frappe.confirm('Are you sure you want to proceed?',
				(if_yes) => {
					frappe.db.set_value('Employee', me.employee_id, {
						confirmation_status: 'Confirmed',
						confirmation_status_feedback : feedbackForEmployee
					}).then(r => {
						let doc = r.message;
						if (doc) {
							frappe.show_alert({ message: __("Confirmation Status Update Successfully ! "), indicator: "green" });
							window.location.reload();
						} else {
							frappe.show_alert({ message: __("Not updated !"), indicator: "red" });
						}
					})
				}, (if_no) => {
					frappe.show_alert({ message: __("Not updated !"), indicator: "gray" });
			})
			
		}else if (btnVal == "c_reject" && selectedRadio == "confirm"){
			frappe.confirm('Are you sure you want to proceed?',
				(if_yes) => {
					frappe.db.set_value('Employee', me.employee_id, {
						confirmation_status: 'Rejected',
						confirmation_status_feedback:feedbackForEmployee
					}).then(r => {
						let doc = r.message;
						if (doc) {
							frappe.show_alert({ message: __("Confirmation Status Rejected Successfully ! "), indicator: "green" });
							window.location.reload();
						} else {
							frappe.show_alert({ message: __("Not updated !"), indicator: "red" });
						}
					})
				}, (if_no) => {
					frappe.show_alert({ message: __("Not updated !"), indicator: "gray" });
			})
		} else {
			frappe.show_alert({
				message:__('Cancel Successfully'),
				indicator:'green'
			}, 5);
			
		}

	},

	upComingConfirmation: function(upcoming_confirmation) {
		let upcoming_confirm_emp ="";
		for (let i = 0; i < upcoming_confirmation.length; i++) 
		{	upcoming_confirmation[i]['image'] = upcoming_confirmation[i]['image'] ? upcoming_confirmation[i]['image'] : "/assets/hrms/images/user_employee.png"
			upcoming_confirm_emp +=
				`<div class="row p-2 border pending_confirm_list" onclick="me.openUpcomingConfEmp(${upcoming_confirmation[i]['id']})">
					<div class="col-md-1  d-none d-md-block">
						<img src="${upcoming_confirmation[i]['image']}"
							alt="employee image" />
					</div>
					<div class="col-md-4 col-sm-4 col-xs-4">
						<b>${upcoming_confirmation[i]['employee_name']}</b> <br>
						<span>${upcoming_confirmation[i]['id']}</span>
					</div>
					<div class="col-md-4 col-sm-5 col-xs-5">
						<span>Joining Date :</span> <b>${upcoming_confirmation[i]['date_of_joining']}</b> <br>
						<span>Confirmation Date :</span> <b>${upcoming_confirmation[i]['final_confirmation_date']}</b>
					</div>
					<div class="col-3">
						<span>Currently With : HR</span>
					</div>
				</div>
				`
		}
		return upcoming_confirm_emp
	},

	openUpcomingConfEmp: function(upc_conf_emp_id){
		let ttl_upcoming_conf = me.dashboard_user_data[0]['probation_employee'];
		let employee = ttl_upcoming_conf.find(emp => emp.id == upc_conf_emp_id);
		employee_name = employee['employee_name'];
		// console.log(employee)

		if (employee) {
			$('.confirmation-list-section').addClass('hide');
			$('.sigle_employee_confirm_extend').removeClass('hide');

			me.employee_id = employee['id']
			reports_to = employee['reports_to']
			branch = employee['branch']
			image = employee['image']
			department = employee['department']
			designation = employee['designation']
			date_of_joining = employee['date_of_joining']
			final_confirmation_date = employee['final_confirmation_date']
			confirmation_initiate_on_date = employee['confirmation_initiate_on_date']
			today = new Date();  // Get the current date
			privious_experience = employee['total_work_experience']
			current_experience = (today - new Date(date_of_joining)) / (1000 * 3600 * 24 * 365); 
			total_work_experience = current_experience + privious_experience
			total_work_experience = Math.round(total_work_experience * 10) / 10;
			confirmation_status = employee['confirmation_status'];
			confirmation_extend_date = employee['confirmation_extend_date'];
			confirmation_extend_reason = employee['confirmation_extend_reason'];
			recommanded_date = confirmation_extend_date || final_confirmation_date;
			confirmation_status_feedback = employee['confirmation_status_feedback'];

			if (confirmation_status == "On Probation" && confirmation_extend_date) {
				$('input[name="toggleStatus"][value="extend"]').prop('checked', true);
				me.showHideByRadio('extend');
			}
			

			$('#confirm_emp_title_name').text(employee_name)
			$('#branch').text(branch)
			$('#date_of_joining').text(date_of_joining)
			$('.final_confirmation_date').text(final_confirmation_date)
			$('.confirmation_extend_date').text(confirmation_extend_date)
			$('#reports_to').text(reports_to)
			$('#image').text(image)
			$('#department').text(department)
			$('#designation').text(designation)
			$('#confirmation_initiate_on_date').text(confirmation_initiate_on_date)
			$('#total_work_experience').text(total_work_experience);
			$('#confirmation_status').text(confirmation_status);
			$('#confirmation_extend_reason').text(confirmation_extend_reason);
			$('.recommanded_date').text(recommanded_date)
			$('#e_feedback_for_employee').text(confirmation_status_feedback);
			$('#e_extend_date').val(confirmation_extend_date);
			$('#e_extend_reason').val(confirmation_extend_reason);


			
		} else {
			console.log("Probation Employee not found");
		}
	},

	extendEmpVal:function(btnVal){
		let selectedRadio = $('input[type="radio"]:checked').val();
		let extend_date = $('#e_extend_date').val();
		let extend_reason = $('#e_extend_reason').val();
		let feedbackForEmployee = $('#e_feedback_for_employee').val();

		// let shareRemark = $('#e_share_remark').val();
		// let fileAttachment = $('#e_file_attachment')[0].files[0];

		
		
		if (btnVal == "e_submit" && selectedRadio == "extend") 
		{	
			if (extend_date) {
				var extendDate = new Date(extend_date); 
					var today = new Date();
					
					if (extendDate > today) {
						frappe.confirm('Are you sure you want to proceed?',
							(if_yes) => {
								frappe.db.set_value('Employee', me.employee_id, {
									confirmation_status: 'On Probation',
									confirmation_extend_date : extend_date,
									confirmation_extend_reason : extend_reason,
									confirmation_status_feedback:feedbackForEmployee

								}).then(r => {
									let doc = r.message;
									if (doc) {
										frappe.show_alert({ message: __("Confirmation Extend Successfully ! "), indicator: "green" });
										window.location.reload();
									} else {
										frappe.show_alert({ message: __("Not updated !"), indicator: "red" });
									}
								})
							}, (if_no) => {
								frappe.show_alert({ message: __("Not updated !"), indicator: "gray" });
						})
					} else {
						frappe.show_alert({ message: __("Select Valid Date !"), indicator: "red" });
					}
			}else{
				frappe.show_alert({ message: __("Select Valid Extend Date !"), indicator: "red" });
			}
			
		}else if (btnVal == "e_reject" && selectedRadio == "extend"){
			frappe.confirm('Are you sure you want to proceed?',
				(if_yes) => {
					frappe.db.set_value('Employee', me.employee_id, {
							confirmation_status: 'Rejected',
							confirmation_extend_reason : extend_reason,
							confirmation_status_feedback : feedbackForEmployee
					}).then(r => {
						let doc = r.message;
						if (doc) {
							frappe.show_alert({ message: __("Confirmation Status Rejected Successfully ! "), indicator: "green" });
							
						} else {
							frappe.show_alert({ message: __("Not updated !"), indicator: "red" });
						}
					})
				}, (if_no) => {
					frappe.show_alert({ message: __("Not updated !"), indicator: "gray" });
			})
		} else {
			frappe.show_alert({
				message:__('Cancel Successfully !'),
				indicator:'green'
			}, 5);
			
		}
	
	},

	emilTest: function(){
		frappe.call({
			method: "hrms.hr.page.confirmation_list.confirmation_list.notify",
			args: {
				start: me.start,
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {
					response.message.forEach(function (d) {
						if (d) {
							frappe.show_alert({ message: __("sent Successfully ! "), indicator: "green" });
						} else {
							frappe.show_alert({ message: __("Not send ! "), indicator: "red" });
						}
					});
				} else {
					frappe.show_alert({ message: __("Not OK"), indicator: "red" });
				}
			},
		});
	},
	Sidebar: function() {
		$('.parent-link').on('click', function(event) {
			event.preventDefault();
			const target = $($(this).data('target'));
			$('.child-menu').not(target).addClass('d-none');
			$('.sub-child-menu').not(target.find('.sub-child-menu')).addClass('d-none');
			target.toggleClass('d-none');
		});
	
		$('.child-link').on('click', function(event) {
			event.preventDefault();
			const target = $($(this).data('target'));
			target.toggleClass('d-none');
		});
	}
	
}
