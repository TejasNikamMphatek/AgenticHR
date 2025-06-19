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
	start: 0,
	holiday_list: [],
	holiday_month_card: "",
	holidays_select_options: "",
	
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
			callback: function (response) {
				if (response.message && response.message.length > 0) {	
					me.holiday_list = response.message;
					me.send_data(me.holiday_list);
					response.message.forEach(function (data) {
						if (!data) {
							frappe.show_alert({ message: __("Data Not Found!"), indicator: "gray" });
						}
					});
				} else {
					$('#page-holiday-calendar').addClass('hidden');
				}
			},
		});
	},

	send_data: function (data) {	
		console.log("holiday data::::::", data);
		me.holidays_select_options = this.holidayListNames(data[0]['holiday_list_names']);
		me.holiday_month_card = this.holidayCal(data[0]['holiday_list']);
		
		// Clear existing content before appending new
		me.body.empty();
		$(frappe.render_template("holiday_calendar")).appendTo(me.body);
	},

	holidayCal: function(holiday_groups) {
		let monthCard = "";
		for (const [month, holidaysList] of Object.entries(holiday_groups)) {
			monthCard += `
				<div class="col-md-3 col-sm-6 col-xs-12 monthCard">
					<div class="card">
						<strong class="month_name text-uppercase">${month}</strong>
			`;
			
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
	},

	holidayListNames: function(Hlist) {
		if (!Array.isArray(Hlist) || Hlist.length === 0) {
			return '<select class="form-control p-2 px-4" name="holiday_list_name" id="holiday_list_name"><option>No holidays available</option></select>';
		}

		const options = Hlist.map(item => {
			const name = item.holiday_list_name;
			return `<option value="${name}">${name}</option>`;
		}).join('');

		return `<select class="form-control p-2 px-2" name="holiday_list_name" id="holiday_list_name" onchange="frappe.holiday_calendar.getHolidayListData(this.value)">
			<option value="" disabled selected>Select Holiday List</option>
			${options}
		</select>`;
	},

	getHolidayListData: function(selectedValue) {
		var me = frappe.holiday_calendar;
		frappe.call({
			method: "hrms.hr.page.holiday_calendar.holiday_calendar.getHolidayData",
			args: {
				start: me.start,
				hlist: selectedValue
			},
			callback: function (response) {
				if (response.message && response.message.length > 0) {	
					me.holiday_list = response.message;
					me.holiday_month_card = me.holidayCal(response.message[0]['holiday_list']);
					
					// Update only the calendar part, keep the dropdown
					$('.monthCard').remove();
					$(me.holiday_month_card).appendTo(me.body.find('.row').first());
					
					response.message.forEach(function (data) {
						if (!data) {
							frappe.show_alert({ message: __("Data Not Found!"), indicator: "gray" });
						}
					});
				} else {
					$('#page-holiday-calendar').addClass('hidden');
				}
			},
		});
	}
}