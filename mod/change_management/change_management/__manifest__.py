# -*- coding: utf-8 -*-
{
    'name': "change_management",
    'summary': """ """,
    'description': """ """,
    'author': "Xmarts",
    'website': "http://www.xmarts.com",
    'category': 'Uncategorized',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['website',
                'base', 
                'project',
                'website_mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/change_request.xml',
        'views/arrears_request_view.xml',
        'views/change_request_type.xml',
        'views/project_inherit.xml',
        'data/sequence.xml',
        'report/report_arrears_management.xml',
        'report/report_change_management.xml',
        'data/mail_template.xml',
        'data/website_change_request_data.xml',
    ],
}
