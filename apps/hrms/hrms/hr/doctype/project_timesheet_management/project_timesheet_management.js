frappe.ui.form.on('Project Timesheet Management', {
    refresh: function(frm) {
        // Add Export button to the top toolbar
        if (!frm.custom_export_button) {
            frm.add_custom_button(__('Export Timesheet'), function() {
                export_timesheet(frm);
            });
            frm.custom_export_button = true;
        }
    }
});

function export_timesheet(frm) {
    let rows = frm.doc.timesheet_table || [];
    if (!rows.length) {
        frappe.msgprint(__('No Timesheet data to export'));
        return;
    }

    // Prepare CSV data with headers
    let data = [['Task Name','Task Assigned By','Task Start Time','Task End Time','Spend Hours','Task Status','Description']];

    rows.forEach(r => {
        data.push([
            r.task_name || '',
            r.task_assigned_by || '',
            r.task_start_time || '',
            r.task_end_time || '',
            r.spend_hours || '',
            r.task_status || '',
            r.description || ''
        ]);
    });

    // Generate CSV and download
    let csvContent = data.map(e => e.join(",")).join("\n");
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Timesheet_${frm.doc.name}.csv`;
    link.click();
}
