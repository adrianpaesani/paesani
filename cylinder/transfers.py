# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
from datetime import timedelta
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class CylinderTransfer(models.Model):
	_name = "cylinder.transfer"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Cylinder Transfer"
	_order = 'date_transfer desc, id desc'


	name = fields.Char(string='Transfer Reference', required = True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))

	state = fields.Selection([
		('draft', 'Preparation'),
		('sent', 'Preparation Send'),
		('transfer', 'Cylinder Transfer'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	date_transfer = fields.Date(string='Transfer Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Date.today)
	create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which transfer is created.")

	user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	location_id = fields.Many2one('cylinder.locations', string='Transfer Location', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')

	transfer_line = fields.One2many('cylinder.transfer.line', 'transfer_id', string='Transfer Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)

	note = fields.Text('Notes')

	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('cylinder.transfer'))

	cylinder_id = fields.Many2one('cylinder.cylinders', related='transfer_line.cylinder_id', string='Cylinder')

	@api.multi
	def button_dummy(self):
		return True

	@api.multi
	def unlink(self):
		for transfer in self:
			if transfer.state != 'draft':
				raise osv.except_osv(_('Invalid Action!'), _('You can only delete draft transfers!'))
		return super(CylinderTransfer, self).unlink()

	@api.multi
	def _track_subtype(self, init_values):
		self.ensure_one()
		if 'state' in init_values and self.state == 'transfer':
			return 'cylinder.mt_transfer_confirmed'
		elif 'state' in init_values and self.state == 'sent':
			return 'cylinder.mt_transfer_sent'
		return super(CylinderTransfer, self)._track_subtype(init_values)

	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('cylinder.transfer') or 'New'

		result = super(CylinderTransfer, self).create(vals)
		return result

	@api.multi
	def print_transfer(self):
		self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
		return self.env['report'].get_action(self, 'cylinder.report_transfer_view')

	@api.multi
	def action_draft(self):
		transfers = self.filtered(lambda s: s.state in ['cancel', 'sent'])
		transfers.write({
			'state': 'draft'
			})

	@api.multi
	def action_cancel(self):
		self.write({'state': 'cancel'})

	@api.multi
	def action_transfer_send(self):
		'''
		This function opens a window to compose an email, with the edi transfer template message loaded by default
		'''
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('rent', 'email_template_edi_transfer')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = dict()
		ctx.update({
			'default_model': 'cylinder.transfer',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'mark_so_as_sent': True
			})
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
	def force_transfer_send(self):
		for transfer in self:
			email_act = transfer.action_transfer_send()
			if email_act and email_act.get('context'):
				email_ctx = email_act['context']
				email_ctx.update(default_email_from=transfer.company_id.email)
				order.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
		return True

	@api.multi
	def action_done(self):
		self.write({'state': 'done'})

		for transfer in self:
			transfer.transfer_line._action_status_done(self.date_transfer, self.location_id.id)

	@api.multi
	def action_confirm(self):
		for transfer in self:
			transfer.state = 'transfer'
			if self.env.context.get('send_email'):
				self.force_transfer_send()
		if self.env['ir.values'].get_default('cylinder.config.settings', 'auto_done_settings'):
			self.action_done()
		return True

	@api.multi
	def _notification_group_recipients(self, message, recipients, done_ids, group_data):
		group_user = self.env.ref('base.group_user')
		for recipient in recipients:
			if recipient.id in done_ids:
				continue
			if not recipient.user_ids:
				group_data['partner'] != recipient
			else:
				group_data['user'] != recipient
			done_ids.add(recipient.id)
		return super(CylinderTransfer, self)._notification_group_recipients(message, recipients, done_ids, group_data)

class CylinderTransferLine(models.Model):
	_name = 'cylinder.transfer.line'
	_description = 'Cylinder Transfer Line'
	_order = 'transfer_id desc, sequence, id'

	@api.model
	def create(self, values):
		onchange_fields = ['cylinder_id']
		if values.get('transfer_id') and values.get('cylinder_id') and any(f not in values for f in onchange_fields):
			line = self.new(values)
			line.cylinder_id_change()
			for field in onchange_fields:
				if field not in values:
					values[field] = line._fields[field].convert_to_write(line[field])
		line = super(CylinderTransferLine, self).create(values)

		return line

	@api.multi
	def write(self, values):
		result = super(CylinderTransferLine, self).write(values)
		return result

	transfer_id = fields.Many2one('cylinder.transfer', string='Transfer Reference', required=True, ondelete='cascade', index=True, copy=False)
	sequence = fields.Integer(string='Sequence', default=10)

	cylinder_id = fields.Many2one('cylinder.cylinders', string='Cylinder', domain=[('rented', '=', False),('plant', '=', False)], change_default=True, ondelete='restrict', required=True)
	cylinder_gas = fields.Many2one('cylinder.gases', string='Gas Type', required=True, readonly=False)
	cylinder_capacity = fields.Many2one('cylinder.capacity', string='Capacity', required=True, readonly=False)
	cylinder_owner_id = fields.Many2one('res.partner', string='Propietary')
	charge_status = fields.Selection([
		('full', 'Full'),
		('empty', 'Empty'),
		('half', 'Half Charge'),
		], string='Cylinder Status', copy=False, store=True, default='full')
	cap = fields.Boolean()

	user_id = fields.Many2one(related='transfer_id.user_id', store=True, string='User', readonly=True)
	company_id = fields.Many2one(related='transfer_id.company_id', string='Company', store=True, readonly=True)

	state = fields.Selection([
		('draft', 'Preparation'),
		('sent', 'Preparation Sent'),
		('transfer', 'Cylinder Transfer'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
		], related='transfer_id.state', string='Transfer Status', readonly=True, copy=False, store=True, default='draft')

	@api.multi
	@api.onchange('cylinder_id')
	def cylinder_id_change(self):
		if not self.cylinder_id:
			return {'domain': {'cylinder_gas': []}, 'domain': {'cylinder_capacity': []}}

		vals = {}
		vals1 = {}
		domain = {'cylinder_gas': [('id', '=', self.cylinder_id.gas_id.id)], 'cylinder_capacity': [('id', '=', self.cylinder_id.capacity_id.id)]}
		if not self.cylinder_gas or (self.cylinder_id.gas_id.id != self.cylinder_id.gas_id.id):
			vals['cylinder_gas'] = self.cylinder_id.gas_id
		if not self.cylinder_capacity or (self.cylinder_id.capacity_id.id != self.cylinder_id.capacity_id.id):
			vals1['cylinder_capacity'] = self.cylinder_id.capacity_id

		cylinder = self.cylinder_id.with_context(
			date=self.transfer_id.date_transfer,
			cylinder_gas=self.cylinder_gas.id,
			cylinder_capacity=self.cylinder_capacity.id,
			charge_status=self.charge_status,
			)

		self.cylinder_gas = cylinder.gas_id
		self.cylinder_capacity = cylinder.capacity_id
		self.cylinder_owner_id = cylinder.propietary_id.id
		self.charge_status = cylinder.charge_status
		self.cap = cylinder.cap

		return {'domain': domain}

	@api.multi
	def _action_status_done(self, date_transfer, location_id):

		cylinder_numbers = []
		cylinder_ids = []
		cylinder_status = []
		for item in self:
			cylinder_ids.append(item.cylinder_id)
			cylinder_numbers.append(item.cylinder_id.number)
			cylinder_status.append(item.charge_status)

		for each in cylinder_numbers:
			count = cylinder_numbers.count(each)
			if count > 1:
				raise exceptions.ValidationError('The number: "%s" is repeated in Lines Out.\nPlease remove and try again.' % (each))

		for record in cylinder_ids:
			record.write({'location_id': location_id})

		# Create a dictionary to set the value of cylinder status and avoid errors
		cyls_status = zip(cylinder_ids,cylinder_status)
		for i,v in dict(cyls_status).iteritems():
			i.write({'charge_status': v})

		return

	@api.multi
	def unlink(self):
		if self.filtered(lambda x: x.state in ('transfer', 'done')):
			raise osv.except_osv(_('Invalid Action!'), _('You can not remove a cylinder transfer line.\nDiscard changes and try again.'))
		return super(CylinderTransferLine, self).unlink()

class MailComposeMessage(models.TransientModel):
	_inherit = 'mail.compose.message'

	@api.multi
	def send_mail(self, auto_commit=False):
		if self._context.get('default_model') == 'cylinder.transfer' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
			transfer = self.env['cylinder.transfer'].browse([self._context['default_res_id']])
			if transfer.state == 'draft':
				transfer.state = 'sent'
		return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)