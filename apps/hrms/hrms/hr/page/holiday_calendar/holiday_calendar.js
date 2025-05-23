frappe.pages['holiday-calendar'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Holiday Calendar',
		single_column: true
	});
	me = frappe.holiday_calendar;
	frappe.holiday_calendar.make(page);
}
	frappe.holiday_calendar = {
	    start : 0,
		holiday_list : [],
		holiday_month_card : "",
		make: function (page) {
			me.page = page;
			me.body = $("<div></div>").appendTo(me.page.main);
			me.run();
		},
		run: function () {
			var me = frappe.holiday_calendar;
			frappe.call({
				method: "hrms.hr.page.holiday_calendar.holiday_calendar.getHolidayData",
				args: {
					start: me.start,
				},
				callback: function (response){
					if (response.message && response.message.length > 0)
					{	
						me.holiday_list = response.message;
						me.send_data(me.holiday_list)
						response.message.forEach(function (data) {
							if (data) {
							}else{
								frappe.show_alert({ message: __("Data Not Found ! "), indicator: "gray" });
							}
						});
					}
					else
					{
						$('#page-holiday-calendar').addClass('hidden')
					}
				},
			});
		},

		send_data: function (data) 
		{	
			console.log("holiday data",data)
			me.holiday_month_card = this.holidayCal(data[0]['holiday_list']);
			$(frappe.render_template("holiday_calendar")).appendTo(me.page.main);
			// console.log(me.holiday_month_card)
		},

		holidayCal: function(holiday_groups)
		{
			let monthCard = "";
			for (const [month, holidaysList] of Object.entries(holiday_groups)) {
				// Create a card for the month
			monthCard += `
					<div class="col-md-3 col-sm-6 col-xs-12 monthCard">
						<div class="card">
							<strong class="month_name text-uppercase">${month}</strong>
				`;
				
				// Check if holidays are available in this month
				if (holidaysList.length > 0) {
					holidaysList.forEach(holiday => {
						monthCard += `
							<div class="row mb-3 holiday-item">
								<div class="col-4">
									<h3>${holiday.date}</h3>
									<span>${holiday.day}</span>
								</div>
								<div class="col-8">
									<span>${holiday.description}</span>
								</div>
							</div>
						`;
					});
				} else {
					// Show "No holidays" message if there are no holidays in the month
					monthCard += `
						<div class="row no_holiday">
							<div class="col-12">
								<span>No Holidays</span>
							</div>
						</div>
					`;
				}

				monthCard += `
                        </div>
                    </div>
                `;
			}
			return monthCard;

		}

}
