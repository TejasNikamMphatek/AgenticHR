// Copyright (c) 2016, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Analytics"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "parameter",
            label: __("Parameter"),
            fieldtype: "Select",
            options: ["Branch", "Grade", "Department", "Designation", "Employment Type"],
            reqd: 1,
        },
    ],
    onload: function(report) {
        // Inject CSS for horizontal scroll
        const style = document.createElement("style");
        style.innerHTML = `
            .frappe-chart-wrapper {
                overflow-x: auto;
                max-width: 100%;
            }
            .frappe-chart-wrapper canvas {
                min-width: 800px; /* minimum width to allow scroll */
            }
        `;
        document.head.appendChild(style);
    },
    after_datatable_render: function(report, wrapper) {
        // Wrap chart container dynamically
        const chartContainer = wrapper.querySelector(".chart-wrapper");
        if(chartContainer && !chartContainer.parentElement.classList.contains("frappe-chart-wrapper")) {
            const wrapperDiv = document.createElement("div");
            wrapperDiv.className = "frappe-chart-wrapper";
            chartContainer.parentNode.insertBefore(wrapperDiv, chartContainer);
            wrapperDiv.appendChild(chartContainer);
        }
    }
};
