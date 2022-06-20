# -*- coding: utf-8 -*-

{   'name': 'WhatsApp Website',
    'version': '13.0',
    'author': "David Montero Crespo",
    'description': """
        Chat with your customers through WhatsApp, the most popular messaging app. Vital extension for your odoo website """,
    'category': 'website',
    'website': "https://softwareescarlata.com/",
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_floating_wsp_views.xml',
        'views/templates.xml',
        'data/website_floating_wsp_data.xml'
    ],

    'assets': {
        'web.assets_frontend': [
            'website_mail/static/src/js/follow.js',
            'website_mail/static/src/css/website_mail.scss',
        ],
    },
    'images': ['static/description/4.jpg'],
    'currency': 'EUR',
    'price': 10,
    'license': 'AGPL-3',

}