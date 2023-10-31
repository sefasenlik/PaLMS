# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'PaLMS',
    'version': '0.3.6',
    'category': 'Human Resources/Student',
    'sequence': 15,
    'summary': 'A prototype ERP solution for handling course work submissions. Created by Sefa Şenlik - 2023',
    'website': 'https://github.com/sefasenlik/PaLMS',
    'installable': True,
    'auto_install': False,
    'application': True,
    'depends' : ['mail'],
    'data': [
        'data/student_groups.xml',
        'data/student_email_templates.xml',
        'data/student_regulations.xml',
        'security/ir.model.access.csv',
        'views/student_application_views.xml',
        'views/student_event_views.xml',
        'views/student_faculty_views.xml',
        'views/student_professor_views.xml',
        'views/student_program_views.xml',
        'views/student_project_views.xml',
        'views/student_proposal_views.xml',
        'views/student_student_views.xml',
        'views/student_supervisor_views.xml',
        'views/student_manager_views.xml',
        'views/student_util_views.xml',
        'views/student_menus.xml'
    ],
    'license': 'LGPL-3'
}
