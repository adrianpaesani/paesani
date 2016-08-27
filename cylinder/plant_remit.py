# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
from datetime import timedelta
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class res_company(models.Model):
	_inherit = "res.company"
	plant_remit_note = fields.Text(string='Default Terms and Conditions', translate=True)

class CylinderPlantRemit(models.Model):
	_name = "cylinder.plant_remit"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Cylinder Plant Remit"
	_order = 'date_remit desc, id desc'


	name = fields.Char(string='Plant Remit Reference', required = True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
	provider_remit_ref = fields.Char(string='Provider Reference', copy=False)

	state = fields.Selection([
		('draft', 'Preparation'),
		('sent', 'Preparation Send'),
		('remit', 'Cylinder Plant Remit'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	date_remit = fields.Date(string='Remit Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Date.today)
	create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which remit is created.")

	user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	partner_id = fields.Many2one('res.partner', string='Provider', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')
	partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current remit.")

	plant_remit_line_out = fields.One2many('cylinder.plant_remit.line_out', 'remit_id', string='Plant Remit Lines Out', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
	plant_remit_line_in = fields.One2many('cylinder.plant_remit.line_in', 'remit_id', string='Plant Remit Lines In', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)

	note = fields.Text('Notes')

	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('cylinders.plant_remit'))

	cylinder_out_id = fields.Many2one('cylinder.cylinders', related='plant_remit_line_out.cylinder_id', string='Cylinder Out')
	cylinder_in_id = fields.Many2one('cylinder.cylinders', related='plant_remit_line_in.cylinder_id', string='Cylinder In')

	@api.multi
	def button_dummy(self):
		return True

	@api.multi
	def unlink(self):
		for remit in self:
			if remit.state != 'draft':
				raise osv.except_osv(_('Invalid Action!'), _('You can only delete draft remits!'))
		return super(CylinderPlantRemit, self).unlink()

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
		# Makes sure 'partner_shipping_id' is defined
		if any(f not in vals for f in ['partner_shipping_id']):
			partner = self.env['res.partner'].browse(vals.get('partner_id'))
			addr = partner.address_get(['delivery'])
			vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
		result = super(CylinderPlantRemit, self).create(vals)
		return result

	@api.multi
	def print_remit(self):
		self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
		return self.env['report'].get_action(self, 'cylinder.report_plant_remit_view')

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
	def action_done(self):
		self.write({'state': 'done'})

		for remit in self:
			remit.plant_remit_line_out._action_status_done(self.date_remit, self.partner_id.id, self.name)
			remit.plant_remit_line_in._action_status_done(self.date_remit, self.partner_id.id, self.name)

	@api.multi
	def action_confirm(self):
		for remit in self:
			remit.state = 'remit'
			if self.env.context.get('send_email'):
				self.force_remit_send()
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
		return super(CylinderPlantRemit, self)._notification_group_recipients(message, recipients, done_ids, group_data)

class CylinderPlantRemitLineOut(models.Model):
	_name = 'cylinder.plant_remit.line_out'
	_description = 'Cylinder Plant Remit Line Out'
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
		line = super(CylinderPlantRemitLineOut, self).create(values)

		return line

	@api.multi
	def write(self, values):
		result = super(CylinderPlantRemitLineOut, self).write(values)
		return result

	remit_id = fields.Many2one('cylinder.plant_remit', string='Plant Remit Reference', required=True, ondelete='cascade', index=True, copy=False)
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
	def _action_status_done(self, date_remit, partner_id, name):

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
			record.write({'plant': True})
			record.write({'plant_send_date': date_remit})
			record.write({'send_control_number': name})

		return

	@api.multi
	def unlink(self):
		if self.filtered(lambda x: x.state in ('rent', 'done')):
			raise osv.except_osv(_('Invalid Action!'), _('You can not remove a cylinder remit line.\nDiscard changes and try again.'))
		return super(CylinderPlantRemitLineOut, self).unlink()

class CylinderPlantRemitLineIn(models.Model):
	_name = 'cylinder.plant_remit.line_in'
	_description = 'Cylinder Plant Remit Line In'
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
		line = super(CylinderPlantRemitLineIn, self).create(values)

		return line

	@api.multi
	def write(self, values):
		result = super(CylinderPlantRemitLineIn, self).write(values)
		return result

	remit_id = fields.Many2one('cylinder.plant_remit', string='Plant Remit Reference', required=True, ondelete='cascade', index=True, copy=False)
	sequence = fields.Integer(string='Sequence', default=10)

	cylinder_id = fields.Many2one('cylinder.cylinders', string='Cylinder', domain=[('rented', '=', False),('plant', '=', True)], change_default=True, ondelete='restrict', required=True)
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
	def _action_status_done(self, date_remit, partner_id, name):

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
			record.write({'plant': False})
			record.write({'plant_arrival_date': date_remit})
			record.write({'arrival_control_number': name})

		return

	@api.multi
	def unlink(self):
		if self.filtered(lambda x: x.state in ('rent', 'done')):
			raise osv.except_osv(_('Invalid Action!'), _('You can not remove a cylinder remit line.\nDiscard changes and try again.'))
		return super(CylinderPlantRemitLineIn, self).unlink()

class MailComposeMessagePlantRemit(models.TransientModel):
	_inherit = 'mail.compose.message'

	@api.multi
	def send_mail(self, auto_commit=False):
		if self._context.get('default_model') == 'cylinder.plant_remit' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
			remit = self.env['cylinder.plant_remit'].browse([self._context['default_res_id']])
			if remit.state == 'draft':
				remit.state = 'sent'
		return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)

class CylinderPlantCylinder(models.Model):
	_inherit = 'cylinder.cylinders'

	@api.multi
	def _plant_count_lines_out(self):
		self.plant_count_out = len(self.env["cylinder.plant_remit.line_out"].search(
			[("cylinder_id", "=", [self.id])]))

	@api.multi
	def _plant_count_lines_in(self):
		self.plant_count_in = len(self.env["cylinder.plant_remit.line_in"].search(
			[("cylinder_id", "=", [self.id])]))

	@api.multi
	def _remit_count_lines_out(self):
		self.remit_count_out = len(self.env["cylinder.remit.line_out"].search(
			[("cylinder_id", "=", [self.id])]))

	@api.multi
	def _remit_count_lines_in(self):
		self.remit_count_in = len(self.env["cylinder.remit.line_in"].search(
			[("cylinder_id", "=", [self.id])]))

	plant_count_out = fields.Integer(compute="_plant_count_lines_out", string="# Out to Plant Movements")
	plant_count_in = fields.Integer(compute="_plant_count_lines_in", string="# In from Plant Movements")
	remit_count_out = fields.Integer(compute="_remit_count_lines_out", string="# Out to Client Movements")
	remit_count_in = fields.Integer(compute="_remit_count_lines_in", string="# In from Client Movements")


# class Partner(models.Model):
#     _name = _inherit = "res.partner"

#     @api.one
#     @api.depends("contract_ids")
#     def _project_count(self):
#         self.project_count = len(self.env["project.project"].search(
#             [("analytic_account_id",
#               "in",
#               [c.id for c in self.contract_ids])]))

#     project_count = fields.Integer(compute="_project_count")


    # @api.multi
    # def _plant_count(self):
    #   r = {}
    #   domain = [
    #       ('active', '=', True),
    #   ]
    #   # for group in self.env['cylinder.report'].read_group(domain, ['cylinder_id'], ['cylinder_id']):
    #   #   r[group['cylinder_id'][0]] = group['cylinder_gas']
    #   for cylinder in self:
    #       cylinder.plant_count = r.get(cylinder.id, 0)


    # plant_count = fields.Integer(compute='_plant_count', string='# Plant Movements')