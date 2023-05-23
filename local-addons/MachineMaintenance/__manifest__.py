# -*- coding: utf-8 -*-
{
    "name": "Machine Maintenance Checksheet",
    "summary": """
        Hoya Machine Maintenance Module""",
    "description": """
        Long description of module's purpose
    """,
    "author": "My Company",
    "website": "http://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "maintenance", "calendar"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/check_sheet.xml",
        "views/machine.xml",
        "views/department.xml",
        "views/factory.xml",
        "views/machine_group.xml",
        "views/machine_calendar.xml",
        "views/menuitem.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
