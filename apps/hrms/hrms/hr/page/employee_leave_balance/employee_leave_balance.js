frappe.pages['employee-leave-balance'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Employee Leave Balance',
		single_column: true
	});

	frappe.employee_leave_balance = new EmployeeLeaveBalance(page);
};

class EmployeeLeaveBalance {
	constructor(page) {
		this.page = page;
		this.body = $('<div></div>').appendTo(this.page.main);
		this.filters = {};
		this.data = [];
		this.current_year = new Date().getFullYear();
		this.init();
	}

	init() {
		this.setup_filters();
		this.setup_buttons();
		this.load_data();
	}

	setup_filters() {
		// Create filter area
		this.filter_area = $(`
			<div class="container my-2 p-3" style="background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
				<div class="form-group">
					<div class="row">
						<div class="col-md-3">
							<label class= "mb-0">${__('Employee')}</label>
							<div class="employee-filter"></div>
						</div>

						<div class="col-md-3">
							<label class= "mb-0">${__('Leave Type')}</label>
							<div class="leave-type-filter"></div>
						</div>

						<div class="col-md-3">
							<label class= "mb-0">${__('Year')}</label>
							<div class="year-filter"></div>
						</div>

						<div class="col-md-3 d-flex flex-column justify-content-center">
							<div class="mt-5">
								<button class="btn btn-primary btn-apply-filters">
									<i class="fa fa-search"></i> ${__('Apply')}
								</button>

								<button class="btn btn-default btn-reset-filters ml-4">
									${__('Reset')}
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`).appendTo(this.body);

		// Employee filter
		this.employee_filter = frappe.ui.form.make_control({
			parent: this.filter_area.find('.employee-filter'),
			df: {
				fieldtype: 'Link',
				options: 'Employee',
				placeholder: __('Select Employee')
			},
			render_input: true
		});

		// Leave Type filter
		this.leave_type_filter = frappe.ui.form.make_control({
			parent: this.filter_area.find('.leave-type-filter'),
			df: {
				fieldtype: 'Link',
				options: 'Leave Type',
				placeholder: __('Select Leave Type')
			},
			render_input: true
		});

		// Year filter
		this.year_filter = frappe.ui.form.make_control({
			parent: this.filter_area.find('.year-filter'),
			df: {
				fieldtype: 'Select',
				options: this.get_year_options(),
				default: this.current_year.toString(),
				placeholder: __('Select Year')
			},
			render_input: true
		});

		// Set default year
		this.year_filter.set_value(this.current_year.toString());

		// Add event listeners
		this.filter_area.find('.btn-apply-filters').on('click', () => this.refresh_data());
		this.filter_area.find('.btn-reset-filters').on('click', () => this.reset_filters());
	}

	get_year_options() {
		const currentYear = new Date().getFullYear();
		const years = [];
		for (let i = currentYear - 2; i <= currentYear + 1; i++) {
			years.push(i.toString());
		}
		return years.join('\n');
	}

	setup_buttons() {
		// Add refresh button
		// this.page.set_primary_action(__('Download'), () => {
		// 	this.export_data();
		// }, 'download');

		// // Add export button
		// this.page.add_menu_item(__('Export Excel'), () => {
		// 	this.export_data();
		// }, true);

		// // Add print button
		// this.page.add_menu_item(__('Print'), () => {
		// 	this.print_report();
		// }, true);
	}

	get_filters() {
		return {
			employee: this.employee_filter.get_value(),
			leave_type: this.leave_type_filter.get_value(),
			year: this.year_filter.get_value() || this.current_year.toString()
		};
	}

	reset_filters() {
		this.employee_filter.set_value('');
		this.leave_type_filter.set_value('');
		this.year_filter.set_value(this.current_year.toString());
		this.refresh_data();
	}

	load_data() {
		this.show_loading();
		const filters = this.get_filters();
		console.log('Loading data with filters:', filters);
		
		frappe.call({
			method: "hrms.hr.page.employee_leave_balance.employee_leave_balance.get_employee_leave_balance",
			args: filters,
			callback: (response) => {
				console.log('Response received:', response);
				this.hide_loading();
				if (response.message && response.message.length > 0) {
	// Round numeric fields to 1 decimal place for each record
	this.data = response.message.map(item => {
	const granted = Number(item.total_allocated || 0);
	const balance = Number(item.balance || 0);
	const consumed = granted - balance;

	return {
		...item,
		total_allocated: granted.toFixed(1),
		total_leaves_taken: Number(item.total_leaves_taken || 0).toFixed(2),
		balance: balance.toFixed(2),
		total_applications: Number(item.total_applications || 0).toFixed(0),
		consumed: consumed.toFixed(2)  // 👈 Add this line
	};
});

	this.render_data();
}

				else {
					this.show_empty_state();
				}
			},
			error: (error) => {
				this.hide_loading();
				frappe.show_alert({
					message: __('Error loading data'),
					indicator: 'red'
				});
				console.error('Error:', error);
				this.show_empty_state();
			}
		});
	}

	refresh_data() {
		this.load_data();
	}

