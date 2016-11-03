# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

#-------------------------------------------------------------
# Type of Gas
#-------------------------------------------------------------
class Gas(models.Model):
	_name = 'cylinder.gases'
	_order = 'name desc, id desc'

	name = fields.Char('Name', required=True)
	description = fields.Text()
	
	capacity_ids = fields.One2many('cylinder.capacity', 'gases_id', 'Capacity')