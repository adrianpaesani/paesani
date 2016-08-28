# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Cylinders',
    'version': '0.5',
    'author': 'Adrian Paesani',
    'category': 'Cylinder Management',
    'demo': [
        'demo.xml',
    ],
    'website': 'https://www.gasolsrl.biz',
    'depends': ['base','mail'],
    'description': """
This is the base module for managing cylinders logistic and rental in OpenERP.
===============================================================================

Cylinders support tracking by number, different types of gases, owner information.

    - Cylinder Information
    - Types of Gases
    - Capacities of Cylinders

    """,
    'data': [
        'security/ir.model.access.csv',
        'reports/remit.xml',
        'reports/plant_remit_report.xml',
        'reports/external_layout_extra.xml',
        'remit_sequence.xml',
        'views/cylinders.xml',
        'views/gases.xml',
        'views/capacity.xml',
        'views/plant_remit.xml',
        'views/cylinder_remit.xml',
        # 'data/mail_template_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
