# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Student Project',
    'version': '1.8',
    'category': 'Human Resources/Student',
    'sequence': 15,
    'summary': 'A test module to manage student projects',
    'website': 'https://github.com/sefasenlik/Course-Work',
    'installable': True,
    'auto_install': False,
    'application': True,
    'depends' : ['mail'],
    'data': [
        'data/student_groups.xml',
        'security/ir.model.access.csv',
        'views/student_professor_views.xml',
        'views/student_project_views.xml',
        'views/student_application_views.xml',
        'views/student_faculty_views.xml',
        'views/student_program_views.xml',
        'views/student_student_views.xml',
        'views/student_util_views.xml',
        'views/student_menus.xml'
    ],
    'license': 'LGPL-3'
}
