# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": "Multi-Company Email - Multi Company Email",
    "summary": "This module allows the odoo users to Add individual email signature per company.",
    "version": "15.0.1",
    "description": """
        This module allows the odoo users to Add individual email signature per company.
        Multi Company Email.
        Email Multi Company.
        Email Signature per Company.
        Signature per Company.
        Email Signature.
        Signature per Company.
        Multiple Email Signature.
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/odoo_multi_company_email.png"],
    "category": "Extra Tools",
    "depends": [
        "base",
    ],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "/odoo_multi_company_email/static/src/js/menu.js"
        ],
        "web.assets_qweb": [         
               
        ]
    },
    "installable": True,
    "application": True,
    "price"                 :  20.00,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
}
