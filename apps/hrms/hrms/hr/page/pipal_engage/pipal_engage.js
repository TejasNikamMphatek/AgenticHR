frappe.pages['pipal-engage'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Engage',
		single_column: true
	});
	me = frappe.pipal_engage;
	frappe.pipal_engage.make(page);
}


	frappe.pipal_engage = {
	    start : 0,
		engage_data : '',
		birth_element : '',
		anni_element : '',
		recently_joiner : '',
		bithday_count : '',
		anniversary_count : '',
		joiny_count : '',
		make: function (page) {
			me.page = page;
			me.body = $("<div></div>").appendTo(me.page.main);
			me.run();
		},
		run: function () {
			var me = frappe.pipal_engage;
			frappe.call({
				method: "hrms.hr.page.pipal_engage.pipal_engage.getEngageData",
				args: {
					start: me.start,
				},
				callback: function (response){
					if (response.message && response.message.length > 0)
					{	
						me.engage_data = response.message;
						me.send_data(me.engage_data)
						response.message.forEach(function (data) {
							if (data) {
							}else{
								frappe.show_alert({ message: __("Data Not Found ! "), indicator: "gray" });
							}
						});
					}
					else
					{
						$('#page-pipal-engage').addClass('hidden')
					}
				},
			});

			window.onpopstate = function(event) {
				window.location.reload();
			};
		},

		send_data: function (engage_data) 
		{	
			console.log("engage_data",engage_data)
			me.birth_element = this.birthDayEmployee(engage_data[0]['birth_emp']);
			me.anni_emp_ele = this.AnniversaryEmployee(engage_data[0]['anni_emp']);
			me.recently_joiner = this.recentlyJoiner(engage_data[0]['latest_joiners'])
			$(frappe.render_template("pipal_engage")).appendTo(me.page.main);
			this.DataNotAvailabe()
		},

		birthDayEmployee: function(birday_arr){
			me.bithday_count = birday_arr.length;
			
			let birth_emp_ele = "";
			for (let i = 0; i < birday_arr.length; i++) {
				birday_arr[i]['image'] = birday_arr[i]['image'] || "/assets/hrms/images/user_employee.png"
				birth_emp_ele += `
				<div class="card p-3 mb-2">
                    <div class="row">
                        <div class="col-6">
                            <img src="/assets/hrms/images/mphatek_logo_tm black.png" class="comp-logo" alt="company_logo">
                        </div>
                        <div class="col-6 text-right">
                            ${birday_arr[i]['days_until_birthday']}
                        </div>
                        <div class="col-md-5 col-sm-10 text-center">
                            <img src="/assets/hrms/images/birthday.svg" alt="birthday-banner" class="celebartion-poster">
                        </div>
                        <div class="col-md-7 birthay-content p-2">
                            <span>Happy Birthday ${birday_arr[i]['employee_name']} , Have a great year ahead!</span>
                            <br>
                            <div class="mt-3 d-flex justify-content-center align-items-center">
                                <img class="birth_image" src="${birday_arr[i]['image']}" alt="user_image">
                                <b>Happy Birthday, ${birday_arr[i]['employee_name']}!</b>
                            </div>
                        </div>
                    </div>
                </div>
				`
			}
			return birth_emp_ele;
		},

		AnniversaryEmployee: function(anni_arr){
			me.anniversary_count = anni_arr.length;
			let anni_emp_ele = "";
			for (let i = 0; i < anni_arr.length; i++) {
				anni_arr[i]['image'] = anni_arr[i]['image'] || "/assets/hrms/images/user_employee.png"
				anni_emp_ele += `
				<div class="card p-3 mb-2">
                    <div class="row">
                        <div class="col-6">
                            <img src="/assets/hrms/images/mphatek_logo_tm black.png" class="comp-logo" alt="company_logo">
                        </div>
                        <div class="col-6 text-right">
                            ${anni_arr[i]['days_until_anniversary']}
                        </div>
                        <div class="col-md-5 col-sm-10 text-center">
                            <img src="/assets/hrms/images/work_anniversary.svg" alt="birthday-banner" class="celebartion-poster">
                        </div>
                        <div class="col-md-7 birthay-content p-2">
                            <span>Our congratulations to ${anni_arr[i]['employee_name']} on completing ${anni_arr[i]['employee_completed_year']} successful year(s).</span>
                            <br>
                            <div class="mt-3 d-flex justify-content-center align-items-center">
                                <img class="birth_image" src="${anni_arr[i]['image']}" alt="user_image">
                                <b>Congratulations, ${anni_arr[i]['employee_name']}!</b>
                            </div>
                        </div>
                    </div>
                </div>
				`
			}
			return anni_emp_ele;
		},

		recentlyJoiner: function(recently_joiner_arr) {
			me.joiny_count = recently_joiner_arr.length;
			let recently_joiner_ele = "";
			for (let i = 0; i < recently_joiner_arr.length; i++) {
				recently_joiner_arr[i]['image'] = recently_joiner_arr[i]['image'] || "/assets/hrms/images/user_employee.png"
				recently_joiner_ele += `
				<div class="card p-3 mb-2">
                    <div class="row">
                        <div class="col-6">
                            <img src="/assets/hrms/images/mphatek_logo_tm black.png" class="comp-logo" alt="company_logo">
                        </div>
                        <div class="col-6 text-right">
                            ${recently_joiner_arr[i]['days_since_joining']}
                        </div>
                        <div class="col-md-5 col-sm-10 text-center">
                            <img src="/assets/hrms/images/recently_joiner.svg" alt="birthday-banner" class="celebartion-poster">
                        </div>
                        <div class="col-md-7 birthay-content p-2">
                            <span>Congratulations to ${recently_joiner_arr[i]['employee_name']} recently Join.</span>
                            <br>
                            <div class="mt-3 d-flex justify-content-center align-items-center">
                                <img class="birth_image" src="${recently_joiner_arr[i]['image']}" alt="user_image">
                                <b>Congratulations, ${recently_joiner_arr[i]['employee_name']}!</b>
                            </div>
                        </div>
                    </div>
                </div>
				`
			}
			return recently_joiner_ele;
		},
		showHideData:function(value) {
			if (value === "birthday"){
				$('.birthday_section').removeClass('hide')
				$('.anniversary_section').addClass('hide')
				$('.joiny_section').addClass('hide')
			}else if(value === "anniversary"){
				$('.birthday_section').addClass('hide')
				$('.anniversary_section').removeClass('hide')
				$('.joiny_section').addClass('hide')

			}else if(value === "new_joiny"){
				$('.birthday_section').addClass('hide')
				$('.anniversary_section').addClass('hide')
				$('.joiny_section').removeClass('hide')
			}else if(value === "all"){
				$('.birthday_section').removeClass('hide')
				$('.anniversary_section').removeClass('hide')
				$('.joiny_section').removeClass('hide')
				console("invalid selection")
			}
		},

		DataNotAvailabe: function(){
			if (me.joiny_count < 1){
				$('.joiny_section').hide()
			}
			if (me.anniversary_count < 1){
                $('.anniversary_section').hide()
            }
			if (me.bithday_count < 1){
                $('.birthday_section').hide()
            }
		}

}
