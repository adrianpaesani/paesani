from odoo import api, fields, models, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

# Gas Type
class PackageGas(models.Model):
    _name = 'crio.package.gas'
    _order = 'name desc, id desc'

    name = fields.Char('Name', required=True)
    formula = fields.Char('Gas Formula')
    description = fields.Text('Extended Description')

    package_ids = fields.Many2many('crio.package.capacity', 'crio_package_capacity_rel', 'package_capacity_id',
                                   'capacity_id', 'Capacity',
                                   copy=False)

    # package_ids = fields.One2many('crio.package.capacity', 'id', 'Capacity', copy=True)
    type_ids = fields.One2many('crio.package.type', 'id', 'Type', copy=True)

    un_safety_data_sheet = fields.Binary('UN Safety Datasheet')
    un_safety_data_sheet_fn = fields.Char('Filename')

# Package Type
class PackageType(models.Model):
    _name = 'crio.package.type'
    _order = 'name desc, id desc'

    name = fields.Char('Name', required=True)
    

# Package Capacity
class PackageCapacity(models.Model):
    _name = 'crio.package.capacity'
    _order = 'name desc, id desc'

    name = fields.Char('Name', required=True)

# Package Tags
class PackageTags(models.Model):
    _name = 'crio.package.tag'

    name = fields.Char(required=True)
    color = fields.Integer('Color Index', default=10)

    _sql_constraints = [('gas_tag_name_uniq', 'UNIQUE(name)', "Tag name already exists!")]

# Packages
class Package(models.Model):
    _name = 'crio.package'
    _rec_name = 'name'
    _order = 'gas_id desc, name desc, id desc'

    # Package info
    name = fields.Char('Package Number', required=True) # Listo
    barcode = fields.Char('Barcode', copy=False, help="International Article Number used for product identification.") # Listo
    propietary_id = fields.Many2one('res.partner', string='Propietary') # Listo
    details = fields.Text('Detailed Information') # Listo
    gas_id = fields.Many2one('crio.package.gas', string='Type of Gas', store=True) # Listo
    capacity_id = fields.Many2one('crio.package.capacity', string='Package Capacity', store=True) # Listo
    active = fields.Boolean('Active', default=True) # Field
    location = fields.Selection([
        ('plant', 'Plant'),
        ('warehouse', 'Warehouse'),
        ('client', 'Client'),
    ], string="Storage Location", copy=False, store=True, default='plant')
    charge_status = fields.Selection([
        ('full', 'Full'),
        ('half', 'Half'),
        ('empty', 'Empty'),
    ], string='Package Status', copy=False, store=True, default='empty') # Listo
    ht_date = fields.Date('Hidrostatic Test', help="Date of last Hidrostatic Test.") # Listo
    rental = fields.Boolean('Rental', default=True, help="Indicates if it's available for rental.") # Listo
    rented = fields.Boolean('Rented', default=False,help="Indicates if it's rented.") # Listo

    # Plant
    plant_date_arrival = fields.Date('Plant arrival date', help="Package date of arrival.") # Listo
    plant_date_send = fields.Date('Plant send date', help="Package date of send.") # Listo
    plant_order_number = fields.Char('Plant Order Number', help="Package order number.") # Listo

    # Warehouse
    warehouse_date_arrival = fields.Date('Warehouse arrival date', help="Package date of arrival.") # Listo
    warehouse_date_send = fields.Date('Warehouse send date', help="Package date of send.") # Listo
    warehouse_order_number = fields.Char('Warehouse Order Number', help="Package order number.") # Listo
    warehouse_location_id = fields.Many2one('stock.warehouse', 'Warehouse', store=False,
                                   search=lambda operator, operand, vals: []) # Listo

    # Partner
    partner_date_arrival = fields.Date('Client arrival date', help="Package date of arrival.") # Listo
    partner_date_send = fields.Date('Client send date', help="Package date of send.") # Listo
    partner_order_number = fields.Char('Client Order Number', help="Package order number.") # Listo
    partner_id = fields.Many2one('res.partner', string='Partner', help="Partner who rented the package.") # Listo
    partner_last_rental_id = fields.Many2one('res.partner', string='Last Partner Rental', help="Last partner who rented the package.") # Listo

    # Extra Fields
    days_rental = fields.Float(string='Rented Days', digits=(6,2), compute='_rental_days')
    days_plant = fields.Float(string='Plant Days', digits=(6,2), compute='_plant_days')

    # Storage Tags
    tags_ids = fields.Many2many('crio.package.tag', 'crio_package_tag_rel', 'package_tag_id', 'tag_id', 'Tags',
                                copy=False)

    # Warehouse
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', store=False,
                                            search=lambda operator, operand, vals: [])

    # Product
    product_id = fields.Many2one('product.product', 'Product', required=True,
                                 help="Product wich will be used for invoicing.")

    _sql_constraints = [
        ('gas_storage_name_unique',
         'UNIQUE(name)',
         "The number must be unique!.\This number already exists."),
    ]

    _sql_constraints = [
        ('gas_storage_barcode_unique',
         'UNIQUE(barcode)',
         "The Barcode must be unique!.\This barcode is already assigned."),
    ]

    @api.depends('partner_date_send')
    def _rental_days(self):
        for d in self:
            if not d.partner_date_send:
                d.days_rental = 0
            else:
                start = fields.Datetime.from_string(d.partner_date_send)
                end = fields.Datetime.from_string(fields.Date.today())
                d.days_rental = (end - start).days

    @api.depends('plant_date_arrival')
    def _plant_days(self):
        for d in self:
            if not d.plant_date_arrival:
                d.days_plant = 0
            else:
                start = fields.Datetime.from_string(d.plant_date_arrival)
                end = fields.Datetime.from_string(fields.Date.today())
                d.days_plant = (end - start).days

    @api.onchange('gas_id')
    def _onchange_gas_id(self):
        res = {}
        res['domain']={'capacity_id':[('capacity_id', '=', self.capacity_id.id)]}
        return res
        # if self.gas_id:
        #     return {
        #         'domain': {'capacity_ids': [('gas_id', '=', self.gas_id.id)]}
        #     }
        # else:
        #     return {
        #         {'domain': {'gas_id': []}}
        #     }