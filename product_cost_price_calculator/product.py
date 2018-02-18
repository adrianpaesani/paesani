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

    _inherit = 'product.template'

    lp = fields.Float('Precio de Lista')
    cxu = fields.Float('Cantidad x Unidad', default=1)
    lp2 = fields.Float('Precio de Lista x Unidad', default=1)
    ds1 = fields.Float('Descuento 1')
    ds2 = fields.Float('Descuento 2')
    ds3 = fields.Float('Descuento 3')
    ds4 = fields.Float('Descuento 4')
    ch1 = fields.Float('Recargo 1')
    ch2 = fields.Float('Recargo 2')
    ch3 = fields.Float('Recargo 3')
    ch4 = fields.Float('Recargo 4')
    ex_cost1 = fields.Float('Cargos Extra 1')
    ex_cost2 = fields.Float('Cargos Extra 2')
    ex_cost3 = fields.Float('Cargos Extra 3')
    ex_cost4 = fields.Float('Cargos Extra 4')

    def on_change_price(self,cr,user,ids,lp,cxu,lp2,ds1,ds2,ds3,ds4,ch1,ch2,ch3,ch4,ex_cost1,ex_cost2,ex_cost3,ex_cost4,context=None):
        if cxu == 0:
            cxu = 1;

        lp2 = lp / cxu
        subtotal = (lp2 * (1-(ds1/100))) * (1-(ds2/100)) * (1-(ds3/100)) * (1-(ds4/100)) * (1+(ch1/100)) * (1+(ch2/100)) * (1+(ch3/100)) * (1+(ch4/100)) + ex_cost1 + ex_cost2 + ex_cost3 + ex_cost4
        
        res = {
            'value': {
                'cxu': cxu,
                'lp2': lp2,
                'standard_price': subtotal
                }
        }
        return res