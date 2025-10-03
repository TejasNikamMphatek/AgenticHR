frappe.listview_settings["Report"] = {
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
            $field.find('div.dropdown.bootstrap-select').removeClass('dropdown bootstrap-select input-with-feedback form-control input-xs ellipsis');
        };

        // Run now and after render
        frappe.after_ajax(clean);
        setTimeout(clean, 300);

        // Re-run on DOM changes (filters often re-render)
        const obs = new MutationObserver(() => clean());
        obs.observe(listview.$page[0], { childList: true, subtree: true });
        listview.__freqObs = obs;
    },

    refresh(listview) {
        // Ensure it runs on each refresh too
        setTimeout(() => {
            if (listview.__freqObs) { /* observer still active */ }
            const $ = window.jQuery;
            if ($) {
                const $field = listview.$page
                    .find('.standard-filter-section [data-fieldname="frequency"]');
                if ($field.length) {
                    const $select = $field.find('select');
                    if ($select.length && $select.data('selectpicker')) {
                        try { $select.selectpicker('destroy'); } catch (e) {}
                    }
                    $field.find('div.dropdown.bootstrap-select')
                        .removeClass('dropdown bootstrap-select input-with-feedback form-control input-xs ellipsis');
                }
            }
        }, 200);
    }
};
frappe.listview_settings["Report"] = {
    onload(listview) {
        const clean = () => {
            // Find the Is Standard standard filter wrapper
            const $field = listview.$page
                .find('.standard-filter-section [data-fieldname="is_standard"]');

            if (!$field.length) return;

            // 1) Prefer: revert to native <select>
            const $select = $field.find('select');
            if ($select.length && $select.data('selectpicker')) {
                try { 
                    $select.selectpicker('destroy');  // remove bootstrap-select enhancement
                } catch (e) {
                    console.warn("Selectpicker destroy failed", e);
                }
            }

            // 2) Also remove unwanted classes from leftover wrapper
            $field.find('div.dropdown.bootstrap-select')
                .removeClass('dropdown bootstrap-select input-with-feedback form-control input-xs ellipsis');
        };

        // Run now and after render
        frappe.after_ajax(clean);
        setTimeout(clean, 300);

        // Re-run on DOM changes (filters often re-render)
        const obs = new MutationObserver(() => clean());
        obs.observe(listview.$page[0], { childList: true, subtree: true });
        listview.__isStandardObs = obs;
    },

};
