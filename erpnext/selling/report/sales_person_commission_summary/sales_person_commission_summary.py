# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt


def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)
	entries = get_entries(filters)
	data = []

	for d in entries:
		if filters.get("doc_type") and filters.get("doc_type") == "Sales Invoice":
			
			target = frappe.db.sql("""select monthly_sales_target from `tabBranch` where name = '{}'""".format(d.branch))
			if not target:
				target = 0.0
			else:
				target = target[0][0]
			data.append([
				d.name, d.customer,d.customer_name, d.branch,target, d.posting_date,d.created_by,
				d.base_net_amount, d.sales_person, d.commission_rate, d.incentives
			])			
		else:
			data.append([
				d.name, d.customer, d.territory, d.posting_date,
				d.base_net_amount, d.sales_person, d.allocated_percentage, d.commission_rate, d.allocated_amount,d.incentives
			])

	if data:
		total_row = [""]*len(data[0])
		data.append(total_row)

	return columns, data

def get_columns(filters):
	if not filters.get("doc_type"):
		msgprint(_("Please select the document type first"), raise_exception=1)
	if filters.get("doc_type") and filters.get("doc_type") == "Sales Invoice":
			columns =[
		{
			"label": _(filters["doc_type"]),
			"options": filters["doc_type"],
			"fieldname": filters['doc_type'],
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Customer"),
			"options": "Customer",
			"fieldname": "customer",
			"fieldtype": "Link",
			"width": 100
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Branch"),
			"options": "Branch",
			"fieldname": "territory",
			"fieldtype": "Link",
			"width": 100
		},
		{
			"label": _("Sales Target"),
			"fieldname": "sales_target",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Created By"),
			"fieldname": "created_by",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Sales Person"),
			"options": "Sales Person",
			"fieldname": "sales_person",
			"fieldtype": "Link",
			"width": 120
		},
		{
			"label": _("Commission Rate %"),
			"fieldname": "commission_rate",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Incentives"),
			"fieldname": "incentives",
			"fieldtype": "Currency",
			"width": 100
		}
	]
	else:
		columns =[
			{
				"label": _(filters["doc_type"]),
				"options": filters["doc_type"],
				"fieldname": filters['doc_type'],
				"fieldtype": "Link",
				"width": 140
			},
			{
				"label": _("Customer"),
				"options": "Customer",
				"fieldname": "customer",
				"fieldtype": "Link",
				"width": 140
			},
			{
				"label": _("Territory"),
				"options": "Territory",
				"fieldname": "territory",
				"fieldtype": "Link",
				"width": 100
			},
			{
				"label": _("Posting Date"),
				"fieldname": "posting_date",
				"fieldtype": "Date",
				"width": 100
			},
			{
				"label": _("Amount"),
				"fieldname": "amount",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"label": _("Sales Person"),
				"options": "Sales Person",
				"fieldname": "sales_person",
				"fieldtype": "Link",
				"width": 140
			},
			{
				"label": _("Contribution %"),
				"fieldname": "contribution_percentage",
				"fieldtype": "Data",
				"width": 110
			},
			{
				"label": _("Commission Rate %"),
				"fieldname": "commission_rate",
				"fieldtype": "Data",
				"width": 100
			},
			{
				"label": _("Contribution Amount"),
				"fieldname": "contribution_amount",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"label": _("Incentives"),
				"fieldname": "incentives",
				"fieldtype": "Currency",
				"width": 120
			}
		]

	return columns

def get_entries(filters):
	date_field = filters["doc_type"] == "Sales Order" and "transaction_date" or "posting_date"
	
	conditions, values = get_conditions(filters, date_field)
	if filters.get("doc_type") and filters.get("doc_type") == "Sales Invoice":
		entries = frappe.db.sql("""
			select
				dt.name, dt.customer,ifnull(dt.customer_name,dt.customer) as customer_name, (select branch from `tabPOS Profile` where name = dt.pos_profile) as branch, dt.owner as created_by, dt.%s as posting_date,dt.base_net_total as base_net_amount,
				st.commission_rate,st.sales_person, st.allocated_percentage, st.allocated_amount, st.incentives
			from
				`tab%s` dt, `tabSales Team` st
			where
				st.parent = dt.name and st.parenttype = %s
				and dt.outstanding_amount = 0 and dt.docstatus = 1 %s order by dt.name desc,st.sales_person 
			""" %(date_field, filters["doc_type"], '%s', conditions),
				tuple([filters["doc_type"]] + values), as_dict=1)
	else:
		entries = frappe.db.sql("""
			select
				dt.name, dt.customer, dt.territory, dt.%s as posting_date,dt.base_net_total as base_net_amount,
				st.commission_rate,st.sales_person, st.allocated_percentage, st.allocated_amount, st.incentives
			from
				`tab%s` dt, `tabSales Team` st
			where
				st.parent = dt.name and st.parenttype = %s
				and dt.docstatus = 1 %s order by dt.name desc,st.sales_person 
			""" %(date_field, filters["doc_type"], '%s', conditions),
				tuple([filters["doc_type"]] + values), as_dict=1)

	return entries

def get_conditions(filters, date_field):
	conditions = [""]
	values = []

	for field in ["company", "customer", "territory"]:
		if filters.get(field):
			conditions.append("dt.{0}=%s".format(field))
			values.append(filters[field])

	if filters.get("sales_person"):
		conditions.append("st.sales_person = '{0}'".format(filters.get("sales_person")))

	if filters.get("from_date"):
		conditions.append("dt.{0}>=%s".format(date_field))
		values.append(filters["from_date"])

	if filters.get("to_date"):
		conditions.append("dt.{0}<=%s".format(date_field))
		values.append(filters["to_date"])

	# if filters.get("branch"):
	# 	conditions.append("st.sales_person = '{0}'".format(filters.get("sales_person")))
	if filters.get("pos"):
		conditions.append("dt.pos_profile = '{0}'".format(filters.get("pos")))
	if filters.get("owner"):
		conditions.append("dt.owner = '{0}'".format(filters.get("owner")))
	conditions.append("dt.customer_group not in ('Kapok Internal','NUST','MicroMerger','Daraz Order','Online','Family','Friends','Website Order') ")
	return " and ".join(conditions), values


