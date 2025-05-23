if(!frappe.user.has_role("System Manager") || frappe.user.has_role("Administrator") )
{
	window.location.replace('/app/pipal-employee-dashboard')
}else if(frappe.user.has_role(["HR Manager","Accounts"])){
	
	frappe.pages['pipal-hr-dashboard'].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Pipal HR Dashboard',
			single_column: true
		});
		me = frappe.pipal_hr_dashboard;
		frappe.pipal_hr_dashboard.make(page);
	};

	frappe.pipal_hr_dashboard = {
		start: 0,
		pending_confirmation : '',
		resign_count : '',
		att_req_count : '',
		leave_app_count : '',
		help_desk_count : '',
		anniver_slide : '',
		birthday_slide : '',
		user_profile : '',
		make: function (page) 
		{
			var me = frappe.pipal_hr_dashboard;
			me.page = page;
			me.run();
		},
		run: function () {
			var me = frappe.pipal_hr_dashboard;
			frappe.call({
				method: "hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.getDashboardData",
				args: {
					start: me.start,
				},
				callback: function (response) {
					if (response.message && response.message.length > 0) {
						me.send_data(response.message);
						response.message.forEach(function (d) {
							if (d) {
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
			$('.page-head').addClass('hide');
		},

		send_data: function(data) 
		{
			// console.log("main data = ",data)
			me.pending_confirmation = data[0]['probation_employee'].length;
			me.resign_count = data[0]['resign_emp'].length;
			me.att_req_count = data[0]['attendance_req'].length;
			me.leave_app_count = data[0]['leave_application'].length;
			me.help_desk_count = data[0]['help_desk_request'].length;
			me.anniver_slide = this.anniEmpSlider(data[0]['anni_emp']);
			me.birthday_slide = this.birthdayEmpSlider(data[0]['birthday_employee'])
			this.showGreeting();
			me.user_profile = this.showUserProfile(data[0]['login_user'])
			$(frappe.render_template("pipal_hr_dashboard", data)).appendTo(me.page.main);
			this.runSlides()
			this.showHideSlider(data[0]['anni_emp'],data[0]['birthday_employee'])
			// $('.sticky-top').removeClass()
			// this.pageRefresh();
		},

		anniEmpSlider: function(anni_emp) {
			let slide = '';
			let isActiveSet = false; // Flag to track if the active class has been set
		
			for (let i = 0; i < anni_emp.length; i++) {
				emp_image = anni_emp[i]['image'] || '/assets/hrms/images/user_employee.png';
		
				if (anni_emp[i]['employee_completed_year'] == 0) {
					continue;
				}
		
				// Add the active class only to the first valid slide
				slide += `
					<div class="carousel-item ${!isActiveSet ? 'active' : ''}" data-interval="1000">
						<div class="card text-center p-2">
							<div class="text-center">
								<img width="50px" src="${emp_image}" />
							</div>
							<b>${anni_emp[i]['employee_completed_year']} Year Completed</b><br>
							<p>Yay! Today is ${anni_emp[i]['employee_name']} Work Anniversary</p><br>
							<button class="btn btn-info btn-sm btn-send-wish" onclick="me.sendAnniversaryWish(${anni_emp[i]['employee']})">
								Send a Wish!
							</button>
						</div>
					</div>
				`;
		
				isActiveSet = true; // Set the flag after assigning the active class
			}
		
			return slide;
		},
		
		birthdayEmpSlider: function(birthday_emp){
			slide = '';
			for (let i = 0; i < birthday_emp.length; i++) 
			{
				emp_image = birthday_emp[i]['image'] || '/assets/hrms/images/user_employee.png';
				slide += `  <div class="carousel-item ${i==0 ? 'active' : ''}" data-interval="1000">
								<div class="card  text-center p-2">
									<div class="text-center">
										<img width="50px" src="${emp_image}" />
									</div>
									<strong>Happy Birthday</strong> <br>
									<p>Yay ! Today is ${birthday_emp[i]['employee_name']} Birthday</p>
									<br>
									<button class="btn btn-info btn-sm btn-send-wish" onclick = "me.sendBirthdayWish(${birthday_emp[i]['employee']})">
										Send a Wish!
									</button>
								</div>
							</div>  `
			}
			return slide;
		},

		sendAnniversaryWish: function(wish_emp){
			frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendAnniversaryWish`, {
				employee: wish_emp
			}).then(r => {
				// console.log(r.message)
			})

		},
		sendToAllAnniversaryWish: function(){
			frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendToAllAnniversaryWish`, 
				{}).then(r => {
				// console.log(r.message)
			})
		},

		sendBirthdayWish:function(birth_emp){
			frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendBirthdayWish`, {
				employee: birth_emp
			}).then(r => {
			// console.log(r.message)
            })
		},

		sendToAllBirthDayWish:function(){
			frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendToAllBirthdayWish`, 
				{}).then(r => {
				// console.log(r.message)
			})
		},

		showHideSlider: function(anni_arr=[], birth_arr=[]){

			if(anni_arr.length < 1 || me.anniver_slide == ""){
				$('.anniver_slide').hide()
			}

			if(birth_arr.length < 1){
				$('.birthday_slide').hide()
			}
		},

		get_default_recipients(fieldname) {
			if (this.frm?.events.get_email_recipients) {
				return (this.frm.events.get_email_recipients(this.frm, fieldname) || []).join(", ");
			} else {
				return "";
			}
		},
		displayGreeting: function(greeting){
			if (hour < 12) {
				greeting = "Good Morning";
			} else if (hour < 17) {
				greeting = "Good Afternoon";
			} else {
				greeting = "Good Evening";
			}
			return greeting
		},

		showGreeting:function(){
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

		runSlides(){
			setInterval(() => {
				$('#carouselAnniversaryInterval').carousel({
					interval: 1000
				});
				$('#carouselBirthdayInterval').carousel({
					interval: 1000
				});		
			}, 3000);
		},

		toggleSideBar:function(){
			alert("Toggle sidebar")
		},

		showUserProfile :function(user_data){
			user_image = user_data[0]['user_image'] || "/assets/hrms/images/user_employee.png";
			role_profile = user_data[0]['role_profile_name'] || "";
			user_profile = `
			<div class="user-info">
				<div class="image">
					<a href=""><img src="${user_image}" alt="User"></a>
				</div>
				<div class="detail">
					<h4>${user_data[0]['full_name']}</h4>
					<small>${role_profile}</small>                        
				</div>
				<a href="javascript:void(0);" class="fullscreen hidden-sm-down" data-provide="fullscreen" data-close="true"><i class="zmdi zmdi-fullscreen"></i></a>
            	<a href="javascript:void(0);" class="js-right-sidebar" data-close="true"><i class="zmdi zmdi-settings zmdi-hc-spin"></i></a>
			</div>
			
			`
			return user_profile;
		},
		
		pageRefresh:function(){
			var current_url = window.location.pathname;
			leftSidebar = "";
			if (current_url == "/app/pipal-hr-dashboard"){
				leftSidebar = $("#leftsidebar").css("marginTop", "0px");
			} else {
				leftSidebar = $("#leftsidebar").css("marginTop", "55px");
			}

			setInterval(function() {
				$("#leftsidebar").css("marginTop", "0px");
			}, 1000);
		}

				
	}
}else{
	frappe.show_alert({ message: __("Role Not Defined .... !"), indicator: "red" });
}

