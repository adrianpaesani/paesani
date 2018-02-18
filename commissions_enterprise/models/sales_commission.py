# -*- coding: utf-8 -*-
from openerp import models, fields, api, _


class SalesCommission(models.Model):
    _name = 'sales.commission'
    _order = 'commission_date desc'

    @api.one
    def state_cancel(self):
        if self.state == 'draft' and not self.invoice_id:
            self.state = 'cancel'

    @api.model
    def generate_sale_invoice(self):
        commission_ids = self.env['sales.commission'].search([('state', '=', 'draft'), ('pay_by', '=', 'invoice'),
                                                              '|', ('invoice_id', '=', False), ('invoice_id.state', '=', 'cancel')])
        user_lst = [comm.user_id.id for comm in commission_ids]
        sale_comm_pay_obj = self.env['sales.commission.payment']
        for user in set(user_lst):
            rec_id = sale_comm_pay_obj.create({'user_id': user})
            rec_id.with_context({'commission_ids': commission_ids.filtered(lambda line: line.user_id.id == user)}).generate_invoice()

    name = fields.Char(string="Source Document")
    user_id = fields.Many2one('res.users', string="User")
    commission_date = fields.Date(string="Commission Date")
    amount = fields.Float(string="Amount")
    pay_by = fields.Selection([('salary', 'Salary'), ('invoice', 'Invoice')], string="Pay By", default="invoice")
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid'),
                              ('cancel', 'Cancel')], string="State", default='draft')
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    reference_invoice_id = fields.Many2one('account.invoice', string='Reference')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: