# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

#-------------------------------------------------------------
# Locations
#-------------------------------------------------------------
class Location(models.Model):
	_name = 'cylinder.locations'
	_order = 'name desc, id desc'

	name = fields.Char('Name', required=True)
	address = fields.Char('Address')