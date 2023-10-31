from odoo import fields, models, api

class Program(models.Model):
    _name = "student.program"
    _description = "PaLMS - Programs"

    name = fields.Char('Program Name', required=True, translate=True)
    degree = fields.Selection([('ba', "Bachelor's"),('ms', "Master's"),('phd', 'PhD')], default='ba', string='Program Degree', required=True)
    language = fields.Selection([('en', 'English'),('ru', 'Russian')], default='ru', string='Language', required=True)
    length = fields.Selection([('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),('6', '6')], default='4', string='Program Length', required=True)
    type = fields.Selection([('on','Online'),('off','Offline'),('hrd','Hybrid')], default='off', string='Mode of Education', required=True)
    program_faculty_id = fields.Many2one('student.faculty', string='Faculty', default=lambda self: self.env['student.faculty'].search([], limit=1), required=True, store=True)
    supervisor = fields.Many2one('student.supervisor', string='Academic Supervisor', required=True)
    manager = fields.Many2one('student.manager', string='Program Manager', required=True)
    
    student_number = fields.Integer(string='Number of Students', compute='_compute_student_count', store=True, readonly=True)
    student_ids = fields.One2many('student.student', 'student_program', string='Students')

    @api.depends('student_ids')
    @api.model
    def _compute_student_count(self):
        self.student_number = len(self.student_ids)

    project_number = fields.Integer(string='Number of Projects', compute='_compute_project_count', store=True, readonly=True)
    project_ids = fields.Many2many('student.project', string='Faculty Projects', domain=[('state','in',['approved','applied','assigned'])])

    @api.depends('project_ids')
    @api.model
    def _compute_project_count(self):
        self.project_number = len(self.project_ids)