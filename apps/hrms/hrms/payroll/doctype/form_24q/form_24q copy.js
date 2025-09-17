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
        
        // Create modal dialog with improved styling
        const modal = new frappe.ui.Dialog({
            title: __('Generate FVU Files - Quarter 1 (Apr-Jun)'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'upload_area',
                    options: `
                        <div class="fvu-upload-section" style="margin: 20px 0; padding: 25px; border: 2px dashed #d1d8dd; border-radius: 10px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);">
                            <div class="row">
                                <div class="col-md-12">
                                    <div style="text-align: center; margin-bottom: 20px;">
                                        <i class="fa fa-cloud-upload" style="font-size: 48px; color: #6c757d; margin-bottom: 15px;"></i>
                                        <h4 style="color: #495057; margin-bottom: 10px;">Upload CSI File for FVU Generation</h4>
                                        <p style="color: #6c7680; font-size: 14px; margin: 0;">
                                            Select the .CSI file exported from the government tax website to generate all required FVU files
                                        </p>
                                    </div>
                                    
                                    <div class="upload-area" style="text-align: center; padding: 20px;">
                                        <input type="file" id="csi-file-input" accept=".csi" class="form-control" 
                                            style="margin-bottom: 15px; border: 2px solid #d1d8dd; border-radius: 8px; padding: 12px; font-size: 14px;">
                                        
                                        <div class="file-requirements" style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 15px 0; text-align: left;">
                                            <h6 style="margin: 0 0 10px 0; color: #856404;">
                                                <i class="fa fa-info-circle"></i> File Requirements:
                                            </h6>
                                            <ul style="margin: 0; padding-left: 20px; color: #856404; font-size: 13px;">
                                                <li>File must have .CSI extension</li>
                                                <li>File should be exported from government tax website</li>
                                                <li>Maximum file size: 10MB</li>
                                                <li>File should contain valid TAN and challan information</li>
                                            </ul>
                                        </div>
                                        
                                        <div id="file-info" style="margin-top: 15px; display: none;">
                                            <div class="alert alert-info" style="margin: 0; text-align: left;">
                                                <div style="display: flex; align-items: center;">
                                                    <i class="fa fa-file-o" style="font-size: 24px; margin-right: 15px; color: #17a2b8;"></i>
                                                    <div>
                                                        <strong>Selected File:</strong> <span id="selected-file-name"></span><br>
                                                        <strong>File Size:</strong> <span id="selected-file-size"></span><br>
                                                        <strong>Status:</strong> <span class="text-success">Ready for processing</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="expected-files" style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 6px; padding: 15px; margin: 15px 0; text-align: left;">
                                            <h6 style="margin: 0 0 10px 0; color: #0c5460;">
                                                <i class="fa fa-list"></i> Files that will be generated:
                                            </h6>
                                            <div class="row" style="font-size: 12px;">
                                                <div class="col-md-6">
                                                    <ul style="margin: 0; padding-left: 20px; color: #0c5460;">
                                                        <li>Form 27A (PDF format)</li>
                                                        <li>Form 24Q FVU file</li>
                                                        <li>Form 24Q Text file</li>
                                                        <li>Challan CSI file</li>
                                                    </ul>
                                                </div>
                                                <div class="col-md-6">
                                                    <ul style="margin: 0; padding-left: 20px; color: #0c5460;">
                                                        <li>FVU Log file</li>
                                                        <li>Warning file (HTML)</li>
                                                        <li>Statistics report (HTML)</li>
                                                    </ul>
                                                </div>
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
            primary_action_label: __('<i class="fa fa-cogs"></i> Generate FVU Files'),
            primary_action: function() {
                const selectedFile = modal.selectedFile;
                if (selectedFile) {
                    process_csi_file_and_generate_fvu(modal, selectedFile, frm.doc.name, "1st_quarter_april_june");
                } else {
                    frappe.msgprint({
                        title: __('No File Selected'),
                        message: __('Please select a valid CSI file before generating FVU files.'),
                        indicator: 'red'
                    });
                }
            },
            secondary_action_label: __('Cancel'),
            secondary_action: function() {
                modal.hide();
            },
            size: 'large'  // Make modal larger to accommodate content
        });

        modal.show();
        
        // Wait for modal to render, then attach events
        setTimeout(() => {
            
            const fileInput = document.getElementById('csi-file-input');
            
            if (!fileInput) {
                console.error('File input not found!');
                return;
            }
            
            const primaryBtn = modal.get_primary_btn()[0];
            if (primaryBtn) {
                primaryBtn.disabled = true;
                primaryBtn.style.background = '#6c757d';
                primaryBtn.innerHTML = '<i class="fa fa-upload"></i> Select CSI File First';
            }
            
            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const isCSI = file.name.toLowerCase().endsWith('.csi');
                    const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB limit
                    
                    if (isCSI && isValidSize) {
                        try {
                            const fileNameElement = document.getElementById('selected-file-name');
                            const fileSizeElement = document.getElementById('selected-file-size');
                            const fileInfoElement = document.getElementById('file-info');
                            const uploadStatusElement = document.getElementById('upload-status');
                            
                            if (fileNameElement) fileNameElement.textContent = file.name;
                            if (fileSizeElement) fileSizeElement.textContent = format_file_size(file.size);
                            if (fileInfoElement) fileInfoElement.style.display = 'block';
                            if (uploadStatusElement) {
                                uploadStatusElement.innerHTML = `
                                    <div class="alert alert-success" style="margin-top: 15px;">
                                        <i class="fa fa-check-circle"></i> CSI file validated successfully. Ready to generate FVU files.
                                    </div>
                                `;
                            }
                            
                            if (primaryBtn) {
                                primaryBtn.disabled = false;
                                primaryBtn.style.background = '#007bff';
                                primaryBtn.innerHTML = '<i class="fa fa-cogs"></i> Generate FVU Files';
                            }
                            modal.selectedFile = file;
                            
                        } catch (error) {
                            console.error('Error processing file:', error);
                            handleFileError('Error processing file: ' + error.message);
                        }
                    } else {
                        let errorMsg = '';
                        if (!isCSI) errorMsg = 'Please select a valid .CSI file';
                        else if (!isValidSize) errorMsg = 'File size must be less than 10MB';
                        
                        handleFileError(errorMsg);
                    }
                } else {
                    resetFileInput();
                }
                
                function handleFileError(message) {
                    const fileInfoElement = document.getElementById('file-info');
                    const uploadStatusElement = document.getElementById('upload-status');
                    
                    if (fileInfoElement) fileInfoElement.style.display = 'none';
                    if (uploadStatusElement) {
                        uploadStatusElement.innerHTML = `
                            <div class="alert alert-danger">
                                <i class="fa fa-exclamation-triangle"></i> ${message}
                            </div>
                        `;
                    }
                    if (primaryBtn) {
                        primaryBtn.disabled = true;
                        primaryBtn.style.background = '#6c757d';
                        primaryBtn.innerHTML = '<i class="fa fa-upload"></i> Select Valid CSI File';
                    }
                    modal.selectedFile = null;
                }
                
                function resetFileInput() {
                    const fileInfoElement = document.getElementById('file-info');
                    const uploadStatusElement = document.getElementById('upload-status');
                    
                    if (fileInfoElement) fileInfoElement.style.display = 'none';
                    if (uploadStatusElement) uploadStatusElement.innerHTML = '';
                    if (primaryBtn) {
                        primaryBtn.disabled = true;
                        primaryBtn.style.background = '#6c757d';
                        primaryBtn.innerHTML = '<i class="fa fa-upload"></i> Select CSI File First';
                    }
                    modal.selectedFile = null;
                }
            });
            
        }, 300);
        
        return modal;
    }
});


// Enhanced format_file_size function with better precision
function format_file_size(bytes) {

    if (bytes === 0) return '0 Bytes';
    if (typeof bytes !== 'number' || isNaN(bytes)) return 'Unknown size';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    const size = bytes / Math.pow(k, i);
    const formattedSize = i === 0 ? size.toString() : size.toFixed(2);
    
    return `${formattedSize} ${sizes[i]}`;
}

// Updated process_csi_file_and_generate_fvu function with better error handling
function process_csi_file_and_generate_fvu(modal, selectedFile, docname, quarter) {
    // Show processing status
    const uploadStatusElement = document.getElementById('upload-status');
    if (uploadStatusElement) {
        uploadStatusElement.innerHTML = `
            <div class="alert alert-info">
                <div style="display: flex; align-items: center;">
                    <i class="fa fa-spinner fa-spin" style="margin-right: 10px;"></i>
                    <div>
                        <strong>Processing CSI file and generating FVU files...</strong>
                        <div style="font-size: 12px; margin-top: 5px;">
                            This may take a few moments. Please wait.
                        </div>
                    </div>
                </div>
                <div class="progress" style="margin-top: 10px;">
                    <div class="progress-bar progress-bar-striped active" style="width: 100%"></div>
                </div>
            </div>
        `;
    }
    
    // Disable the button during processing
    const primaryBtn = modal.get_primary_btn()[0];
    if (primaryBtn) {
        primaryBtn.disabled = true;
        primaryBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Processing...';
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
                quarter: quarter,
                docname : docname
            },
            callback: function(response) {
                const uploadStatusElement = document.getElementById('upload-status');
                if (response.message && response.message.success) {
                    // Show success message
                    if (uploadStatusElement) {
                        uploadStatusElement.innerHTML = `
                            <div class="alert alert-success">
                                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                    <i class="fa fa-check-circle" style="margin-right: 10px; font-size: 18px;"></i>
                                    <div>
                                        <h6 style="margin: 0; color: #155724;">FVU Files Generated Successfully!</h6>
                                        <p style="margin: 5px 0 0 0; font-size: 13px;">All required files have been generated and are ready for download.</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Show download links if available
                    if (response.message.files) {
                        show_download_links(response.message.files);
                    }
                    
                    frappe.show_alert({
                        message: __('FVU files generated successfully! Check the download links below.'),
                        indicator: 'green'
                    }, 5);
                    
                    // Reset button
                    if (primaryBtn) {
                        primaryBtn.innerHTML = '<i class="fa fa-check"></i> Files Generated Successfully';
                        primaryBtn.disabled = false;
                        primaryBtn.classList.remove('btn-primary');
                        primaryBtn.classList.add('btn-success');
                    }
                } else {
                    const error = response.message ? response.message.error : 'Unknown error occurred';
                    if (uploadStatusElement) {
                        uploadStatusElement.innerHTML = `
                            <div class="alert alert-danger">
                                <div style="display: flex; align-items: center;">
                                    <i class="fa fa-exclamation-triangle" style="margin-right: 10px; font-size: 18px;"></i>
                                    <div>
                                        <h6 style="margin: 0; color: #721c24;">Error Generating FVU Files</h6>
                                        <p style="margin: 5px 0 0 0; font-size: 13px;">${error}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    if (primaryBtn) {
                        primaryBtn.innerHTML = '<i class="fa fa-refresh"></i> Try Again';
                        primaryBtn.disabled = false;
                        primaryBtn.classList.remove('btn-success');
                        primaryBtn.classList.add('btn-primary');
                        primaryBtn.style.background = '#007bff';
                    }
                }
            },
            error: function(error) {
                console.error('FVU Generation Error:', error);
                const uploadStatusElement = document.getElementById('upload-status');
                if (uploadStatusElement) {
                    uploadStatusElement.innerHTML = `
                        <div class="alert alert-danger">
                            <div style="display: flex; align-items: center;">
                                <i class="fa fa-exclamation-triangle" style="margin-right: 10px; font-size: 18px;"></i>
                                <div>
                                    <h6 style="margin: 0; color: #721c24;">Server Communication Error</h6>
                                    <p style="margin: 5px 0 0 0; font-size: 13px;">Failed to communicate with server. Please check your connection and try again.</p>
                                    <div style="margin-top: 10px; padding: 8px; background-color: #f8d7da; border-radius: 4px; font-size: 12px;">
                                        <strong>Error Details:</strong> ${error.message || 'Unknown server error'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
                if (primaryBtn) {
                    primaryBtn.innerHTML = '<i class="fa fa-refresh"></i> Try Again';
                    primaryBtn.disabled = false;
                    primaryBtn.classList.remove('btn-success');
                    primaryBtn.classList.add('btn-primary');
                    primaryBtn.style.background = '#007bff';
                }
                
                // Show error alert
                frappe.show_alert({
                    message: __('Failed to generate FVU files. Please try again.'),
                    indicator: 'red'
                }, 5);
            }
        });
    };
    
    reader.onerror = function() {
        const uploadStatusElement = document.getElementById('upload-status');
        if (uploadStatusElement) {
            uploadStatusElement.innerHTML = `
                <div class="alert alert-danger">
                    <div style="display: flex; align-items: center;">
                        <i class="fa fa-exclamation-triangle" style="margin-right: 10px; font-size: 18px;"></i>
                        <div>
                            <h6 style="margin: 0; color: #721c24;">Error Reading File</h6>
                            <p style="margin: 5px 0 0 0; font-size: 13px;">Failed to read the selected CSI file. Please ensure the file is not corrupted and try again.</p>
                        </div>
                    </div>
                </div>
            `;
        }
        if (primaryBtn) {
            primaryBtn.innerHTML = '<i class="fa fa-refresh"></i> Try Again';
            primaryBtn.disabled = false;
            primaryBtn.classList.remove('btn-success');
            primaryBtn.classList.add('btn-primary');
            primaryBtn.style.background = '#007bff';
        }
    };
    
    // Read file as text
    reader.readAsText(selectedFile);
}