	render_data() {
		// Clear existing content
		this.body.find('.data-container').remove();
		
		if (!this.data || this.data.length === 0) {
			this.show_empty_state();
			return;
		}

		// Group data by employee if multiple employees
		const groupedData = this.group_data_by_employee();
		
		// Create data container
		this.data_container = $('<div class="data-container"></div>').appendTo(this.body);
		
		// Render each employee's data
		Object.keys(groupedData).forEach(employeeId => {
			const employeeData = groupedData[employeeId];
			const employeeInfo = employeeData[0]; // Get employee info from first record
			
			this.render_employee_section(employeeInfo, employeeData);
		});
	}

	group_data_by_employee() {
		const grouped = {};
		this.data.forEach(record => {
			if (!grouped[record.employee]) {
				grouped[record.employee] = [];
			}
			grouped[record.employee].push(record);
		});
		return grouped;
	}

	render_employee_section(employeeInfo, leaveData) {
		const filters = this.get_filters();
		const selectedYear = filters.year || this.current_year.toString();
		
		// Create employee section
		const employeeSection = $(`
			<div class="employee-section" style="margin-bottom: 30px;">
				<div class="employee-header" style="background: #f8f9fa; padding: 15px; border-radius: 8px 8px 0 0; border-left: 4px solid #17a2b8;">
					<div class="row">
						<div class="col-sm-8">
							<h4 style="margin: 0; color: #495057;">${employeeInfo.employee_name}</h4>
							<p style="margin: 5px 0 0 0; color: #6c757d;">
								<strong>ID:</strong> ${employeeInfo.employee} | 
								<strong>Department:</strong> ${employeeInfo.department || 'N/A'} | 
								<strong>Designation:</strong> ${employeeInfo.designation || 'N/A'}
							</p>
						</div>
						<div class="col-sm-4 text-right">
							<div class="year-selector" style="background: white; padding: 8px 15px; border-radius: 4px; display: inline-block;">
								<i class="fa fa-calendar" style="color: #17a2b8;"></i>
								<strong style="margin-left: 8px; color: #495057;">${selectedYear}</strong>
							</div>
						</div>
					</div>
				</div>
				<div class="leave-cards-container" style="background: white; padding: 20px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
					<div class="row leave-cards-row"></div>
				</div>
			</div>
		`);

		// Add leave type cards
		const cardsRow = employeeSection.find('.leave-cards-row');
		
		leaveData.forEach(leave => {
			const card = this.create_leave_card(leave);
			const cardCol = $('<div class="col-md-3" style="margin-bottom: 20px;"></div>');
			cardCol.append(card);
			cardsRow.append(cardCol);
		});

		this.data_container.append(employeeSection);
	}

	create_leave_card(leaveData) {
		const granted = parseFloat(leaveData.total_allocated || 0);
		const taken = parseFloat(leaveData.total_leaves_taken || 0);
		const balance = parseFloat(leaveData.balance || 0);
		//const consumed = granted - balance;
		const consumed = parseFloat(leaveData.consumed || 0);

		
		// Determine card color based on balance
		let cardColor = '#28a745'; // Green for good balance
		if (balance <= 2) {
			cardColor = '#dc3545'; // Red for low balance
		} else if (balance <= 5) {
			cardColor = '#ffc107'; // Yellow for medium balance
		}

		const card = $(`
			<div class="leave-card" style="
				border: 1px solid #dee2e6; 
				border-radius: 8px; 
				padding: 20px; 
				background: white;
				box-shadow: 0 2px 4px rgba(0,0,0,0.08);
				transition: transform 0.2s, box-shadow 0.2s;
				cursor: pointer;
				height: 220px;
				position: relative;
			" data-employee="${leaveData.employee}" data-leave-type="${leaveData.leave_type}">
				<div style="border-left: 4px solid ${cardColor}; padding-left: 15px; margin-left: -20px; margin-top: -20px; margin-bottom: 15px; padding-top: 20px;">
					<h5">${leaveData.leave_type_name}</h5>
					<p style="color: #6c757d;">Granted: ${granted}</p>
				</div>
				
				<div class="text-center" style="">
					<h5 style="color: ${cardColor}; line-height: 1;">
						${balance}
					</h5>
					<p style="color: #6c757d;">
						Balance
					</p>
				</div>

				<div class="text-center">
					<div style="color: #17a2b8; font-size: 14px; cursor: pointer; font-weight:bolder" class="view-details-link">
						View Details
					</div>
				</div>

				<div style="position: absolute; bottom: 15px; left: 20px; right: 20px;">
					<div style="font-size: 11px; color: #6c757d;">
						${consumed} of ${granted} Consumed
					</div>
					<div style="background: #e9ecef; height: 4px; border-radius: 2px; margin-top: 5px;">
						<div style="
							background: ${cardColor}; 
							height: 100%; 
							border-radius: 2px; 
							width: ${granted > 0 ? (consumed / granted * 100) : 0}%;
							transition: width 0.3s ease;
						"></div>
					</div>
				</div>
			</div>
		`);

		// Add hover effects
		card.hover(
			function() {
				$(this).css({
					'transform': 'translateY(-2px)',
					'box-shadow': '0 4px 12px rgba(0,0,0,0.15)'
				});
			},
			function() {
				$(this).css({
					'transform': 'translateY(0)',
					'box-shadow': '0 2px 4px rgba(0,0,0,0.08)'
				});
			}
		);

		// Add click handler for details
		card.find('.view-details-link').on('click', (e) => {
			e.stopPropagation();
			this.show_leave_details(leaveData);
		});

		// Add click handler for card
		card.on('click', () => {
			this.show_employee_details(leaveData.employee);
		});

		return card;
	}

