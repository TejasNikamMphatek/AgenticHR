# Copyright (c) 2022, mPHATEK Systems Pvt. Ltd. and Contributors
# See license.txt


def get_data():
	return {
		"fieldname": "license_plate",
		"non_standard_fieldnames": {"Delivery Trip": "vehicle"},
		"transactions": [{"items": ["Vehicle Log"]}, {"items": ["Delivery Trip"]}],
	}
