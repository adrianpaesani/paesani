from datetime import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidatoinError
from odoo.tools import float_compare

class CriogenicOrder(models.Model):
    _name = 'crio.order'
    _description = "Criogenic Partner Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def _default_stock_location(self):
        warehouse = self.env['stock.warehouse'].search([], limit=1)

    # Order Info
    name = fields.Char(
        'Order Reference',
        default=lambda self: self.env['ir.sequence'].next_by_code('crio.partner_order'),
        copy=False, required=True,
        states={'confirmed': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Order'),
        ('sent', 'Order Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
                                 default=fields.Datetime.now)
    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True,
                                  help="Date on which sales order is created.")
    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=True, index=True,
                                        help="Date on which the sales order is confirmed.", oldname="date_confirm",
                                        copy=False)

    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    # Partner Info
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, states={'confirmed': [('readonly', True)]},
        help='Choose partner for whom the order will be invoiced and delivered.')
    address_id = fields.Many2one(
        'res.partner', 'Delivery Address',
        domain="[('parent_id','=',partner_id)]",
        states={'confirmed': [('readonly', True)]})
    default_address_id = fields.Many2one('res.partner', compute='_compute_default_address_id')

    # Order Lines
    lines_out = fields.One2many('crio.order.line_out', 'order_id', 'Out', copy=True, readonly=True,
                                     states={'draft': [('readonly', False)]})
    lines_in = fields.One2many('crio.order.line_in', 'order_id', 'In', copy=True, readonly=True,
                                    states={'draft': [('readonly', False)]})

    # Invoice Info
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist',
        default=lambda self: self.env['product.pricelist'].search([], limit=1).id,
        help='Pricelist of the selected partner.')
    partner_invoice_id = fields.Many2one('res.partner', 'Invoicing Address')
    invoice_id = fields.Many2one(
        'account.invoice', 'Invoice',
        copy=False, readonly=True, track_visibility="onchange")
    invoice_status = fields.Selection([
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Invoice Status', compute='_get_invoiced', store=True, readonly=True)
    invoice_method = fields.Selection([
        ("none", "No Invoice"),
        ("invoice", "To Invoice"),
    ], string="Invoice Method", default='invoice', index=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]})

    # Extra Fields
    internal_notes = fields.Text('Internal Notes')
    order_notes = fields.Text('Order Notes')
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('crio.order'))
    invoiced = fields.Boolean('Invoiced', copy=False, readonly=True)

    # Computation
    amount_untaxed = fields.Float('Untaxed Amount', compute='_amount_untaxed', store=True)
    amount_tax = fields.Float('Taxes', compute='_amount_tax', store=True)
    amount_total = fields.Float('Total', compute='_amount_total', store=True)

    # Location
    location_id = fields.Many2one(
        'stock.location', 'Current Location',
        default=_default_stock_location,
        index=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})
    location_dest_id = fields.Many2one(
        'stock.location', 'Delivery Location',
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})

    @api.one
    @api.depends('partner_id')
    def _compute_default_address_id(self):
        if self.partner_id:
            self.default_address_id = self.partner_id.address_get(['contact'])['contact']

    @api.one
    @api.depends('lines_in.price_subtotal', 'invoice_method', 'lines_in.price_subtotal', 'pricelist_id.currency_id')
    def _amount_untaxed(self):
        total = sum(lines_in.price_subtotal for lines_in in self.lines_in)
        self._amount_untaxed = self.pricelist_id.currency_id.round(total)

    @api.one
    @api.depends('lines_in.price_unit', 'lines_in.product_uom_qty', 'lines_in.product_id',
                 'pricelist_id.currency_id', 'partner_id')
    def _amount_tax(self):
        val = 0.0
        for lines_in in self.lines_in:
            if lines_in.tax_id:
                tax_calculate = lines_in.tax_id.compute_all(lines_in.price_unit, self.pricelist_id.currency_id, lines_in.product_uom_qty, lines_in.product_id, self.partner_id)
                for c in tax_calculate['taxes']:
                    val +=c['amount']
            self._amount_tax = val

    @api.one
    @api.depends('amount_untaxed', 'amount_tax')
    def _amount_total(self):
        self.amount_total = self.pricelist_id.currency_id.round(self.amount_untaxed + self.amount_tax)

    _sql_constraints = [
        ('name', 'unique (name)', 'The name of the Order must be unique!'),
    ]

    @api.onchange('location_id')
    def onchange_location_id(self):
        self.location_dest_id = self.location_id.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.address_id = False
            self.partner_invoice_id = False
            self.pricelist_id = self.env['product.pricelist'].search([], limit=1).id
        else:
            addresses = self.partner_id.address_get(['delivery', 'invoice', 'contact'])
            self.address_id = addresses['delivery'] or addresses['contact']
            self.partner_invoice_id = addresses['invoice']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.multi
    def action_order_confirm(self):
        if self.filtered(lambda order: order.state != 'draft'):
            raise UserError(_('Can only confirm draft orders.'))

    @api.multi
    def action_draft_order(self):


    @api.multi
    def action_cancel_order(self):
        if self.filtered(lambda order: order.state != 'cancel'):
            raise UserError(_("Order must be canceled in order to reset it to draft."))
        self.mapped('lines_in').write({'state': 'draft'})
        return self.write({'state': 'draft'})

    @api.multi
    def action_send_order(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('crio', 'email_template_crio')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'crio.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': 'crio.mail_template_data_notification_email_crio_order',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_force_order_send(self):
        for order in self:
            email_act = order.action_send_order()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=order.company_id.email)
                order.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
        return True

    @api.multi
    def action_done_order(self):
        return self.write({'state': 'done'})

    @api.multi
    def _action_confirm_order(self):
        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        if self.env.context.get('send_email'):
            self.action_force_order_send()

        return True

    @api.multi
    def action_confirm_order(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_('It is not allowed to confirm an order in the following states: %s') % (', '.join(self.get_forbidden_state_confirm())))
        self._action_confirm_order()
        if self.env['ir.config.parameter'].sudo().get_param('crio.auto_done_setting'):
            self.action_done_order()
        return True

    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel'}

    @api.multi
    def action_print_order(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref('crio.action_report_crio_order').report_action(self)

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_invoice_create(self, group=False):
        """
        Creates invoice(s) for order
        :param grouped: It is set to true when group invoice is to be generated.
        :return: Invoice Ids.
        """
        res = dict.fromkeys(self.ids, False)
        invoices_group = {}
        InvoiceLine = self.env['account.invoice.line']
        Invoice = self.env['account.invoice']
        for order in self.filtered(lambda order: order.state not in ('draft', 'cancel') and not order.invoice_id):
            if not order.partner_id.id and not order.partner_invoice_id.id:
                raise UserError(_('You have to select a Partner Invoice Address in the order form!'))
            comment = order.order_notes
            if order.invoice_method != 'none':
                if group and order.partner_invoice_id.id in invoices_group:
                    invoice = invoices_group[order.partner_invoice_id.id]
                    invoice.write({
                        'name': invoice.name + ', ' + order.name,
                        'origin': invoice.origin + ', ' + order.name,
                        'comment': (comment and (invoice.comment and invoice.comment + "\n" + comment or comment)) or (invoice.comment and invoice.comment or ''),
                    })
                else:
                    if not order.partner_id.property_account_receivable_id:
                        raise UserError(_('No account defined for partner "%s.') % order.partner_id.name)
                    invoice = Invoice.create({
                        'name': order.name,
                        'origin': order.name,
                        'type': 'out_invoice',
                        'account_id': order.partner_id.property_account_receivable_id.id,
                        'partner_id': order.partner_invoice_id.id or order.partner_id.id,
                        'currency_id': order.pricelist_id.currency_id.id,
                        'comment': order.order_notes,
                        'fiscal_position_id': order.partner_id.property_account_position_id.id
                    })
                    invoices_group[order.partner_invoice_id.id] = invoice
                order.write({'invoiced': True, 'invoice_id': invoice.id})

                for line_in in order.lines_in:
                    if line_in.type == 'invoice':
                        if group:
                            name = order.name + '-' + line_in.name
                        else:
                            name = line_in.name

                        if line_in.product_id.property_account_income_id:
                            account_id = line_in.product_id.property_account_income_id.id
                        elif line_in.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_in.product_id.categ_id.property_account_income_categ_id.id
                        else:
                            raise UserError(_('No account defined for product "%s".') % line_in.product_id.name)

                        invoice_line = InvoiceLine.create({
                            'invoice_id': invoice.id,
                            'name': name,
                            'origin': order.name,
                            'account_id': account_id,
                            'quantity': order.product_uom_qty,
                            'invoice_line_tax_ids': [(6, 0, [x.id for x in order.tax_id])],
                            'uom_id': order.product_uom.id,
                            'price_unit': order.price_unit,
                            'price_subtotal': order.product_uom_qty * order.price_unit,
                            'product_id': order.product_id and order.product_id.id or False
                        })
                        line_in.write({'invoiced': True, 'invoice_line_id': invoice_line.id})
                    invoice.compute_taxes()
                    res[order.id] = invoice.id
            return res

    @api.multi
    def action_created_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoice created'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': self.env.ref('account.invoice_form').id,
            'target': 'current',
            'res_id': self.invoice_id.id,
        }

    class OrderLineIn(models.Model):
        _name = 'crio.order.line_in'
        _description = 'Order Line In'

        name = fields.Char('Description', required=True)
        order_id = fields.Many2one('crio.order', 'Order Reference', index=True, ondelete='cascade')
        type = fields.Selection([
            ('none','None'),
            ('invoice', 'To Invoice')
        ], 'Type', required=True)
        product_id = fields.Many2one('crio.package.product_id', 'Product', required=True)
        invoiced = fields.Boolean('Invoiced', copy=False, readonly=True)
        price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'))
        price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', digits=0)
        tax_id = fields.Many2many('account.tax', 'order_line_in_tax', 'order_line_in_id', 'tax_id', 'Taxes')
        product_uom_qty = fields.Float('Quantity', compute='_rental_days', digits=dp.get_precision('Product Unit of Measure'), required=True)
        product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
        invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice Line', copy=False, readonly=True)
        location_id = fields.Many2one(
            'stock.location', 'Source Location',
            index=True, required=True)
        state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')], 'Status', default='draft',
            copy=False, readonly=True, required=True,
            help='The status of a order line is set automatically to the one of the linked order.')

    # state = fields.Selection([
    #     ('draft', 'Order'),
    #     ('sent', 'Order Sent'),
    #     ('sale', 'Sales Order'),
    #     ('done', 'Locked'),
    #     ('cancel', 'Cancelled'),
    # ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    # invoice_status = fields.Selection([
    #     ('invoiced', 'Fully Invoiced'),
    #     ('to invoice', 'To Invoice'),
    #     ('no', 'Nothing to Invoice')
    # ], string='Invoice Status', compute='_get_invoiced', store=True, readonly=True)

    # invoice_method = fields.Selection([
    #     ("none", "No Invoice"),
    #     ("invoice", "To Invoice"),
    # ], string="Invoice Method", default='invoice', index=True, readonly=True, required=True,
    #     states={'draft': [('readonly', False)]})