function show_download_links(files) {
    let downloadHtml = '<div class="row" style="margin-top: 20px;">';
    downloadHtml += '<div class="col-md-12"><h6><i class="fa fa-check-circle text-success"></i> Files Generated Successfully:</h6></div>';
    
    // Define the order and display names for your specific files
    const fileOrder = [
        { key: 'form_27a_pdf', label: 'Form 27A (PDF)', icon: 'fa-file-pdf-o', color: 'btn-danger' },
        { key: 'form24q_fvu', label: 'Form 24Q FVU File', icon: 'fa-file-code-o', color: 'btn-primary' },
        { key: 'form24q_txt', label: 'Form 24Q Text File', icon: 'fa-file-text-o', color: 'btn-info' },
        { key: 'challan_csi', label: 'Challan CSI File', icon: 'fa-file-o', color: 'btn-warning' },
        { key: 'fvu_log', label: 'FVU Log File', icon: 'fa-file-text-o', color: 'btn-secondary' },
        { key: 'warning_html', label: 'Warning File (HTML)', icon: 'fa-exclamation-triangle', color: 'btn-warning' },
        { key: 'statistics_html', label: 'Statistics Report (HTML)', icon: 'fa-bar-chart', color: 'btn-success' }
    ];
    
    fileOrder.forEach(fileInfo => {
        const file = files[fileInfo.key];
        if (file && file.file_url && !file.error) {
            downloadHtml += `
                <div class="col-md-6 col-lg-4" style="margin-bottom: 15px;">
                    <div class="file-download-card" style="border: 1px solid #ddd; border-radius: 6px; padding: 15px; background: #fafbfc;">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <i class="fa ${fileInfo.icon} text-muted" style="font-size: 18px; margin-right: 10px;"></i>
                            <div style="flex: 1;">
                                <strong style="font-size: 13px; color: #36414c;">${fileInfo.label}</strong>
                                <div style="font-size: 11px; color: #8d99a6;">${file.filename}</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 5px;">
                            <a href="${file.file_url}" target="_blank" class="btn ${fileInfo.color} btn-xs" style="flex: 1; text-align: center;">
                                <i class="fa fa-eye"></i> View
                            </a>
                            <a href="${file.file_url}" download="${file.filename}" class="btn btn-default btn-xs" style="flex: 1; text-align: center;">
                                <i class="fa fa-download"></i> Download
                            </a>
                        </div>
                        <div style="margin-top: 5px; font-size: 10px; color: #8d99a6; text-align: center;">
                            Size: ${format_file_size(file.size)}
                        </div>
                    </div>
                </div>
            `;
        } else if (file && file.error) {
            downloadHtml += `
                <div class="col-md-6 col-lg-4" style="margin-bottom: 15px;">
                    <div class="file-error-card" style="border: 1px solid #f56565; border-radius: 6px; padding: 15px; background: #fed7d7;">
                        <div style="display: flex; align-items: center;">
                            <i class="fa fa-exclamation-circle text-danger" style="font-size: 18px; margin-right: 10px;"></i>
                            <div>
                                <strong style="font-size: 13px; color: #e53e3e;">${fileInfo.label}</strong>
                                <div style="font-size: 11px; color: #c53030;">Error: ${file.error}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    downloadHtml += '</div>';
    
    // Add a summary section
    const successCount = fileOrder.filter(fileInfo => files[fileInfo.key] && files[fileInfo.key].file_url && !files[fileInfo.key].error).length;
    const totalCount = fileOrder.length;
    
    downloadHtml += `
        <div class="row" style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px;">
            <div class="col-md-12">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>Generation Summary:</strong> 
                        <span class="text-success">${successCount}/${totalCount} files generated successfully</span>
                    </div>
                    <div>
                        <button class="btn btn-primary btn-sm" onclick="download_all_files()">
                            <i class="fa fa-download"></i> Download All Files
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const uploadStatusElement = document.getElementById('upload-status');
    if (uploadStatusElement) {
        uploadStatusElement.insertAdjacentHTML('afterend', downloadHtml);
    }
}

// Replace your existing download_all_files function with this enhanced version
function download_all_files() {
    try {
        // Get all download links with proper validation
        const downloadLinks = document.querySelectorAll('a.download-link[download]');
        
        if (downloadLinks.length === 0) {
            frappe.msgprint({
                title: __('No Files Available'),
                message: __('No files are available for download. Please generate the files first.'),
                indicator: 'orange'
            });
            return;
        }
        
        // Show enhanced progress dialog
        const progressDialog = new frappe.ui.Dialog({
            title: __(`Downloading ${downloadLinks.length} FVU Files`),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'progress_area',
                    options: `
                        <div class="download-progress" style="text-align: center; padding: 30px;">
                            <div style="font-size: 18px; margin-bottom: 20px; color: #007bff;">
                                <i class="fa fa-cloud-download" style="font-size: 32px; margin-bottom: 10px;"></i>
                                <div>Preparing FVU file downloads...</div>
                            </div>
                            
                            <div class="progress" style="height: 25px; margin-bottom: 15px; background-color: #e9ecef;">
                                <div class="progress-bar progress-bar-striped active" 
                                     id="download-progress-bar" 
                                     style="width: 0%; transition: width 0.5s ease; background-color: #007bff;">
                                    <span id="progress-percentage">0%</span>
                                </div>
                            </div>
                            
                            <div id="download-status" style="margin-bottom: 15px; font-size: 14px; color: #495057; min-height: 40px;">
                                Initializing secure download sequence...
                            </div>
                            
                            <div id="file-list" style="max-height: 200px; overflow-y: auto; text-align: left; font-size: 12px; background: #f8f9fa; padding: 15px; border-radius: 5px;">
                                <strong>Files to download:</strong>
                                <ul id="file-items" style="margin: 10px 0; padding-left: 20px;"></ul>
                            </div>
                            
                            <div id="download-warnings" style="margin-top: 15px; font-size: 11px; color: #6c757d; text-align: left;">
                                <i class="fa fa-info-circle"></i> 
                                <strong>Note:</strong> Files will be downloaded with proper extensions. 
                                Large files may take a moment. Please don't close this window until complete.
                            </div>
                        </div>
                    `
                }
            ],
            primary_action_label: __('Cancel Downloads'),
            primary_action: function() {
                downloadCancelled = true;
                progressDialog.hide();
                frappe.show_alert({
                    message: __('Download cancelled by user'),
                    indicator: 'orange'
                }, 3);
            },
            size: 'large'
        });
        
        progressDialog.show();
        
        // Initialize file list
        setTimeout(() => {
            const fileListElement = document.getElementById('file-items');
            if (fileListElement) {
                downloadLinks.forEach((link, index) => {
                    const fileName = link.getAttribute('download');
                    const fileSize = link.getAttribute('data-size') || '0';
                    const listItem = document.createElement('li');
                    listItem.innerHTML = `
                        <span id="file-status-${index}" class="text-muted">
                            <i class="fa fa-clock-o"></i> Pending
                        </span>
                        ${fileName} (${format_file_size(parseInt(fileSize))})
                    `;
                    fileListElement.appendChild(listItem);
                });
            }
        }, 300);
        
        let downloadCancelled = false;
        let downloadCount = 0;
        let successCount = 0;
        let errorCount = 0;
        const totalFiles = downloadLinks.length;
        
        // Enhanced download function with proper MIME type handling
        const downloadFile = async (link, index) => {
            if (downloadCancelled) return { success: false, cancelled: true };
            
            try {
                // Update progress UI
                updateDownloadProgress(index, totalFiles, link.getAttribute('download'), 'downloading');
                
                const fileName = link.getAttribute('download');
                const fileUrl = link.href;
                const contentType = link.getAttribute('data-content-type') || 'application/octet-stream';
                const fileSize = parseInt(link.getAttribute('data-size') || '0');
                
                // Validate file extension
                const extension = fileName.split('.').pop().toLowerCase();
                const expectedMimeTypes = {
                    'html': 'text/html',
                    'fvu': 'application/xml',
                    'txt': 'text/plain',
                    'csi': 'text/plain',
                    'log': 'text/plain',
                    'xml': 'application/xml'
                };
                
                const expectedMimeType = expectedMimeTypes[extension] || 'application/octet-stream';
                
                // Fetch file with proper headers
                const response = await fetch(fileUrl, {
                    method: 'GET',
                    headers: {
                        'Accept': expectedMimeType,
                        'Cache-Control': 'no-cache'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const blob = await response.blob();
                
                // Create blob with correct MIME type
                const correctedBlob = new Blob([blob], { 
                    type: expectedMimeType 
                });
                
                // Validate file size
                if (fileSize > 0 && Math.abs(correctedBlob.size - fileSize) > (fileSize * 0.1)) {
                    console.warn(`File size mismatch for ${fileName}: expected ${fileSize}, got ${correctedBlob.size}`);
                }
                
                // Create and trigger download
                const downloadUrl = window.URL.createObjectURL(correctedBlob);
                const tempLink = document.createElement('a');
                tempLink.href = downloadUrl;
                tempLink.download = fileName;
                tempLink.style.display = 'none';
                
                document.body.appendChild(tempLink);
                tempLink.click();
                document.body.removeChild(tempLink);
                
                // Clean up URL after a delay
                setTimeout(() => {
                    window.URL.revokeObjectURL(downloadUrl);
                }, 1000);
                
                updateDownloadProgress(index, totalFiles, fileName, 'success');
                successCount++;
                return { success: true };
                
            } catch (error) {
                console.error(`Error downloading file ${index + 1}:`, error);
                updateDownloadProgress(index, totalFiles, link.getAttribute('download'), 'error', error.message);
                errorCount++;
                return { success: false, error: error.message };
            }
        };
        
        // Update progress UI function
        const updateDownloadProgress = (index, total, fileName, status, errorMsg = '') => {
            const progressBar = document.getElementById('download-progress-bar');
            const progressPercentage = document.getElementById('progress-percentage');
            const statusDiv = document.getElementById('download-status');
            const fileStatusElement = document.getElementById(`file-status-${index}`);
            
            const progress = ((index + (status === 'downloading' ? 0.5 : 1)) / total) * 100;
            
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
                if (progressPercentage) {
                    progressPercentage.textContent = `${Math.round(progress)}%`;
                }
            }
            
            if (statusDiv) {
                let statusText = '';
                switch (status) {
                    case 'downloading':
                        statusText = `Downloading file ${index + 1} of ${total}: ${fileName}`;
                        break;
                    case 'success':
                        statusText = `Successfully downloaded ${index + 1} of ${total} files`;
                        break;
                    case 'error':
                        statusText = `Error downloading file ${index + 1}: ${errorMsg}`;
                        break;
                    case 'complete':
                        statusText = `Download complete! ${successCount} successful, ${errorCount} failed`;
                        break;
                }
                statusDiv.textContent = statusText;
            }
            
            if (fileStatusElement) {
                let statusIcon = '';
                let statusClass = '';
                switch (status) {
                    case 'downloading':
                        statusIcon = '<i class="fa fa-spinner fa-spin"></i> Downloading';
                        statusClass = 'text-info';
                        break;
                    case 'success':
                        statusIcon = '<i class="fa fa-check-circle"></i> Downloaded';
                        statusClass = 'text-success';
                        break;
                    case 'error':
                        statusIcon = `<i class="fa fa-exclamation-circle"></i> Failed: ${errorMsg}`;
                        statusClass = 'text-danger';
                        break;
                }
                fileStatusElement.innerHTML = statusIcon;
                fileStatusElement.className = statusClass;
            }
        };
        
        // Download files sequentially with proper error handling
        const downloadSequentially = async () => {
            for (let i = 0; i < downloadLinks.length && !downloadCancelled; i++) {
                await downloadFile(downloadLinks[i], i);
                downloadCount++;
                
                // Add delay between downloads to prevent browser blocking
                if (i < downloadLinks.length - 1 && !downloadCancelled) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            
            if (!downloadCancelled) {
                // Update final progress
                const progressBar = document.getElementById('download-progress-bar');
                const statusDiv = document.getElementById('download-status');
                const primaryBtn = progressDialog.get_primary_btn()[0];
                
                if (progressBar) {
                    progressBar.style.width = '100%';
                    progressBar.classList.remove('active');
                    progressBar.classList.add(errorCount > 0 ? 'bg-warning' : 'bg-success');
                }
                
                if (statusDiv) {
                    const finalMessage = errorCount > 0 
                        ? `Download completed with ${errorCount} errors. ${successCount} of ${totalFiles} files downloaded successfully.`
                        : `All ${successCount} files downloaded successfully! Check your downloads folder.`;
                    statusDiv.innerHTML = `
                        <div style="color: ${errorCount > 0 ? '#856404' : '#155724'};">
                            <i class="fa fa-${errorCount > 0 ? 'exclamation-triangle' : 'check-circle'}"></i> 
                            ${finalMessage}
                        </div>
                    `;
                }
                
                if (primaryBtn) {
                    primaryBtn.innerHTML = '<i class="fa fa-check"></i> Close';
                    primaryBtn.onclick = () => progressDialog.hide();
                }
                
                // Auto-close dialog after 5 seconds if all successful
                if (errorCount === 0) {
                    setTimeout(() => {
                        progressDialog.hide();
                        frappe.show_alert({
                            message: __(`Successfully downloaded all ${successCount} FVU files!`),
                            indicator: 'green'
                        }, 5);
                    }, 5000);
                }
            }
        };
        
        // Start download sequence
        setTimeout(downloadSequentially, 500);
        
    } catch (error) {
        console.error('Error in download_all_files:', error);
        frappe.show_alert({
            message: __(`Error initiating downloads: ${error.message}. Please try downloading files individually.`),
            indicator: 'red'
        }, 8);
    }
}


// Validation function to check download readiness
function validate_download_readiness() {
    const downloadLinks = document.querySelectorAll('a.download-link[download]');
    const issues = [];
    
    downloadLinks.forEach((link, index) => {
        const fileName = link.getAttribute('download');
        const fileUrl = link.href;
        const contentType = link.getAttribute('data-content-type');
        
        if (!fileName) issues.push(`File ${index + 1}: Missing filename`);
        if (!fileUrl || fileUrl === '#') issues.push(`File ${index + 1}: Invalid URL`);
        if (!contentType) issues.push(`File ${index + 1}: Missing content type`);
        
        // Check file extension
        const extension = fileName ? fileName.split('.').pop().toLowerCase() : '';
        const validExtensions = ['html', 'fvu', 'txt', 'csi', 'log', 'xml'];
        if (!validExtensions.includes(extension)) {
            issues.push(`File ${index + 1}: Invalid extension .${extension}`);
        }
    });
    
    return {
        isValid: issues.length === 0,
        issues: issues,
        fileCount: downloadLinks.length
    };
}

// Add download readiness check before attempting downloads
function check_and_download_all_files() {
    const validation = validate_download_readiness();
    
    if (!validation.isValid) {
        frappe.msgprint({
            title: __('Download Validation Failed'),
            message: __('The following issues were found:<br><ul><li>' + validation.issues.join('</li><li>') + '</li></ul>'),
            indicator: 'red'
        });
        return;
    }
    
    if (validation.fileCount === 0) {
        frappe.msgprint({
            title: __('No Files Found'),
            message: __('No files are available for download. Please generate the FVU files first.'),
            indicator: 'orange'
        });
        return;
    }
    
    // Proceed with download
    download_all_files();
}
