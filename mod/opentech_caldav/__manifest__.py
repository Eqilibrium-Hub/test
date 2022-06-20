# -*- coding: utf-8 -*-
{
    'name': "CalDAV",

    'summary': """
        Calendar CalDAV protocol
        """,

    'description': """
        - Support only 1 database
        - Install Required module ics:
            - On Windows: c:\\\program files\\\odoo 12.0\\\python\\\> scripts\\\pip install ics
            - On GNU/Linux: sudo pip install ics
        - timezone must be established on user profile
        - Categories are not supported
        - VTODO is not supported only VEVENT
        - Only support send 1 alarm for event
        - Recurrent events must be modified on Odoo Web
        - Attendees are not supported
        - Tested on:
            - android (opensync)
            - evolution (url http[s]://odooaddress[:odooport]/caldav/calendar/[username])
            - outlook (caldavsyncronizer.org)
            - mac os X
            - ios
    """,

    'author': "Open Tech S.L.",
    'website': "https://www.opentech.es",
    'price': 100,
    'currency': 'EUR',
    'license': 'AGPL-3',
    'images': ['static/description/icon.png'],
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'calendar',
    ],

    # always loaded
    # 'data': [
    #     # 'security/ir.model.access.csv',
    #     'views/views.xml',
    #     'views/templates.xml',
    # ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
