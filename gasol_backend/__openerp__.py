# -*- coding: utf-8 -*-
# Copyright 2016 Openworx, LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Gasol Backend Theme",
    "summary": "Odoo 9.0 Community Backend Theme",
    "version": "9.0.1",
    "category": "Themes/Backend",
    "website": "http://www.gasolsrl.biz",
	"description": """
                Backend theme for Odoo 9.0 community edition.
                The app dashboard is based on the module web_responsive from LasLabs Inc
    """,
        'images':[
        'images/screen.png'
        ],
    "author": "Adrian Paesani",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web',
    ],
    "data": [
        'views/assets.xml',
        'views/web.xml',
    ],
    'qweb': [
        'static/src/xml/app_drawer_menu_search.xml',
        'static/src/xml/form_view.xml',
        'static/src/xml/navbar.xml',
    ],
}