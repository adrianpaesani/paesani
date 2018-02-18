# -*- coding: utf-8 -*-

{
    'name': 'Sales Commissions Enterprise',
    'summary': 'Commission to Sales Person',
    'version': '9.1.0',
    'description' :"""Sales Commissions for Enterprise.""",
    'author': 'Adrian Paesani',
    'category': 'Sales',
    'depends' : ['base', 'account', 'sale', 'hr_payroll'],
    'data' : [
        'security/ir.model.access.csv',
        'views/sale_invoice_scheduler.xml',
        'views/sale_team_view.xml',
        'views/sale_view.xml',
        'views/product_view.xml',
        'views/sales_commission.xml',
        'views/hr_payroll_view.xml',
        'views/account_view.xml',
        'data/hr_payroll_data.xml',
        'report/print_commission_summary_template.xml',
        'report/report.xml',
        'wizard/sales_commission_payment_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 