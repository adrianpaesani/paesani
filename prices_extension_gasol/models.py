# -*- coding: utf-8 -*-

from openerp import models, fields, api

class on_change_function(models.Model):
    #Inhertis the model product.template
    _inherit = 'product.template'
    #Creates new fields (ListPrice, Discount1, Discount2, Discount3, Discount4, Charge1, Charge2, Charge3, Charge4) in the model product.template
    ListPrice = fields.Float('List Price')
    Discount1 = fields.Float('Discount1')
    Discount1 = fields.Float('Discount2')
    Discount3 = fields.Float('Discount3')
    Discount4 = fields.Float('Discount4')
    Charge1 = fields.Float('Charge1')
    Charge2 = fields.Float('Charge2')
    Charge3 = fields.Float('Charge3')
    Charge4 = fields.Float('Charge4')

    #This method will be called when either the field CostPrice or the field ShippingCost changes.
    def on_change_price(self,cr,user,ids,ListPrice,Discount1,Discount2,Discount3,Discount4,Charge1,Charge2,Charge3,Charge4,context=None):
    #Calculate the total
        subtotal = (ListPrice * (1-(Discount1/100))) * (1-(Discount2/100)) * (1-(Discount3/100)) * (1-(Discount4/100)) * (1+(Discount1/100)) * (1+(Charge1/100)) * (1+(Charge2/100)) * (1+(Charge3/100)) * (1+(Charge4/100))
        res = {
            'value': {
        #This sets the total price on the field standard_price.
                'standard_price': subtotal
        }
    }
        #Return the values to update it in the view.
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: