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

        eventClick: function (event, jsEvent, view) {
            // Fetch user roles
            frappe.call({
                method: "hrms.hr.doctype.attendance.attendance.get_user_roles",
                callback: function (r) {
                    let roles = r.message;
                    //console.log("User Roles:", roles);

                    let isManager = roles.some(role =>
                        ['HR Manager', 'Projects Manager', 'System Manager'].includes(role)
                    );
                    let isEmployee = roles.includes('Employee');

                   let employee_id = event.employee || event.employee_name || null;
let employeeFilters = null;
//console.log("Employee ID passed to backend:", employee_id);

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
                            // console.log("Attendance Summary:", data);

                            if (!data || (!data.swipes?.length && !data.sessions?.length && !data.employee)) {
                                frappe.msgprint(__("No attendance data found for this date."));
                                return;
                            }

                            let dialogFields = [
                                {
                                    fieldtype: "HTML",
                                    label: __("Summary"),
                                    options: `
                                        <div>
                                            <p><strong>Date:</strong> ${data.date || "N/A"}</p>
                                            ${isManager ? `<p><strong>Employee:</strong> ${data.employee_name || "N/A"}</p>` : ""}
                                            <p><strong>Total Hours:</strong> ${data.total_hours || 0}</p>
                                            <p><strong>Swipes:</strong> ${data.swipes?.length ? data.swipes.join(", ") : "None"}</p>
                                            <p><strong>Sessions:</strong></p>
                                            <ul>
                                                ${
                                                    data.sessions?.length
                                                        ? data.sessions
                                                              .map(
                                                                  (session) =>
                                                                      `<li>IN: ${session.in}, OUT: ${session.out}, Hours: ${session.hours}</li>`
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
                                title: __("Attendance Details for {0}", [
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

    refresh: function (calendar_view) {
        // console.log("🔁 Calendar refreshed");

        if ($(".attendance-request-btn").length === 0) {
            setTimeout(() => {
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
                    // console.log("✅ Attendance Request button added");
                } else {
                    // console.log("⚠️ Button area not found");
                }
            }, 300);
        }
    },
};
