if(frappe.user.has_role("Administrator"))
{	
	window.location.replace('/app/home')
}
else if(frappe.user.has_role("HR Manager")){
	window.location.replace('/app/pipal-hr-dashboard')
}
else if(frappe.user.has_role("Onboarding Employee")){
	window.location.replace('/app/employee/view/list')
}
else if(frappe.user.has_role("Projects Manager") && frappe.user.has_role("Employee")){
	window.location.replace('/app/project-manager-dash')
}
else if(frappe.user.has_role("Employee")){
	frappe.pages['pipal-employee-dashboard'].on_page_load = function(wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Pipal Employee Dashboard',
			single_column: true
		});
		me = frappe.pipal_employee_dashboard;
		frappe.pipal_employee_dashboard.make(page);
	}

	frappe.pages['pipal-employee-dashboard'].on_page_show = function(wrapper) {
		$('.standard-actions.flex').addClass('hide');
		$('.standard-actions.flex').remove();
	};

	frappe.pipal_employee_dashboard = {
		start : 0,
		manager_data: [],
		emp_id: "",
		default_shift: "",
		actual_start_time: "",
		actual_end_time: "",
		checkInLogType: "",
		toggle_salary: "Show",
		holiday_element: "",
		
		make: function (page) {
			me.page = page;
			me.body = $("<div></div>").appendTo(me.page.main);
			me.run();
		},
		
		run: function () {
			var me = frappe.pipal_employee_dashboard;
			frappe.call({
				method: "hrms.hr.page.pipal_employee_dashboard.pipal_employee_dashboard.getDashboardData",
				args: {
					start: me.start,
				},
				callback: function (response){
					if (response.message && response.message.length > 0)
					{	
						me.manager_data = response.message;
						me.send_data(me.manager_data)
						response.message.forEach(function (data) {
							if (data) {
							}else{
								frappe.show_alert({ message: __("Data Not Found ! "), indicator: "gray" });
							}
						});
					}
					else
					{
						$('#page-pipal-employee-dashboard').addClass('hidden')
					}
				},
			});
			me.updateTime();
		},

		send_data: function (data) 
		{	
			emp_data = data[0].employee[0];
			employee_name = emp_data['employee_name'];
			designation = emp_data['designation'];
			me.emp_id = emp_data['id'];
			me.default_shift = emp_data['default_shift'];
			emp_image = emp_data['image'];
			emp_image = emp_image ? emp_image : "/assets/hrms/images/user_employee.png";

			me.checkInLogType = data[1]['valid_log_type'];

			payslip_val = data[3]['payslip'][0]
			this.showPayslip(payslip_val)

			me.holiday_element = this.displayUpcomingHoliday(data[4]['holiday_data'])

			emp_declaration = data[5]['employee_declaration']
			this.showDeclaration(emp_declaration)

			emp_proof_submission = data[6]['employee_tax_proof']
			this.showProofSubmission(emp_proof_submission)

			this.showGreeting();

			$(frappe.render_template("pipal_employee_dashboard",data)).appendTo(me.page.main);
			this.startClock()
			this.showHideDeclarationData(emp_declaration)
			this.showHideProofSubmissionData(emp_proof_submission)
			payslip_val['name'] ? "" : $('.payslip_card').remove();
			this.salaryPiechart(payslip_val);

			if (me.manager_data[2]['todaysSwipe'].length > 0) {
				$('#view-swipe').removeClass('hide');
			}
			this.toggleLeaveLinks()
		},

		checkInOut: function (check_type) {
			frappe.db.insert({
				doctype: 'Employee Checkin',
				employee : me.emp_id,
				log_type: check_type
			}).then(doc => {
				if (doc.log_type == "IN") {
					me.checkInLogType = "OUT"
					frappe.show_alert({ message: __("Signed In Successfully ! "), indicator: "green" });
					this.callRefreshData()
				} else {
					me.checkInLogType = "IN"
					frappe.show_alert({ message: __("Signed Out Successfully ! "), indicator: "green" });
				}

				$('#check-in-out-btn').text("Check " + me.checkInLogType)
				if (me.manager_data[2]['todaysSwipe'].length) {
					$('#view-swipe').removeClass('hide');
					this.callRefreshData()
				}
			});
		},

		viewSwipe: function () {
			var todays_swipe = me.manager_data[2];
			var swipe_data = todays_swipe['todaysSwipe'];
			
			// Get today's date info
			var today = new Date();
			var dateOptions = { year: 'numeric', month: 'long', day: 'numeric' };
			var todayFormatted = today.toLocaleDateString('en-US', dateOptions);
			var dayName = today.toLocaleDateString('en-US', { weekday: 'long' });
			
			// Create modal HTML
			var modalHTML = `
				<div class="swipe-modal-overlay" id="swipeModalOverlay">
					<div class="swipe-modal">
						<div class="swipe-modal-header">
							<h3><i class="fa fa-clock-o"></i> Today's Attendance</h3>
							<button class="swipe-modal-close" onclick="me.closeSwipeModal()">
								<i class="fa fa-times"></i>
							</button>
						</div>
						<div class="swipe-modal-body">
							<div class="swipe-info-section">
								<div class="swipe-info-row">
									<span class="swipe-info-label">Date</span>
									<span class="swipe-info-value">${todayFormatted}</span>
								</div>
								<div class="swipe-info-row">
									<span class="swipe-info-label">Day</span>
									<span class="swipe-info-value">${dayName}</span>
								</div>
								<div class="swipe-info-row">
									<span class="swipe-info-label">Shift</span>
									<span class="swipe-info-value">${me.default_shift || 'N/A'}</span>
								</div>
							</div>
							
							<div class="swipe-list-title">
								<i class="fa fa-history"></i> Swipe Records
							</div>
							<div class="swipe-list">
			`;
			
			// Add swipe records
			if (swipe_data && swipe_data.length > 0) {
				swipe_data.forEach(function(swipe) {
					var badgeClass = swipe.log_type === 'IN' ? 'badge-in' : 'badge-out';
					modalHTML += `
						<div class="swipe-item">
							<span class="swipe-item-badge ${badgeClass}">${swipe.log_type}</span>
							<span class="swipe-item-time">${swipe.time}</span>
						</div>
					`;
				});
			} else {
				modalHTML += `
					<div class="swipe-empty">
						<p>No swipe records for today</p>
					</div>
				`;
			}
			
			modalHTML += `
							</div>
						</div>
					</div>
				</div>
			`;
			
			// Append modal to body
			$('body').append(modalHTML);
			
			// Close on overlay click
			$('#swipeModalOverlay').on('click', function(e) {
				if (e.target.id === 'swipeModalOverlay') {
					me.closeSwipeModal();
				}
			});
			
			// Close on ESC key
			$(document).on('keydown.swipeModal', function(e) {
				if (e.key === 'Escape') {
					me.closeSwipeModal();
				}
			});
		},

		closeSwipeModal: function() {
			$('#swipeModalOverlay').fadeOut(200, function() {
				$(this).remove();
			});
			$(document).off('keydown.swipeModal');
		},

		callRefreshData: function () {
			frappe.call({
				method: "hrms.hr.page.pipal_employee_dashboard.pipal_employee_dashboard.getDashboardData",
				args: {
					start: me.start,
				},
				callback: function (response) {
					if (response.message && response.message.length > 0) {
						me.manager_data = response.message;
						if (me.manager_data[2]['todaysSwipe'].length) {
							$('#view-swipe').removeClass('hide');
						}
					} else {
						frappe.show_alert({ message: __("No more updates"), indicator: "gray" });
						me.more.parent().addClass("hidden");
					}
				},
			});
		},
		
		ShowHideSalary: function (text_val) {
			if (text_val == "Show") {
				me.toggle_salary = "Hide"
				$('#pay_gross_pay').text(pay_gross_pay)
				$('#pay_total_deduction').text(pay_total_deduction)
				$('#pay_net_pay').text(pay_net_pay)
			} else {
				me.toggle_salary = "Show"
				$('#pay_gross_pay').text("*****")
				$('#pay_total_deduction').text("*****")
				$('#pay_net_pay').text("*****")
			}
			$('#salary-toggle').text(me.toggle_salary)
		},
		
		displayUpcomingHoliday: function (holiday_array) {
			me.holiday_element = "<div>"
			for (i = 0; i < holiday_array.length; i++) {
				me.holiday_element += ` <div class="hld_item"><b>${holiday_array[i]['holiday_date']}</b> <span>${holiday_array[i]['holiday_day']} </span>
				<br>
				<span>${holiday_array[i]['description']}</span>  
				<br></div>`
			}
			me.holiday_element += "</div>"
			return me.holiday_element
		},
		
		showPayslip: function (payslip_val) {
			slip_name = payslip_val['name']
			slip_company = payslip_val['company']
			pay_currency = payslip_val['currency'];
			pay_month_date = payslip_val['start_date'];
			pay_payment_days = payslip_val['payment_days'];
			pay_gross_pay = payslip_val['gross_pay'];
			pay_net_pay = payslip_val['net_pay'];
			pay_total_deduction = payslip_val['total_deduction'];
		},

		showDeclaration: function (emp_declaration) {
			emp_declaration_currency = emp_declaration[0]['currency']
			total_declared_amount = emp_declaration[0]['total_declared_amount']
			total_exemption_amount = emp_declaration[0]['total_exemption_amount']
		},

		showHideDeclarationData: function (emp_declaration) {
			if (emp_declaration[0]['employee']) {
				$('.declaration_not_found').remove()
			} else {
				$('#declaration_data').remove()
			}
		},

		showProofSubmission: function (emp_proof_submission) {
			proof_currency = emp_proof_submission[0]['currency'];
			proof_total_actual_amount = emp_proof_submission[0]['total_actual_amount'];
			proof_exemption_amount = emp_proof_submission[0]['exemption_amount'];
		},

		showHideProofSubmissionData: function (emp_proof_submission) {
			if (emp_proof_submission[0]['employee']) {
				$('.proof_not_found').remove()
			} else {
				$('#proof_data').remove()
			}
		},

		displayGreeting: function (greeting) {
			if (hour < 12) {
				greeting = "Good Morning";
			} else if (hour < 17) {
				greeting = "Good Afternoon";
			} else {
				greeting = "Good Evening";
			}
			return greeting
		},

		showGreeting: function () {
			user_email = frappe.session.user_email;
			user_avatar = frappe.avatar(user_email);
			greetingMessage = "Good Morning";
			now = new Date();
			hour = now.getHours();
			minute = now.getMinutes();
			seconds = now.getSeconds();
			formattedTime = hour + ":" + minute + ":" + seconds;

			dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
			dayOfWeek = dayNames[now.getDay()];
			dayOfMonth = now.getDate();
			monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
			month = monthNames[now.getMonth()];
			year = now.getFullYear();
			formattedDate = dayOfMonth + " " + month + " " + year;

			full_date = ""
			greetingMessage = me.displayGreeting(greetingMessage);
		},

		updateTime: function () {
			frappe.call({
				method: "hrms.hr.page.pipal_employee_dashboard.pipal_employee_dashboard.get_server_time",
				callback: function (r) {
					if (r.message && r.message.server_time) {
						me.startClock(r.message.server_time);
					}
				}
			});
		},

		startClock: function (server_time) {
			if(server_time){
				let currentTime = new Date(server_time); 
				setInterval(function () {
					currentTime.setSeconds(currentTime.getSeconds() + 1);
					$('#liveTime').text(currentTime.toLocaleTimeString());
				}, 1000);
			}
		},


		salaryPiechart: function (payslip_val) {
			try {
				// Store payslip_val for later use
				this.currentPayslipVal = payslip_val;
				
				// Wait for DOM to be ready
				setTimeout(() => {
					this.drawPieChart(payslip_val);
				}, 100);
				
				// Remove old event listeners if they exist
				if (this.resizeHandler) {
					window.removeEventListener('resize', this.resizeHandler);
				}
				
				// Create bound function that includes payslip_val
				this.resizeHandler = () => {
					this.drawPieChart(this.currentPayslipVal);
				};
				
				// Add new listener with bound function
				window.addEventListener('resize', this.resizeHandler);
				
			} catch (error) {
				console.log(error);
			}
		},

		// Rename adjustCanvasForZoom to drawPieChart and accept parameter
		drawPieChart: function(payslip_val) {
			let canvas = document.getElementById('pieChart');
			if (!canvas) {
				console.warn("Canvas element not found");
				return;
			}

			// Detect zoom level
			let zoomLevel = window.devicePixelRatio * 100;
			let scaleFactor = 1;

			if (zoomLevel <= 100) {
				scaleFactor = 1;
			} else if (zoomLevel <= 200) {
				scaleFactor = 2;
			} else if (zoomLevel <= 300) {
				scaleFactor = 3;
			} else if (zoomLevel <= 400) {
				scaleFactor = 4;
			} else if (zoomLevel <= 500 || zoomLevel > 500) {
				scaleFactor = 5;
			}

			canvas.width = canvas.offsetWidth * scaleFactor;
			canvas.height = canvas.offsetHeight * scaleFactor;
			canvas.style.width = `${canvas.width / scaleFactor}px`;
			canvas.style.height = `${canvas.height / scaleFactor}px`;

			let ctx = canvas.getContext('2d');
			ctx.scale(scaleFactor, scaleFactor);

			let gross_pay = payslip_val['gross_pay'];
			let total_deduction = payslip_val['total_deduction'];
			let net_pay = gross_pay - total_deduction;

			let outerRadius = (canvas.width / 2 / scaleFactor) - 10;
			let innerRadius = canvas.width / 4 / scaleFactor;

			let netPayAngle = (total_deduction / gross_pay) * 2 * Math.PI;
			let deductionAngle = (net_pay / gross_pay) * 2 * Math.PI;

			// Draw payment days section
			ctx.beginPath();
			ctx.moveTo(canvas.width / 2 / scaleFactor, canvas.height / 2 / scaleFactor);
			ctx.arc(canvas.width / 2 / scaleFactor, canvas.height / 2 / scaleFactor, outerRadius, 0, netPayAngle);
			ctx.fillStyle = '#B9E3C6';
			ctx.fill();
			ctx.closePath();

			// Draw leave day section
			ctx.beginPath();
			ctx.moveTo(canvas.width / 2 / scaleFactor, canvas.height / 2 / scaleFactor);
			ctx.arc(canvas.width / 2 / scaleFactor, canvas.height / 2 / scaleFactor, outerRadius, netPayAngle, netPayAngle + deductionAngle);
			ctx.fillStyle = '#1C7293';
			ctx.fill();
			ctx.closePath();

			// Draw the inner circle (cutout)
			ctx.beginPath();
			ctx.arc(canvas.width / 2 / scaleFactor, canvas.height / 2 / scaleFactor, innerRadius, 0, 2 * Math.PI);
			ctx.fillStyle = '#FFFFFF';
			ctx.fill();
			ctx.closePath();

			// Draw the border
			ctx.beginPath();
			ctx.arc(canvas.width / 2 / scaleFactor, canvas.height / 2 / scaleFactor, outerRadius + 6, 0, 2 * Math.PI);
			ctx.strokeStyle = '#000000';
			ctx.lineWidth = 4;
			ctx.stroke();
			ctx.closePath();
		},

		waitLoad: function() {
			$('#payslip_download_link').addClass('hide');
			frappe.show_alert({ message: __("Wait Loading ! "), indicator: "gray" });
			setTimeout(function() {
				$('#payslip_download_link').removeClass('hide');
			}, 5000);
		},
		
		toggleLeaveLinks: function() {
			$(document).ready(function() {
				$('.parent-link > a').click(function(e) {
					e.preventDefault();
					
					// Get the parent link element
					var $parentLink = $(this).parent();
					
					// Check if this link is already active
					var isActive = $parentLink.hasClass('active');
					
					// Close all other parent links
					$('.parent-link').not($parentLink).removeClass('active');
					$('.parent-link').not($parentLink).find('.child-links').slideUp(200);
					
					// Toggle the clicked parent link
					if (isActive) {
						$parentLink.removeClass('active');
						$parentLink.find('.child-links').slideUp(200);
					} else {
						$parentLink.addClass('active');
						$parentLink.find('.child-links').slideDown(200);
					}
				});
			});
		},
	}
}
else{
	frappe.show_alert({ message: __("Role Not Defined !"), indicator: "red" });
}