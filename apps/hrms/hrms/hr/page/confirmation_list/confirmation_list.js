frappe.pages['confirmation-list'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Confirmation',
        single_column: true
    });
    
    me = new ConfirmationList(page);
    frappe.confirmation_list = me;
}

frappe.pages['confirmation-list'].on_page_show = function(wrapper) {
    $('.standard-actions.flex').addClass('hide');
    if (frappe.confirmation_list) {
        frappe.confirmation_list.refresh();
    }
}

class ConfirmationList {
    constructor(page) {
        this.page = page;
        this.confirmed_emp_element = "";
        this.upcoming_confirmation_element = "";
        this.employee_id = "";
        this.current_user_role = "";
        this.dashboard_user_data = [];
        
        this.make();
    }
    
    make() {
        this.body = $("<div></div>").appendTo(this.page.main);
        this.show_loader();
        this.run();
    }
    
    show_loader() {
        this.page.main.html(`
            <div class="page-loader-wrapper">
                <div class="loader">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-3">Please wait...</p>
                </div>
            </div>
        `);
    }
    
    run() {
        frappe.call({
            method: "hrms.hr.page.confirmation_list.confirmation_list.getConfirmationData",
            callback: (response) => {
                this.page.main.empty();
                
                if (response.message && response.message.length > 0) {
                    this.dashboard_user_data = response.message;
                    this.current_user_role = response.message[0].user_role;
                    this.render_page(this.dashboard_user_data);
                } else {
                    this.show_empty_state();
                }
            },
            error: () => {
                this.show_error_state();
            }
        });
    }
    
    render_page(data) {
        this.confirmed_emp_element = this.renderConfirmedEmployee(data[0]['confirmed_employee']);
        this.upcoming_confirmation_element = this.renderUpcomingConfirmation(data[0]['probation_employee']);
        
        const html = this.get_page_html();
        this.page.main.html(html);
        
        // Update counts
        $('#probation-count').text(data[0]['probation_employee'].length);
        $('#confirmed-count').text(data[0]['confirmed_employee'].length);
    }
    
