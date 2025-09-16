// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Form 24Q", {
    refresh(frm) {
        $('.grid-buttons').hide();
    },

    form_24q_settings: function(frm) {
        frappe.set_route('/app/form-24q-settings');
    },

    update_challan_details_quart_1: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Apr", "May", "Jun"]]
        });
    },

    update_challan_details_quart_2: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Jul", "Aug", "Sep"]]
        });
    },

    update_challan_details_quart_3: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Oct", "Nov", "Dec"]]
        });
    },

    update_challan_details_quart_4: function(frm) {
        frappe.set_route('List', 'Challan Details', {
            'payroll_period': frm.doc.payroll_period,
            'payroll_month': ["in", ["Jan", "Feb", "Mar"]]
        });
    },

    generate_fvu_quart_1: function(frm) {
        
        // Create modal dialog directly
        const modal = new frappe.ui.Dialog({
            title: __('Generate FVU'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'upload_area',
                    options: `
                        <div class="fvu-upload-section" style="margin: 20px 0; padding: 20px; border: 2px dashed #d1d8dd; border-radius: 8px; background-color: #f8f9fa;">
                            <div class="row">
                                <div class="col-md-12">
                                    <h5 style="color: #36414c; margin-bottom: 15px;">
                                        <i class="fa fa-upload"></i> Upload CSI File for FVU Generation
                                    </h5>
                                    <div class="upload-area" style="text-align: center; padding: 20px;">
                                        <input type="file" id="csi-file-input" accept=".csi" class="form-control" 
                                            style="margin-bottom: 15px; border: 2px solid #d1d8dd; border-radius: 6px; padding: 10px;">
                                        <p style="color: #6c7680; font-size: 14px; margin: 10px 0;">
                                            Select a .CSI file exported from the government tax website
                                        </p>
                                        <div id="file-info" style="margin-top: 15px; display: none;">
                                            <div class="alert alert-info" style="margin: 0;">
                                                <strong>Selected File:</strong> <span id="selected-file-name"></span><br>
                                                <strong>Size:</strong> <span id="selected-file-size"></span>
                                            </div>
                                        </div>
                                    </div>
                                    <div id="upload-status" style="margin-top: 15px;"></div>
                                </div>
                            </div>
                        </div>
                    ` 
                }
            ],
            primary_action_label: __('Ok, Generate FVU'),
            primary_action: function() {
                const selectedFile = modal.selectedFile;
                if (selectedFile) {
                    process_csi_file_and_generate_fvu(modal, selectedFile);
                } else {
                    frappe.msgprint({
                        title: __('No File Selected'),
                        message: __('Please select a CSI file before generating FVU.'),
                        indicator: 'red'
                    });
                }
            },
            secondary_action_label: __('Cancel'),
            secondary_action: function() {
                modal.hide();
            }
        });

        modal.show();
        
        // Wait a moment for the modal to render, then attach events
        setTimeout(() => {
            
            const fileInput = document.getElementById('csi-file-input');
            
            if (!fileInput) {
                console.error('File input not found!');
                const $fileInput = $('#csi-file-input');
                return;
            }
            
            const primaryBtn = modal.get_primary_btn()[0];
            if (primaryBtn) {
                primaryBtn.disabled = true;
            }
            
            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const isCSI = file.name.toLowerCase().endsWith('.csi');
                    if (isCSI) {
                        try {
                            const fileNameElement = document.getElementById('selected-file-name');
                            const fileSizeElement = document.getElementById('selected-file-size');
                            const fileInfoElement = document.getElementById('file-info');
                            const uploadStatusElement = document.getElementById('upload-status');
                            
                            if (fileNameElement) fileNameElement.textContent = file.name;
                            if (fileSizeElement) fileSizeElement.textContent = format_file_size(file.size);
                            if (fileInfoElement) fileInfoElement.style.display = 'block';
                            if (uploadStatusElement) {
                                uploadStatusElement.innerHTML = '<div class="alert alert-success"><i class="fa fa-check-circle"></i> CSI file selected successfully.</div>';
                            }
                            
                            if (primaryBtn) primaryBtn.disabled = false;
                            modal.selectedFile = file;
                            
                        } catch (error) {
                            console.error('Error processing file:', error);
                            const fileInfoElement = document.getElementById('file-info');
                            const uploadStatusElement = document.getElementById('upload-status');
                            
                            if (fileInfoElement) fileInfoElement.style.display = 'none';
                            if (uploadStatusElement) {
                                uploadStatusElement.innerHTML = '<div class="alert alert-danger"><i class="fa fa-exclamation-triangle"></i> Error processing file: ' + error.message + '</div>';
                            }
                            if (primaryBtn) primaryBtn.disabled = true;
                            modal.selectedFile = null;
                        }
                    } else {
                        console.log('Invalid file type');
                        const fileInfoElement = document.getElementById('file-info');
                        const uploadStatusElement = document.getElementById('upload-status');
                        
                        if (fileInfoElement) fileInfoElement.style.display = 'none';
                        if (uploadStatusElement) {
                            uploadStatusElement.innerHTML = '<div class="alert alert-danger"><i class="fa fa-exclamation-triangle"></i> Please select a valid .CSI file</div>';
                        }
                        if (primaryBtn) primaryBtn.disabled = true;
                        modal.selectedFile = null;
                    }
                } else {
                    console.log('No file selected');
                    const fileInfoElement = document.getElementById('file-info');
                    const uploadStatusElement = document.getElementById('upload-status');
                    
                    if (fileInfoElement) fileInfoElement.style.display = 'none';
                    if (uploadStatusElement) uploadStatusElement.innerHTML = '';
                    if (primaryBtn) primaryBtn.disabled = true;
                    modal.selectedFile = null;
                }
                
            });
            
            
        }, 300);
        
        return modal;
    }
});

