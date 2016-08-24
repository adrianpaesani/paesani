# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

#-------------------------------------------------------------
# Capacity of Cylinder
#-------------------------------------------------------------
class Capacity(models.Model):
	_name = 'cylinder.capacity'

	name = fields.Char('Name', required=True)