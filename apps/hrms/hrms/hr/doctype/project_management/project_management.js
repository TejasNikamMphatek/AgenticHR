frappe.ui.form.on('Project Management', {
    async onload(frm) {
        const user = frappe.session.user;

        // Find Employee record for current user
        const emp = await frappe.db.get_value('Employee', { user_id: user }, 'name');
        const emp_id = emp?.message?.name;

        frm.fields_dict.project_team.grid.get_field('employee').get_query = function(doc, cdt, cdn) {
            let filters = {};

            // Get all roles of the current user
            const roles = frappe.user_roles || [];

            if (roles.includes('Projects Manager') && emp_id) {
                // Filter employees who report to this manager
                filters = { reports_to: emp_id };
            } else if (
                roles.includes('HR User') ||
                roles.includes('HR Manager') ||
                roles.includes('System Manager') ||
                roles.includes('Administrator')
            ) {
                // HR/Admins can see all
                filters = {};
            } else if (emp_id) {
                // Others see only themselves
                filters = { name: emp_id };
            }

            return { filters };
        };
    }
});
