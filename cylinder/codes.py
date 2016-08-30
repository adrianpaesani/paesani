# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

#-------------------------------------------------------------
# Codes for Capacities
#-------------------------------------------------------------
class Capacity(models.Model):
	_name = 'cylinder.codes'
	_order = 'name desc, id desc'

	name = fields.Char('Name', required=True)