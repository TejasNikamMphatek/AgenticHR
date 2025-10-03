frappe.listview_settings["Auto Email"] = {
    onload(listview) {
        const clean = () => {
            // Find the Frequency standard filter wrapper
            const $field = listview.$page
                .find('.standard-filter-section [data-fieldname="frequency"]');

            if (!$field.length) return;

            // 1) Prefer: revert to native <select>
            const $select = $field.find('select');
            if ($select.length && $select.data('selectpicker')) {
                try { $select.selectpicker('destroy'); } catch (e) {}
            }

            // 2) Also remove unwanted classes from any leftover wrapper
            $field.find('div.dropdown.bootstrap-select')
                .removeClass('dropdown bootstrap-select input-with-feedback form-control input-xs ellipsis');
        
            // For placeholder
            $('.frappe-control[data-fieldtype="Select"].form-group .placeholder.xs').css({
            'top': '6px'
            });

            // For select icon
            $('.frappe-control[data-fieldtype="Select"].form-group .select-icon.xs').css({
            'top': '6px',
            'right': '10px'
            });

            };

        // Run now and after render
        frappe.after_ajax(clean);
        setTimeout(clean, 300);

        // Re-run on DOM changes (filters often re-render)
        const obs = new MutationObserver(() => clean());
        obs.observe(listview.$page[0], { childList: true, subtree: true });
        listview.__freqObs = obs;
    },

};
