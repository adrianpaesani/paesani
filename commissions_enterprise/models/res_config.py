# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class AccountConfiguration(models.TransientModel):
    _inherit = 'account.config.settings'

    @api.multi
    def set_commission_account_id_defaults(self):
        return self.env['ir.values'].sudo().set_default('account.config.settings', 'commission_account_id', self.commission_account_id.id)

    commission_account_id = fields.Many2one('account.account', string="Commission Account")


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    @api.multi
    def set_commission_pay_on_defaults(self):
        return self.env['ir.values'].sudo().set_default('sale.config.settings', 'commission_pay_on', self.commission_pay_on)

    @api.multi
    def set_commission_calc_defaults(self):
        return self.env['ir.values'].sudo().set_default('sale.config.settings', 'commission_calc', self.commission_calc)

    @api.multi
    def set_commission_pay_by_defaults(self):
        return self.env['ir.values'].sudo().set_default('sale.config.settings', 'commission_pay_by', self.commission_pay_by)

    commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Commission Pay On")
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation")
    commission_pay_by = fields.Selection([('invoice', 'Invoice'), ('salary', 'Salary')], string="Commission Pay By")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: