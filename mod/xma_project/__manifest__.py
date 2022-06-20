# -*- coding: utf-8 -*-
{
    'name': "Xmarts Project",

    'summary': """
        Adaptación del módulo de Proyectos en cuanto a Resumen de proyecto y Cobranza""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Xmarts",
    'website': "http://www.xmarts.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'crm',
        'mail', 
        'sale_subscription', 
        'project',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_subscription_view.xml',
        'views/xmarts_subscription_view.xml',
        'views/xmarts_server_view.xml',
        'views/project_inherit_view.xml',
        'views/project_task.xml',
        'reports/report.xml',
    ],
}