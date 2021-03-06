# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

#-------------------------------------------------------------
# Cylinder
#-------------------------------------------------------------
class Cylinder(models.Model):
	_name = 'cylinder.cylinders'
	_rec_name = 'number'
	_order = 'gas_id desc, number desc, id desc'

	# Cylinder Info
	number = fields.Char('Cylinder Number', required=True)
	propietary_id = fields.Many2one('res.partner', string='Propietary')
	details = fields.Text('Detailed Information')
	gas_id = fields.Many2one('cylinder.gases', string='Type of Gas')
	capacity_id = fields.Many2one('cylinder.capacity', string='Capacity')
	cap = fields.Boolean('Has cap', default=True)
	active = fields.Boolean('Active', default=True)
	plant = fields.Boolean('Is in plant', default=True)
	ht_date = fields.Date('Last Hidraulic Test')
	location_id = fields.Many2one('cylinder.locations', string='Location')
	# Rental Info
	rental = fields.Boolean('Is active for Rent', default=True)
	rented = fields.Boolean(string="Is rented", default=False)
	# Plant Info Arrival
	plant_arrival_date = fields.Date('Creation Date')
	arrival_control_number = fields.Char('Arrival from plant control ticket number')
	control_arrival_detail = fields.Text('Detailed information about plant control')
	# Plant Info Send
	plant_send_date = fields.Date('Creation Date')
	send_control_number = fields.Char('Send to plant control ticket number')
	control_send_detail = fields.Text('Detailed information about plant control')
	# Remit Info
	partner_id = fields.Many2one('res.partner', string='Partner')
	last_rent_partner_id = fields.Many2one('res.partner', string='Partner')
	last_rental_date = fields.Date('Last Rental Date')
	last_return_date = fields.Date('Last Return Date')
	# Extras
	days_rented = fields.Float(digits=(6,2), compute='_calculation')

	days_plant = fields.Float(digits=(6,2), compute='_calculation_from_plant')

	charge_status = fields.Selection([
		('full', 'Full'),
		('empty', 'Empty'),
		('half', 'Half Charge'),
		], string='Cylinder Status', copy=False, store=True, default='full')

	_sql_constraints = [
		('number_unique',
			'UNIQUE(number)',
			"The number must be unique!.\nThis number already exists."),
		]

	@api.depends('last_rental_date')
	def _calculation(self):
		for r in self:
			if not r.last_rental_date:
				r.days_rented = 0
			else:
				start_date = fields.Datetime.from_string(r.last_rental_date)
				end_date = fields.Datetime.from_string(fields.Date.today())
				r.days_rented = (end_date - start_date).days

	@api.depends('plant_arrival_date')
	def _calculation_from_plant(self):
		for r in self:
			if not r.plant_arrival_date:
				r.days_plant = 0
			else:
				start_date = fields.Datetime.from_string(r.plant_arrival_date)
				end_date = fields.Datetime.from_string(fields.Date.today())
				r.days_plant = (end_date - start_date).days