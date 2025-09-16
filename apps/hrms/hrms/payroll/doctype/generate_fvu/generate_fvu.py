# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import os
from frappe.model.document import Document


class GenerateFVU(Document):
	
	def autoname(self):
		if self.upload_csi_file:
			# Extract filename without extension
			file_path = self.upload_csi_file
			filename = os.path.basename(file_path) 
			filename_no_ext = os.path.splitext(filename)[0]


			# Get existing records with same base name
			existing = frappe.get_all(
				'Generate FVU',
				filters={'name': ['like', f'{filename_no_ext}_%']},
				fields=['name']
			)
			# Find existing suffix numbers
			suffix_numbers = []
			for d in existing:
				parts = d['name'].split('_')
				if len(parts) == 2 and parts[1].isdigit():
					suffix_numbers.append(int(parts[1]))

			next_suffix = (max(suffix_numbers) + 1) if suffix_numbers else 1

			# Set final document name
			self.name = f"{filename_no_ext}_{next_suffix}"
		else:
			frappe.throw("Upload CSI File is required to generate the document name.")

	def on_trash(self):
		if self.upload_csi_file:
			file_url = self.upload_csi_file

			file_doc = frappe.get_all('File', filters={'file_url': file_url}, limit=1)
			if file_doc:
				file_name = file_doc[0]['name']
				frappe.delete_doc('File', file_name, force=True)