    get_page_html() {
        return `
        <div class="page-content">
            <div class="container-fluid">
                <div class="row">
                    <div class="col-12">
                        <div class="page-title-box d-flex align-items-center justify-content-between">
                            <div class="page-title">
                                <h4 class="mb-0">Employee Confirmation Management</h4>
                            </div>
                            <div class="page-actions">
                                <button class="btn btn-sm btn-default" onclick="window.location.href='/app/pipal-employee-dashboard'">
                                    <i class="fa fa-home"></i> Home
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- List View Section -->
                <div class="confirmation-list-section">
                    <div class="row mb-3">
                        <div class="col-12">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-default active" onclick="me.openProbationList()" id="probation-tab">
                                    On Probation <span class="badge badge-warning ml-2" id="probation-count">0</span>
                                </button>
                                <button type="button" class="btn btn-default" onclick="me.openConfirmedList()" id="confirmed-tab">
                                    Confirmed <span class="badge badge-success ml-2" id="confirmed-count">0</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Probation List -->
                    <div id="probation-list-container">
                        <div class="frappe-card">
                            <div class="frappe-card-head">
                                <div class="frappe-card-title">
                                    <strong>Upcoming and Pending Confirmation</strong>
                                </div>
                            </div>
                            <div class="frappe-card-body" id="probation-employees">
                                ${this.upcoming_confirmation_element}
                            </div>
                        </div>
                    </div>

                    <!-- Confirmed List -->
                    <div id="confirmed-list-container" style="display: none;">
                        <div class="frappe-card">
                            <div class="frappe-card-head">
                                <div class="frappe-card-title">
                                    <strong>Confirmed Employees</strong>
                                </div>
                            </div>
                            <div class="frappe-card-body" id="confirmed-employees">
                                ${this.confirmed_emp_element}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Detail View Section -->
                <div class="sigle_employee_confirm_extend" style="display: none;">
                    <div class="row mb-3">
                        <div class="col-12">
                            <button class="btn btn-default btn-sm" onclick="me.backToList()">
                                <i class="fa fa-arrow-left"></i> Back to List
                            </button>
                        </div>
                    </div>

                    <!-- Employee Information Card -->
                    <div class="frappe-card mb-3">
                        <div class="frappe-card-head">
                            <div class="frappe-card-title">
                                <strong id="confirm_emp_title_name">Employee Details</strong>
                            </div>
                        </div>
                        <div class="frappe-card-body">
                            <div class="row">
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Location</label>
                                        <div class="font-weight-bold" id="branch"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Department</label>
                                        <div class="font-weight-bold" id="department"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Reporting Manager</label>
                                        <div class="font-weight-bold" id="reports_to"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Total Experience</label>
                                        <div class="font-weight-bold"><span id="total_work_experience"></span> Years</div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Date Of Joining</label>
                                        <div class="font-weight-bold" id="date_of_joining"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Confirmation Date</label>
                                        <div class="font-weight-bold final_confirmation_date"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Confirmation Initiated On</label>
                                        <div class="font-weight-bold" id="confirmation_initiate_on_date"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Extended Date</label>
                                        <div class="font-weight-bold confirmation_extend_date"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Current Status Card -->
                    <div class="frappe-card mb-3">
                        <div class="frappe-card-head">
                            <div class="frappe-card-title">
                                <strong>Current Confirmation Status</strong>
                            </div>
                        </div>
                        <div class="frappe-card-body">
                            <div class="row">
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Recommended Status</label>
                                        <div class="font-weight-bold" id="confirmation_status"></div>
                                    </div>
                                </div>
                                <div class="col-md-3 col-sm-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Recommended Date</label>
                                        <div class="font-weight-bold recommanded_date"></div>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <div class="form-group">
                                        <label class="text-muted">Reason</label>
                                        <div id="confirmation_extend_reason"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Action Section -->
                    <div class="frappe-card">
                        <div class="frappe-card-head">
                            <div class="frappe-card-title">
                                <strong>Take Action</strong>
                            </div>
                        </div>
                        <div class="frappe-card-body">
                            <div class="row mb-4">
                                <div class="col-md-6 mb-3">
                                    <div class="action-card" onclick="me.selectAction('confirm')">
                                        <input type="radio" name="toggleStatus" value="confirm" id="confirm-radio">
                                        <label for="confirm-radio" class="d-flex align-items-center mb-0">
                                            <div class="flex-fill">
                                                <div class="font-weight-bold">Confirm Employee</div>
                                                <div class="text-muted small">Select this to confirm the employee</div>
                                            </div>
                                            <div class="ml-3">
                                                <i class="fa fa-check-circle fa-2x text-success"></i>
                                            </div>
                                        </label>
                                    </div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <div class="action-card" onclick="me.selectAction('extend')">
                                        <input type="radio" name="toggleStatus" value="extend" id="extend-radio">
                                        <label for="extend-radio" class="d-flex align-items-center mb-0">
                                            <div class="flex-fill">
                                                <div class="font-weight-bold">Extend Probation</div>
                                                <div class="text-muted small">Select this to extend the probation period</div>
                                            </div>
                                            <div class="ml-3">
                                                <i class="fa fa-calendar fa-2x text-warning"></i>
                                            </div>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <!-- Confirm Form -->
                            <div class="show_by_confirm_radio" style="display: none;">
                                <div class="form-section-heading mb-3">Confirmation Details</div>
                                <div class="form-group">
                                    <label class="reqd">Feedback For Employee</label>
                                    <textarea class="form-control" id="c_feedback_for_employee" rows="4" 
                                        placeholder="Enter feedback that will be visible to the employee"></textarea>
                                </div>
                                <div class="form-group text-right mt-4">
                                    <button type="button" class="btn btn-default btn-sm" onclick="me.confirmEmpVal('c_cancel')">
                                        Cancel
                                    </button>
                                    <button type="button" class="btn btn-danger btn-sm ml-2" onclick="me.confirmEmpVal('c_reject')">
                                        Reject
                                    </button>
                                    <button type="button" class="btn btn-primary btn-sm ml-2" onclick="me.confirmEmpVal('c_submit')">
                                        Submit
                                    </button>
                                </div>
                            </div>

                            <!-- Extend Form -->
                            <div class="show_by_extend_radio" style="display: none;">
                                <div class="form-section-heading mb-3">Extension Details</div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="form-group">
                                            <label class="reqd">Extend Date</label>
                                            <input class="form-control" type="date" id="e_extend_date">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-group">
                                            <label class="reqd">Reason</label>
                                            <select id="e_extend_reason" class="form-control">
                                                <option value="" selected disabled>--Select--</option>
                                                <option value="Discipline">Discipline</option>
                                                <option value="Low Efficiency">Low Efficiency</option>
                                                <option value="Low Performance">Low Performance</option>
                                                <option value="Suggest To Terminate">Suggest to Terminate</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="reqd">Feedback For Employee</label>
                                    <textarea class="form-control" id="e_feedback_for_employee" rows="4" 
                                        placeholder="Enter feedback that will be visible to the employee"></textarea>
                                </div>
                                <div class="form-group text-right mt-4">
                                    <button type="button" class="btn btn-default btn-sm" onclick="me.extendEmpVal('e_cancel')">
                                        Cancel
                                    </button>
                                    <button type="button" class="btn btn-danger btn-sm ml-2" onclick="me.extendEmpVal('e_reject')">
                                        Reject
                                    </button>
                                    <button type="button" class="btn btn-primary btn-sm ml-2" onclick="me.extendEmpVal('e_submit')">
                                        Submit
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }
    
    renderConfirmedEmployee(confirmedEmployee) {
        if (!confirmedEmployee || confirmedEmployee.length === 0) {
            return `
                <div class="text-center text-muted py-5">
                    <div class="mb-3">
                        <i class="fa fa-users fa-4x"></i>
                    </div>
                    <p>No confirmed employees found</p>
                </div>
            `;
        }
        
        let html = "";
        confirmedEmployee.forEach(emp => {
            emp.image = emp.image || "/assets/hrms/images/user_employee.png";
            html += `
                <div class="employee-list-item" onclick="me.openConfirmedEmployee('${emp.id}')">
                    <div class="row align-items-center">
                        <div class="col-auto d-none d-md-block">
                            <img src="${emp.image}" class="employee-avatar" alt="${emp.employee_name}">
                        </div>
                        <div class="col-md-4 col-6">
                            <div class="employee-name">${emp.employee_name}</div>
                            <div class="employee-id">${emp.id}</div>
                        </div>
                        <div class="col-md-4 col-6">
                            <div class="employee-info-label">Joining Date</div>
                            <div class="employee-info-value">${frappe.datetime.str_to_user(emp.date_of_joining)}</div>
                        </div>
                        <div class="col-md-3 col-6 mt-2 mt-md-0">
                            <div class="employee-info-label">Confirmation Date</div>
                            <div class="employee-info-value">${frappe.datetime.str_to_user(emp.final_confirmation_date)}</div>
                        </div>
                        <div class="col-auto ml-auto">
                            <i class="fa fa-chevron-right text-muted"></i>
                        </div>
                    </div>
                </div>
            `;
        });
        
        return html;
    }
    
    renderUpcomingConfirmation(upcomingEmployee) {
        if (!upcomingEmployee || upcomingEmployee.length === 0) {
            return `
                <div class="text-center text-muted py-5">
                    <div class="mb-3">
                        <i class="fa fa-users fa-4x"></i>
                    </div>
                    <p>No employees on probation</p>
                </div>
            `;
        }
        
        let html = "";
        upcomingEmployee.forEach(emp => {
            emp.image = emp.image || "/assets/hrms/images/user_employee.png";
            html += `
                <div class="employee-list-item" onclick="me.openUpcomingConfEmp('${emp.id}')">
                    <div class="row align-items-center">
                        <div class="col-auto d-none d-md-block">
                            <img src="${emp.image}" class="employee-avatar" alt="${emp.employee_name}">
                        </div>
                        <div class="col-md-4 col-6">
                            <div class="employee-name">${emp.employee_name}</div>
                            <div class="employee-id">${emp.id}</div>
                        </div>
                        <div class="col-md-4 col-6">
                            <div class="employee-info-label">Joining Date</div>
                            <div class="employee-info-value">${frappe.datetime.str_to_user(emp.date_of_joining)}</div>
                        </div>
                        <div class="col-md-3 col-6 mt-2 mt-md-0">
                            <div class="employee-info-label">Confirmation Date</div>
                            <div class="employee-info-value">${frappe.datetime.str_to_user(emp.final_confirmation_date)}</div>
                        </div>
                        <div class="col-auto ml-auto">
                            <i class="fa fa-chevron-right text-muted"></i>
                        </div>
                    </div>
                </div>
            `;
        });
        
        return html;
    }
    
    openConfirmedList() {
        $('#probation-list-container').hide();
        $('#confirmed-list-container').show();
        $('#probation-tab').removeClass('active');
        $('#confirmed-tab').addClass('active');
    }
    
    openProbationList() {
        $('#confirmed-list-container').hide();
        $('#probation-list-container').show();
        $('#confirmed-tab').removeClass('active');
        $('#probation-tab').addClass('active');
    }
    
    openConfirmedEmployee(emp_id) {
        this.openEmployeeDetail(emp_id, 'confirmed');
    }
    
    openUpcomingConfEmp(emp_id) {
        this.openEmployeeDetail(emp_id, 'probation');
    }
    
    openEmployeeDetail(emp_id, type) {
        const employeeList = type === 'confirmed' 
            ? this.dashboard_user_data[0]['confirmed_employee']
            : this.dashboard_user_data[0]['probation_employee'];
            
        const employee = employeeList.find(emp => emp.id == emp_id);
        
        if (!employee) {
            frappe.show_alert({
                message: __('Employee not found'),
                indicator: 'red'
            });
            return;
        }
        
        this.employee_id = employee.id;
        
        // Hide list and show detail
        $('.confirmation-list-section').hide();
        $('.sigle_employee_confirm_extend').show();
        
        // Populate employee details
        this.populateEmployeeDetails(employee);
        
        // Set default action for confirmed employees
        if (type === 'confirmed') {
            this.selectAction('confirm');
        } else if (employee.confirmation_extend_date) {
            this.selectAction('extend');
        }
    }
    
    populateEmployeeDetails(employee) {
        const today = new Date();
        const joiningDate = new Date(employee.date_of_joining);
        const currentExp = (today - joiningDate) / (1000 * 3600 * 24 * 365);
        const totalExp = (currentExp + (employee.total_work_experience || 0)).toFixed(1);
        
        $('#confirm_emp_title_name').text(employee.employee_name);
        $('#branch').text(employee.branch || '-');
        $('#department').text(employee.department || '-');
        $('#reports_to').text(employee.reports_to || '-');
        $('#date_of_joining').text(frappe.datetime.str_to_user(employee.date_of_joining));
        $('.final_confirmation_date').text(frappe.datetime.str_to_user(employee.final_confirmation_date));
        $('.confirmation_extend_date').text(employee.confirmation_extend_date ? frappe.datetime.str_to_user(employee.confirmation_extend_date) : '-');
        $('#confirmation_initiate_on_date').text(employee.confirmation_initiate_on_date ? frappe.datetime.str_to_user(employee.confirmation_initiate_on_date) : '-');
        $('#total_work_experience').text(totalExp);
        $('#confirmation_status').text(employee.confirmation_status || '-');
        $('#confirmation_extend_reason').text(employee.confirmation_extend_reason || '-');
        
        const recommandedDate = employee.confirmation_extend_date || employee.final_confirmation_date;
        $('.recommanded_date').text(recommandedDate ? frappe.datetime.str_to_user(recommandedDate) : '-');
        
        // Set form values
        $('#c_feedback_for_employee').val(employee.confirmation_status_feedback || '');
        $('#e_feedback_for_employee').val(employee.confirmation_status_feedback || '');
        $('#e_extend_date').val(employee.confirmation_extend_date || '');
        $('#e_extend_reason').val(employee.confirmation_extend_reason || '');
    }
    
    selectAction(action) {
        $(`input[name="toggleStatus"][value="${action}"]`).prop('checked', true);
        
        if (action === 'confirm') {
            $('.show_by_confirm_radio').show();
            $('.show_by_extend_radio').hide();
        } else {
            $('.show_by_confirm_radio').hide();
            $('.show_by_extend_radio').show();
        }
    }
    
    backToList() {
        $('.sigle_employee_confirm_extend').hide();
        $('.confirmation-list-section').show();
        
        // Clear form inputs
        $('#c_feedback_for_employee, #e_feedback_for_employee').val('');
        $('#e_extend_date, #e_extend_reason').val('');
        $('input[name="toggleStatus"]').prop('checked', false);
        $('.show_by_confirm_radio, .show_by_extend_radio').hide();
    }
    
    confirmEmpVal(btnVal) {
        const selectedRadio = $('input[name="toggleStatus"]:checked').val();
        const feedbackForEmployee = $('#c_feedback_for_employee').val();
        
        if (!selectedRadio) {
            frappe.show_alert({
                message: __('Please select an action'),
                indicator: 'red'
            });
            return;
        }
        
        if (btnVal === "c_cancel") {
            this.backToList();
            return;
        }
        
        if (!feedbackForEmployee && btnVal === "c_submit") {
            frappe.show_alert({
                message: __('Please enter feedback for employee'),
                indicator: 'red'
            });
            return;
        }
        
        let status = '';
        let message = '';
        
        if (btnVal === "c_submit" && selectedRadio === "confirm") {
            status = 'Confirmed';
            message = 'Are you sure you want to confirm this employee?';
        } else if (btnVal === "c_reject" && selectedRadio === "confirm") {
            status = 'Rejected';
            message = 'Are you sure you want to reject this employee?';
        } else {
            return;
        }
        
        frappe.confirm(message, () => {
            frappe.call({
                method: "hrms.hr.page.confirmation_list.confirmation_list.updateEmployeeConfirmation",
                args: {
                    employee_id: this.employee_id,
                    confirmation_status: status,
                    confirmation_status_feedback: feedbackForEmployee
                },
                callback: (r) => {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __(r.message.message),
                            indicator: 'green'
                        });
                        
                        // If confirmed, redirect to Leave Policy Assignment
                        if (status === 'Confirmed' && frappe.user.has_role("HR Manager")) {
                            setTimeout(() => {
                                frappe.route_options = {
                                    employee: this.employee_id
                                };
                                frappe.new_doc('Leave Policy Assignment');
                            }, 1000);
                        } else {
                            // For reject, go back to list
                            setTimeout(() => {
                                this.backToList();
                                this.refresh();
                            }, 1000);
                        }
                    } else {
                        frappe.show_alert({
                            message: __(r.message ? r.message.message : 'Failed to update'),
                            indicator: 'red'
                        });
                    }
                }
            });
        });
    }
    
    extendEmpVal(btnVal) {
        const selectedRadio = $('input[name="toggleStatus"]:checked').val();
        const extendDate = $('#e_extend_date').val();
        const extendReason = $('#e_extend_reason').val();
        const feedbackForEmployee = $('#e_feedback_for_employee').val();
        
        if (!selectedRadio) {
            frappe.show_alert({
                message: __('Please select an action'),
                indicator: 'red'
            });
            return;
        }
        
        if (btnVal === "e_cancel") {
            this.backToList();
            return;
        }
        
        if (btnVal === "e_submit" && selectedRadio === "extend") {
            if (!extendDate) {
                frappe.show_alert({
                    message: __('Please select extend date'),
                    indicator: 'red'
                });
                return;
            }
            
            if (!extendReason) {
                frappe.show_alert({
                    message: __('Please select a reason'),
                    indicator: 'red'
                });
                return;
            }
            
            if (!feedbackForEmployee) {
                frappe.show_alert({
                    message: __('Please enter feedback for employee'),
                    indicator: 'red'
                });
                return;
            }
            
            const today = new Date();
            const selectedDate = new Date(extendDate);
            
            if (selectedDate <= today) {
                frappe.show_alert({
                    message: __('Extend date must be in the future'),
                    indicator: 'red'
                });
                return;
            }
            
            frappe.confirm('Are you sure you want to extend probation?', () => {
                frappe.call({
                    method: "hrms.hr.page.confirmation_list.confirmation_list.updateEmployeeConfirmation",
                    args: {
                        employee_id: this.employee_id,
                        confirmation_status: 'On Probation',
                        confirmation_extend_date: extendDate,
                        confirmation_extend_reason: extendReason,
                        confirmation_status_feedback: feedbackForEmployee
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: 'green'
                            });
                            
                            setTimeout(() => {
                                this.backToList();
                                this.refresh();
                            }, 1000);
                        } else {
                            frappe.show_alert({
                                message: __(r.message ? r.message.message : 'Failed to update'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            });
        } else if (btnVal === "e_reject" && selectedRadio === "extend") {
            if (!feedbackForEmployee) {
                frappe.show_alert({
                    message: __('Please enter feedback for employee'),
                    indicator: 'red'
                });
                return;
            }
            
            frappe.confirm('Are you sure you want to reject this employee?', () => {
                frappe.call({
                    method: "hrms.hr.page.confirmation_list.confirmation_list.updateEmployeeConfirmation",
                    args: {
                        employee_id: this.employee_id,
                        confirmation_status: 'Rejected',
                        confirmation_extend_reason: extendReason,
                        confirmation_status_feedback: feedbackForEmployee
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: 'green'
                            });
                            
                            setTimeout(() => {
                                this.backToList();
                                this.refresh();
                            }, 1000);
                        } else {
                            frappe.show_alert({
                                message: __(r.message ? r.message.message : 'Failed to update'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            });
        }
    }
    
    refresh() {
        this.show_loader();
        this.run();
    }
    
    show_empty_state() {
        this.page.main.html(`
            <div class="text-center py-5">
                <div class="mb-3">
                    <i class="fa fa-users fa-5x text-muted"></i>
                </div>
                <h4 class="text-muted">No Employees Found</h4>
                <p class="text-muted">There are no employees for confirmation at this time.</p>
            </div>
        `);
    }
    
    show_error_state() {
        this.page.main.html(`
            <div class="text-center py-5">
                <div class="mb-3">
                    <i class="fa fa-exclamation-triangle fa-5x text-danger"></i>
                </div>
                <h4 class="text-danger">Error Loading Data</h4>
                <p class="text-muted">An error occurred while loading the confirmation list.</p>
                <button class="btn btn-primary btn-sm" onclick="frappe.confirmation_list.refresh()">
                    <i class="fa fa-refresh"></i> Retry
                </button>
            </div>
        `);
    }
}

// Make instance globally accessible as 'me'
window.me = null;