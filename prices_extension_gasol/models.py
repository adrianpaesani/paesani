# -*- coding: utf-8 -*-

from openerp import models, fields, api

class on_change_function(models.Model):
    #Inhertis the model product.template
    _inherit = 'product.product'
    #Creates new fields (ListPrice, Discount1, Discount2, Discount3, Discount4, Charge1, Charge2, Charge3, Charge4) in the model product.template
    ListPrice = fields.Float('List Price')
    Discount1 = fields.Float('Discount1')
    Discount2 = fields.Float('Discount2')
    Discount3 = fields.Float('Discount3')
    Discount4 = fields.Float('Discount4')
    Charge1 = fields.Float('Charge1')
    Charge2 = fields.Float('Charge2')
    Charge3 = fields.Float('Charge3')
    Charge4 = fields.Float('Charge4')
		
	@api.multi
	@api.onchange('ListPrice','Discount1','Discount2','Discount3','Discount4','Charge1','Charge2','Charge3','Charge4')
	def on_change_price(self):

	
        subtotal = (ListPrice * (1-(Discount1/100))) * (1-(Discount2/100)) * (1-(Discount3/100)) * (1-(Discount4/100)) * (1+(Charge1/100)) * (1+(Charge2/100)) * (1+(Charge3/100)) * (1+(Charge4/100))
		values = {
			'standard_price': subtotal,
		}

		self.update(values)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: