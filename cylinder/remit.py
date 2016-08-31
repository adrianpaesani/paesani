# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
from datetime import timedelta
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class res_company(models.Model):
	_inherit = "res.company"
	remit_note = fields.Text(string='Default Terms and Conditions', translate=True)

class CylinderRemit(models.Model):
	_name = "cylinder.remit"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Cylinder Remit"
	_order = 'date_remit desc, id desc'


	name = fields.Char(string='Remit Reference', required = True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
	client_remit_ref = fields.Char(string='Customer Reference', copy=False)

	state = fields.Selection([
		('draft', 'Preparation'),
		('sent', 'Preparation Send'),
		('remit', 'Cylinder Remit'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	date_remit = fields.Date(string='Remit Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Date.today)
	create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which remit is created.")

	user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')
	partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current remit.")

	remit_line_out = fields.One2many('cylinder.remit.line_out', 'remit_id', string='Remit Lines Out', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
	remit_line_in = fields.One2many('cylinder.remit.line_in', 'remit_id', string='Remit Lines In', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)

	note = fields.Text('Notes')

	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('cylinder.remit'))

	cylinder_out_id = fields.Many2one('cylinder.cylinders', related='remit_line_out.cylinder_id', string='Cylinder Out')
	cylinder_in_id = fields.Many2one('cylinder.cylinders', related='remit_line_in.cylinder_id', string='Cylinder In')

	@api.multi
	def button_dummy(self):
		return True

	@api.multi
	def unlink(self):
		for remit in self:
			if remit.state != 'draft':
				raise osv.except_osv(_('Invalid Action!'), _('You can only delete draft remits!'))
		return super(CylinderRemit, self).unlink()

	@api.multi
	def _track_subtype(self, init_values):
		self.ensure_one()
		if 'state' in init_values and self.state == 'remit':
			return 'cylinder.mt_remit_confirmed'
		elif 'state' in init_values and self.state == 'sent':
			return 'cylinder.mt_remit_sent'
		return super(CylinderRemit, self)._track_subtype(init_values)

	@api.multi
	@api.onchange('partner_id')
	def onchange_partner_id(self):
		"""
		Update the following fields when the partner is changed:
		- Delivery address
		"""
		if not self.partner_id:
			self.update({
				'partner_shipping_id': False,
				})
			return

		addr = self.partner_id.address_get(['delivery'])
		values = {
			'partner_shipping_id': addr['delivery'],
		}

		if self.partner_id.user_id:
			values['user_id'] = self.partner_id.user_id.id
		self.update(values)

	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('cylinder.remit') or 'New'

		# Makes sure 'partner_shipping_id' is defined
		if any(f not in vals for f in ['partner_shipping_id']):
			partner = self.env['res.partner'].browse(vals.get('partner_id'))
			addr = partner.address_get(['delivery'])
			vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
		result = super(CylinderRemit, self).create(vals)
		return result

	@api.multi
	def print_remit(self):
		self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
		return self.env['report'].get_action(self, 'cylinder.report_remit_view')

	@api.multi
	def action_draft(self):
		remits = self.filtered(lambda s: s.state in ['cancel', 'sent'])
		remits.write({
			'state': 'draft'
			})

	@api.multi
	def action_cancel(self):
		self.write({'state': 'cancel'})

	@api.multi
	def action_remit_send(self):
		'''
		This function opens a window to compose an email, with the edi remit template message loaded by default
		'''
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('rent', 'email_template_edi_rent')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = dict()
		ctx.update({
			'default_model': 'cylinder.remit',
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
	def force_remit_send(self):
		for remit in self:
			email_act = remit.action_remit_send()
			if email_act and email_act.get('context'):
				email_ctx = email_act['context']
				email_ctx.update(default_email_from=remit.company_id.email)
				order.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
		return True

	@api.multi
	def action_done(self):
		self.write({'state': 'done'})

		for remit in self:
			remit.remit_line_out._action_status_done(self.date_remit, self.partner_id.id)
			remit.remit_line_in._action_status_done(self.date_remit, self.partner_id.id)

	@api.multi
	def action_confirm(self):
		for remit in self:
			remit.state = 'remit'
			if self.env.context.get('send_email'):
				self.force_remit_send()
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
		return super(CylinderRemit, self)._notification_group_recipients(message, recipients, done_ids, group_data)

class CylinderRemitLineOut(models.Model):
	_name = 'cylinder.remit.line_out'
	_description = 'Cylinder Remit Line Out'
	_order = 'remit_id desc, sequence, id'

	@api.model
	def create(self, values):
		onchange_fields = ['cylinder_id']
		if values.get('remit_id') and values.get('cylinder_id') and any(f not in values for f in onchange_fields):
			line = self.new(values)
			line.cylinder_id_change()
			for field in onchange_fields:
				if field not in values:
					values[field] = line._fields[field].convert_to_write(line[field])
		line = super(CylinderRemitLineOut, self).create(values)

		return line

	@api.multi
	def write(self, values):
		result = super(CylinderRemitLineOut, self).write(values)
		return result

	remit_id = fields.Many2one('cylinder.remit', string='Remit Reference', required=True, ondelete='cascade', index=True, copy=False)
	sequence = fields.Integer(string='Sequence', default=10)

	cylinder_id = fields.Many2one('cylinder.cylinders', string='Cylinder', domain=[('rented', '=', False),('plant', '=', False)], change_default=True, ondelete='restrict', required=True)
	cylinder_gas = fields.Many2one('cylinder.gases', string='Gas Type', required=True, readonly=False)
	cylinder_capacity = fields.Many2one('cylinder.capacity', string='Capacity', required=True, readonly=False)
	cylinder_owner_id = fields.Many2one('res.partner', string='Propietary')
	cap = fields.Boolean()

	user_id = fields.Many2one(related='remit_id.user_id', store=True, string='User', readonly=True)
	company_id = fields.Many2one(related='remit_id.company_id', string='Company', store=True, readonly=True)
	remit_partner_id = fields.Many2one(related='remit_id.partner_id', store=True, string='Customer')

	state = fields.Selection([
		('draft', 'Preparation'),
		('sent', 'Preparation Sent'),
		('rent', 'Cylinder Remit'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
		], related='remit_id.state', string='Remit Status', readonly=True, copy=False, store=True, default='draft')

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
			partner=self.remit_id.partner_id.id,
			date=self.remit_id.date_remit,
			cylinder_gas=self.cylinder_gas.id,
			cylinder_capacity=self.cylinder_capacity.id,
			)

		self.cylinder_gas = cylinder.gas_id
		self.cylinder_capacity = cylinder.capacity_id
		self.cylinder_owner_id = cylinder.propietary_id.id
		self.cap = cylinder.cap

		return {'domain': domain}

	@api.multi
	def _action_status_done(self, date_remit, partner_id):

		cylinder_numbers = []
		cylinder_ids = []
		for item in self:
			cylinder_ids.append(item.cylinder_id)
			cylinder_numbers.append(item.cylinder_id.number)

		for each in cylinder_numbers:
			count = cylinder_numbers.count(each)
			if count > 1:
				raise exceptions.ValidationError('The number: "%s" is repeated in Lines Out.\nPlease remove and try again.' % (each))

		for record in cylinder_ids:
			record.write({'rented': True})
			record.write({'last_rental_date': date_remit})
			record.write({'partner_id': partner_id})

		return

	@api.multi
	def unlink(self):
		if self.filtered(lambda x: x.state in ('rent', 'done')):
			raise osv.except_osv(_('Invalid Action!'), _('You can not remove a cylinder remit line.\nDiscard changes and try again.'))
		return super(CylinderRemitLineOut, self).unlink()

class CylinderRemitLineIn(models.Model):
	_name = 'cylinder.remit.line_in'
	_description = 'Cylinder Remit Line in'
	_order = 'remit_id desc, sequence, id'

	@api.model
	def create(self, values):
		onchange_fields = ['cylinder_id']
		if values.get('remit_id') and values.get('cylinder_id') and any(f not in values for f in onchange_fields):
			line = self.new(values)
			line.cylinder_id_change()
			for field in onchange_fields:
				if field not in values:
					values[field] = line._fields[field].convert_to_write(line[field])
		line = super(CylinderRemitLineIn, self).create(values)

		return line

	@api.multi
	def write(self, values):
		result = super(CylinderRemitLineIn, self).write(values)
		return result

	remit_id = fields.Many2one('cylinder.remit', string='Remit Reference', required=True, ondelete='cascade', index=True, copy=False)
	sequence = fields.Integer(string='Sequence', default=10)

	cylinder_id = fields.Many2one('cylinder.cylinders', string='Cylinder', domain=[('rented', '=', True), ('plant', '=', False)], change_default=True, ondelete='restrict', required=True)
	cylinder_gas = fields.Many2one('cylinder.gases', string='Gas Type', required=True, readonly=False)
	cylinder_capacity = fields.Many2one('cylinder.capacity', string='Capacity', required=True, readonly=False)
	cylinder_owner_id = fields.Many2one('res.partner', string='Propietary')
	cap = fields.Boolean()

	user_id = fields.Many2one(related='remit_id.user_id', store=True, string='User', readonly=True)
	company_id = fields.Many2one(related='remit_id.company_id', string='Company', store=True, readonly=True)
	remit_partner_id = fields.Many2one(related='remit_id.partner_id', store=True, string='Customer')

	state = fields.Selection([
		('draft', 'Preparation'),
		('sent', 'Preparation Sent'),
		('rent', 'Cylinder Remit'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
		], related='remit_id.state', string='Remit Status', readonly=True, copy=False, store=True, default='draft')

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
			partner=self.remit_id.partner_id.id,
			date=self.remit_id.date_remit,
			cylinder_gas=self.cylinder_gas.id,
			cylinder_capacity=self.cylinder_capacity.id,
			)

		self.cylinder_gas = cylinder.gas_id
		self.cylinder_capacity = cylinder.capacity_id
		self.cylinder_owner_id = cylinder.propietary_id.id
		self.cap = cylinder.cap

		return {'domain': domain}

	@api.multi
	def _action_status_done(self, date_remit, partner_id):

		cylinder_numbers = []
		cylinder_ids = []
		for item in self:
			cylinder_ids.append(item.cylinder_id)
			cylinder_numbers.append(item.cylinder_id.number)

		for each in cylinder_numbers:
			count = cylinder_numbers.count(each)
			if count > 1:
				raise exceptions.ValidationError('The number: "%s" is repeated in Lines In.\nPlease remove and try again.' % (each))

		for record in cylinder_ids:
			record.write({'rented': False})
			record.write({'last_rental_date': None})
			record.write({'last_return_date': date_remit})
			record.write({'last_rent_partner_id': partner_id})

		return

	@api.multi
	def unlink(self):
		if self.filtered(lambda x: x.state in ('rent', 'done')):
			raise osv.except_osv(_('Invalid Action!'), _('You can not remove a cylinder remit line.\nDiscard changes and try again.'))
		return super(CylinderRemitLineIn, self).unlink()

class MailComposeMessage(models.TransientModel):
	_inherit = 'mail.compose.message'

	@api.multi
	def send_mail(self, auto_commit=False):
		if self._context.get('default_model') == 'cylinder.remit' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
			remit = self.env['cylinder.remit'].browse([self._context['default_res_id']])
			if remit.state == 'draft':
				remit.state = 'sent'
		return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)