function format_file_size(bytes) {
    
    if (bytes === 0) return '0 Bytes';
    if (typeof bytes !== 'number' || isNaN(bytes)) return 'Invalid size';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    const result = parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    
    return result;
}

function process_csi_file_and_generate_fvu(modal, selectedFile) {
    // Show processing status
    const uploadStatusElement = document.getElementById('upload-status');
    if (uploadStatusElement) {
        uploadStatusElement.innerHTML = '<div class="alert alert-info"><i class="fa fa-spinner fa-spin"></i> Processing CSI file and generating FVU files...</div>';
    }
    
    // Disable the button during processing
    const primaryBtn = modal.get_primary_btn()[0];
    if (primaryBtn) {
        primaryBtn.disabled = true;
        primaryBtn.textContent = 'Processing...';
    }
    
    // Read file content
    const reader = new FileReader();
    reader.onload = function(e) {
        const fileContent = e.target.result;
        
        // Call the backend method
        frappe.call({
            method: 'hrms.payroll.doctype.form_24q.form_24q.generate_fvu_files_from_csi',
            args: {
                csi_content: fileContent,
                quarter: "Q1"
            },
            callback: function(response) {
                const uploadStatusElement = document.getElementById('upload-status');
                if (response.message && response.message.success) {
                    // Show success message
                    if (uploadStatusElement) {
                        uploadStatusElement.innerHTML = `
                            <div class="alert alert-success">
                                <h6><i class="fa fa-check-circle"></i> FVU Files Generated Successfully!</h6>
                                <p>All required files have been generated.</p>
                            </div>
                        `;
                    }
                    
                    // Show download links if available
                    if (response.message.files) {
                        show_download_links(response.message.files);
                    }
                    
                    frappe.show_alert({
                        message: __('FVU files generated successfully!'),
                        indicator: 'green'
                    }, 5);
                    
                    // Reset button
                    if (primaryBtn) {
                        primaryBtn.textContent = 'Ok, Generate FVU';
                        primaryBtn.disabled = false;
                    }
                } else {
                    const error = response.message ? response.message.error : 'Unknown error occurred';
                    if (uploadStatusElement) {
                        uploadStatusElement.innerHTML = `
                            <div class="alert alert-danger">
                                <h6><i class="fa fa-exclamation-triangle"></i> Error Generating FVU</h6>
                                <p>${error}</p>
                            </div>
                        `;
                    }
                    if (primaryBtn) {
                        primaryBtn.textContent = 'Ok, Generate FVU';
                        primaryBtn.disabled = false;
                    }
                }
            },
            error: function(error) {
                console.error('FVU Generation Error:', error);
                const uploadStatusElement = document.getElementById('upload-status');
                if (uploadStatusElement) {
                    uploadStatusElement.innerHTML = `
                        <div class="alert alert-danger">
                            <h6><i class="fa fa-exclamation-triangle"></i> Error Generating FVU</h6>
                            <p>Failed to communicate with server. Please try again.</p>
                        </div>
                    `;
                }
                if (primaryBtn) {
                    primaryBtn.textContent = 'Ok, Generate FVU';
                    primaryBtn.disabled = false;
                }
            }
        });
    };
    
    reader.onerror = function() {
        const uploadStatusElement = document.getElementById('upload-status');
        if (uploadStatusElement) {
            uploadStatusElement.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fa fa-exclamation-triangle"></i> Error Reading File</h6>
                    <p>Failed to read the selected file. Please try again.</p>
                </div>
            `;
        }
        if (primaryBtn) {
            primaryBtn.textContent = 'Ok, Generate FVU';
            primaryBtn.disabled = false;
        }
    };
    
    // Read file as text
    reader.readAsText(selectedFile);
}

function show_download_links(files) {
    let downloadHtml = '<div class="row" style="margin-top: 20px;">';
    downloadHtml += '<div class="col-md-12"><h6>Generated Files:</h6></div>';
    
    Object.keys(files).forEach(fileKey => {
        const file = files[fileKey];
        if (file.file_url) {
            downloadHtml += `
                <div class="col-md-6 col-sm-12" style="margin-bottom: 10px;">
                    <a href="${file.file_url}" target="_blank" class="btn btn-default btn-sm btn-block">
                        <i class="fa fa-download"></i> Download ${fileKey}
                    </a>
                </div>
            `;
        }
    });
    
    downloadHtml += '</div>';
    const uploadStatusElement = document.getElementById('upload-status');
    if (uploadStatusElement) {
        uploadStatusElement.insertAdjacentHTML('afterend', downloadHtml);
    }
}