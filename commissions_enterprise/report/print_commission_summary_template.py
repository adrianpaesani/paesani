# -*- coding: utf-8 -*-
from openerp import models, api, _


class PrintCommissionSummaryTemplate(models.AbstractModel):
    _name = 'report.sales_commission.print_commission_summary_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('sales_commission.print_commission_summary_template')
        docargs = {
            'doc_ids': self.env['wizard.commission.summary'].search([('id', 'in', list(data["ids"]))]),
            'doc_model': report.model,
            'docs': self,
            'data': data,
            'get_sorted_summary': self._get_sorted_summary
        }
        return report_obj.render('sales_commission.print_commission_summary_template', docargs)

    def _get_sorted_summary(self, summary):
        return sorted(summary.items(), key=lambda item: item[1], reverse=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: