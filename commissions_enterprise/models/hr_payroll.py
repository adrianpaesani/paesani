# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sale_commission_amount = fields.Float(string="Commission Amount", readonly=True, copy=False)

    @api.multi
    def compute_sheet(self):
        comm_obj = self.env['sales.commission']
        for payslip in self:
            commission = 0.0
            if payslip.employee_id.user_id:
                comm_ids = comm_obj.search([('user_id', '=', payslip.employee_id.user_id.id),
                                            ('commission_date', '>=', payslip.date_from),
                                            ('commission_date', '<=', payslip.date_to),
                                            ('pay_by', '=', 'salary'), ('state', '=', 'draft')])
                commission = sum([commid.amount for commid in comm_ids])
            payslip.sale_commission_amount = commission
        return super(HrPayslip, self).compute_sheet()

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        comm_obj = self.env['sales.commission']
        comm_rule_id = self.env.ref('sales_commission.hr_salary_rule_sales_commission')
        if comm_rule_id:
            for payslip in self:
                if payslip.employee_id.user_id and comm_rule_id.id in [line.salary_rule_id.id for line in payslip.line_ids]:
                    comm_ids = comm_obj.search([('user_id', '=', payslip.employee_id.user_id.id),
                                                ('commission_date', '>=', payslip.date_from),
                                                ('commission_date', '<=', payslip.date_to),
                                                ('pay_by', '=', 'salary'), ('state', '=', 'draft')])
                    comm_ids.write({'state': 'paid'})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: