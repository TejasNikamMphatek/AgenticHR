// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.views.calendar["Attendance"] = {
    field_map: {
        start: "start",
        end: "end",
        id: "name",
        title: "title",
        allDay: "allDay",
        color: "color",
    },

    get_css_class: function (data) {
        if (data.doctype === "Holiday") return "default";
        else if (data.doctype === "Attendance") {
            if (data.status === "Absent" || data.status === "On Leave") {
                return "danger";
            }
            if (data.status === "Half Day") return "warning";
            return "success";
        }
    },

    options: {
        header: {
            left: "prev,next today",
            center: "title",
            right: "month",
        },
        selectable: false,

        viewRender: function (view, element) {
            // Initialize legend
            let legendHtml = `
                <div id="calendar-legend" style="margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px;">
                    <h6>Legend</h6>
                    <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                        <div>
                            <span style="display: inline-block; width: 20px; height: 20px; background: #6c757d; margin-right: 5px;"></span>
                            Holiday
                        </div>
                        <div>
                            <span style="display: inline-block; width: 20px; height: 20px; background:red; margin-right: 5px;"></span>
                            Absent / On Leave
                        </div>
                        <div>
                            <span style="display: inline-block; width: 20px; height: 20px; background: #BD3E0C; margin-right: 5px;"></span>
                            Half Day
                        </div>
                        <div>
                            <span style="display: inline-block; width: 20px; height: 20px; background: #28a745; margin-right: 5px;"></span>
                            Present
                        </div>
                    </div>
                </div>
            `;

            // Append legend to the bottom of the calendar container
            if (!$("#calendar-legend").length) {
                $(".fc-view-container").after(legendHtml);
            }

            // Add Attendance Request button
            if ($(".attendance-request-btn").length === 0) {
                let button_area = $(".calendar-actions");
                if (!button_area.length) {
                    button_area = $(".page-actions");
                }

                if (button_area.length) {
                    $('<button class="btn btn-primary attendance-request-btn">Attendance Request</button>')
                        .appendTo(button_area)
                        .on("click", function () {
                            frappe.new_doc("Attendance Request");
                        });
                }
            }
        },

        eventClick: function (event, jsEvent, view) {
            // Existing eventClick logic remains unchanged
            frappe.call({
                method: "hrms.hr.doctype.attendance.attendance.get_user_roles",
                callback: function (r) {
                    let roles = r.message;
                    let isManager = roles.some(role =>
                        ['HR Manager', 'Projects Manager', 'System Manager'].includes(role)
                    );
                    let isEmployee = roles.includes('Employee');

                    let employee_id = event.employee || event.employee_name || null;
                    let employeeFilters = null;

                    if (isManager && employee_id) {
                        employeeFilters = JSON.stringify([
                            ["Attendance", "employee", "=", employee_id]
                        ]);
                    }

                    frappe.call({
                        method: "hrms.hr.doctype.attendance.attendance.get_attendance_summary_for_date",
                        args: {
                            date: event.start.format("YYYY-MM-DD"),
                            is_manager: isManager,
                            filters: employeeFilters
                        },
                        freeze: true,
                        freeze_message: __("Fetching attendance details..."),
                        callback: function (r) {
                            let data = r.message;

                            if (!data || (!data.swipes?.length && !data.sessions?.length && !data.employee)) {
                                frappe.msgprint(__("No attendance data found for this date."));
                                return;
                            }

                            let shift_text = "";
                            if (typeof data.shift?.type === "string") {
                                shift_text = `Shift: ${data.shift.type}`;
                                if (typeof data.shift.timing === "string" && data.shift.timing.trim()) {
                                    shift_text += ` (${data.shift.timing})`;
                                }
                            }

                            let dialogFields = [
                                {
                                    fieldtype: "HTML",
                                    label: __("Summary"),
                                    options: `
                                        <div>
                                            ${isManager ? `<p><strong>Employee:</strong> ${data.employee_name || "N/A"}</p>` : ""}
                                            ${shift_text ? `<p><strong>${shift_text}</strong></p>` : ""}
                                            <p><strong>Total Hours:</strong> ${data.total_hours || 0} hrs</p>
                                            <p><strong>Sessions:</strong></p>
                                            <ul>
                                                ${
                                                    data.sessions?.length
                                                        ? data.sessions
                                                              .map(
                                                                  (session) =>
                                                                      `<li class='text-success'>IN: <span class='text-dark'>${session.in}</span></li>
                                                                       <li class='text-danger'>OUT: <span class='text-dark'>${session.out}</span></li>`
                                                              )
                                                              .join("")
                                                        : "<li>No sessions recorded</li>"
                                                }
                                            </ul>
                                        </div>
                                    `,
                                },
                            ];

                            let dialog = new frappe.ui.Dialog({
                                title: __("<b>Attendance Details for {0} </b>", [
                                    event.start.format("MMMM D, YYYY"),
                                ]),
                                fields: dialogFields,
                                primary_action_label: __("Close"),
                                primary_action: function () {
                                    dialog.hide();
                                },
                            });

                            dialog.show();
                        },
                        error: function () {
                            frappe.msgprint(__("Error fetching attendance details."));
                        },
                    });
                }
            });
        },
    },

    get_events_method: "hrms.hr.doctype.attendance.attendance.get_events",

    // Remove the refresh function as it's no longer needed
};