	show_leave_details(leaveData) {
		// Create a dialog to show detailed leave applications
		const dialog = new frappe.ui.Dialog({
			title: `${leaveData.leave_type_name} - ${leaveData.employee_name}`,
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'leave_details_html'
				}
			]
		});

		// Prepare HTML content for leave applications
		let detailsHtml = `
			<div style="margin-bottom: 20px;">
				<h5>Leave Summary</h5>
				<div class="row">
					<div class="col-sm-3">
						<strong>Total Allocated:</strong><br>
						<span style="font-size: 18px; color: #28a745;">${leaveData.total_allocated || 0}</span>
					</div>
					<div class="col-sm-3">
						<strong>Leaves Taken:</strong><br>
						<span style="font-size: 18px; color: #dc3545;">${leaveData.total_leaves_taken || 0}</span>
					</div>
					<div class="col-sm-3">
						<strong>Balance:</strong><br>
						<span style="font-size: 18px; color: #17a2b8;">${leaveData.balance || 0}</span>
					</div>
					<div class="col-sm-3">
						<strong>Applications:</strong><br>
						<span style="font-size: 18px; color: #6c757d;">${leaveData.total_applications || 0}</span>
					</div>
				</div>
			</div>
		`;

		if (leaveData.leave_applications && leaveData.leave_applications.length > 0) {
			detailsHtml += `
				<h5>Recent Leave Applications</h5>
				<div class="table-responsive">
					<table class="table table-striped">
						<thead>
							<tr>
								<th>Application</th>
								<th>From Date</th>
								<th>To Date</th>
								<th>Days</th>
								<th>Status</th>
								<th>Type</th>
							</tr>
						</thead>
						<tbody>
			`;

			leaveData.leave_applications.forEach(app => {
				detailsHtml += `
					<tr>
						<td><a href="/app/leave-application/${app.name}" target="_blank">${app.name}</a></td>
						<td>${frappe.datetime.str_to_user(app.from_date)}</td>
						<td>${frappe.datetime.str_to_user(app.to_date)}</td>
						<td>${app.total_leave_days}</td>
						<td><span class="text-success ${app.status === 'Approved' ? 'green' : app.status === 'Rejected' ? 'red' : 'text-danger'}">${app.status}</span></td>
						<td>${app.leave_application_type || 'N/A'}</td>
					</tr>
				`;
			});

			detailsHtml += `
						</tbody>
					</table>
				</div>
			`;
		} else {
			detailsHtml += `<p class="text-muted">No leave applications found for this leave type.</p>`;
		}

		dialog.fields_dict.leave_details_html.$wrapper.html(detailsHtml);
		dialog.show();
	}

	show_employee_details(employee) {
		frappe.set_route('Form', 'Employee', employee);
	}

	show_loading() {
		this.body.find('.data-container').remove();
		this.loading_container = $(`
			<div class="data-container">
				<div class="text-center" style="padding: 100px;">
					<i class="fa fa-spinner fa-spin fa-3x text-muted"></i>
					<p class="text-muted" style="margin-top: 20px; font-size: 16px;">${__('Loading leave balance data...')}</p>
				</div>
			</div>
		`).appendTo(this.body);
	}

	hide_loading() {
		if (this.loading_container) {
			this.loading_container.remove();
		}
	}

	show_empty_state() {
		this.body.find('.data-container').remove();
		$(`
			<div class="data-container">
				<div class="text-center" style="padding: 100px;">
					<i class="fa fa-calendar-times-o fa-4x text-muted"></i>
					<h4 class="text-muted" style="margin-top: 20px;">${__('No Leave Balance Data Found')}</h4>
					<p class="text-muted">${__('Try adjusting your filters or check if leave allocations exist for the selected criteria')}</p>
					<button class="btn btn-primary btn-sm" onclick="frappe.employee_leave_balance.reset_filters()">
						${__('Reset Filters')}
					</button>
				</div>
			</div>
		`).appendTo(this.body);
	}

	export_data() {
		if (!this.data || this.data.length === 0) {
			frappe.show_alert({
				message: __('No data to export'),
				indicator: 'orange'
			});
			return;
		}

		frappe.show_alert({
			message: __('Export functionality will be implemented'),
			indicator: 'blue'
		});
	}

	print_report() {
		if (!this.data || this.data.length === 0) {
			frappe.show_alert({
				message: __('No data to print'),
				indicator: 'orange'
			});
			return;
		}

		window.print();
	}
}