# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models, api

    # @api.multi
    # @api.onchange('list_price_def','discount1','discount2','discount3','discount4','charge1','charge2','charge3','charge4')
    # def on_change_price(self):

        # subtotal = (list_price_def * (1-(discount1/100))) * (1-(discount2/100)) * (1-(discount3/100)) * (1-(discount4/100)) * (1+(charge1/100)) * (1+(charge2/100)) * (1+(charge3/100)) * (1+(charge4/100))
        # values = {
            # 'standard_price': subtotal,
        # }

        # self.update(values)

# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


class product(models.Model):

    """"""

    _inherit = 'product.product'

    lp = fields.Float('List Price')
    ds1 = fields.Float('Discount 1')
    ds2 = fields.Float('Discount 2')
    ds3 = fields.Float('Discount 3')
    ds4 = fields.Float('Discount 4')
    ch1 = fields.Float('Charge 1')
    ch2 = fields.Float('Charge 2')
    ch3 = fields.Float('Charge 3')
    ch4 = fields.Float('Charge 4')

    @api.multi
    @api.onchange('list_price_def','discount1','discount2','discount3','discount4','charge1','charge2','charge3','charge4')
    def on_change_price(self)
    
        subtotal = (lp * (1-(ds1/100))) * (1-(ds2/100)) * (1-(ds3/100)) * (1-(ds4/100)) * (1+(ch1/100)) * (1+(ch2/100)) * (1+(ch3/100)) * (1+(ch4/100))

        res = {
            'value': {
                'standard_price': subtotal
                }
        }
        return res


# class product_template(models.Model):

#     """"""

#     _inherit = 'product.template'

#     lp = fields.Float('List Price')
#     ds1 = fields.Float('Discount 1')
#     ds2 = fields.Float('Discount 2')
#     ds3 = fields.Float('Discount 3')
#     ds4 = fields.Float('Discount 4')
#     ch1 = fields.Float('Charge 1')
#     ch2 = fields.Float('Charge 2')
#     ch3 = fields.Float('Charge 3')
#     ch4 = fields.Float('Charge 4')

#     internal_code = fields.Char(
#         related='product_variant_ids.internal_code',
#         string='Internal Code')