# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

#-------------------------------------------------------------
# Type of Gas
#-------------------------------------------------------------
class Gas(models.Model):
	_name = 'cylinder.gases'

	name = fields.Char('Name', required=True)
	description = fields.Text()