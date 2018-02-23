# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models, api

class AccountInvoice(models.Model):

    """"""

    _inherit = 'account.invoice'

    comments = fields.Text('Additional Information')