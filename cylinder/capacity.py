# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

#-------------------------------------------------------------
# Capacity of Cylinder
#-------------------------------------------------------------
class Capacity(models.Model):
	_name = 'cylinder.capacity'
	_order = 'name desc, id desc'

	name = fields.Char('Name', required=True)