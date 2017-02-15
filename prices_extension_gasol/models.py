# -*- coding: utf-8 -*-

from openerp import models, fields, api

# class on_change_function(models.Model):
    # #Inhertis the model product.template
    # _inherit = 'product.template'
    # #Creates new fields (ListPrice, Discount1, Discount2, Discount3, Discount4, Charge1, Charge2, Charge3, Charge4) in the model product.template
    # list_price_def = fields.Float('List Price')
    # discount1 = fields.Float('Discount1')
    # discount2 = fields.Float('Discount2')
    # discount3 = fields.Float('Discount3')
    # discount4 = fields.Float('Discount4')
    # charge1 = fields.Float('Charge1')
    # charge2 = fields.Float('Charge2')
    # charge3 = fields.Float('Charge3')
    # charge4 = fields.Float('Charge4')
		
    # @api.multi
    # @api.onchange('list_price_def','discount1','discount2','discount3','discount4','charge1','charge2','charge3','charge4')
    # def on_change_price(self):

        # subtotal = (list_price_def * (1-(discount1/100))) * (1-(discount2/100)) * (1-(discount3/100)) * (1-(discount4/100)) * (1+(charge1/100)) * (1+(charge2/100)) * (1+(charge3/100)) * (1+(charge4/100))
        # values = {
            # 'standard_price': subtotal,
        # }

        # self.update(values)

# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
class on_change_function(models.Model):
    #Inhertis the model product.template
    _inherit = 'product.template'
    #Creates two new fields (CostPrice and ShippingCost) in the model product.template
    CostPrice = fields.Float('Buy price')
    ShippingCost = fields.Float('Shipping Cost')

    #This method will be called when either the field CostPrice or the field ShippingCost changes.
    def on_change_price(self,cr,user,ids,CostPrice,ShippingCost,context=None):
	#Calculate the total
	total = CostPrice + ShippingCost
        res = {
            'value': {
		#This sets the total price on the field standard_price.
                'standard_price': total
	      }
	}
	#Return the values to update it in the view.
	return res