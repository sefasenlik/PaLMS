from odoo import fields, models, api

class Faculty(models.Model):
    _name = "student.faculty"
    _description = "PaLMS - Faculties"

    name = fields.Char('Faculty Name', required=True, translate=True)
    dean = fields.Many2one('res.users', string='Faculty Dean', required=True)
    address = fields.Text('Address', required=True)
    campus = fields.Many2one('student.campus', string='Campus', default=lambda self: self.env['student.campus'].search([], limit=1), required=True)

    program_number = fields.Integer(string='Number of Programs', compute='_compute_program_count', store=True, readonly=True)
    program_ids = fields.One2many('student.program', 'program_faculty_id', string='Programs', readonly=True)

    @api.depends('program_ids')
    @api.model
    def _compute_program_count(self):
        self.program_number = len(self.program_ids)

    professor_number = fields.Integer(string='Number of Professors', compute='_compute_professor_count', store=True, readonly=True)
    professor_ids = fields.One2many('student.professor', 'professor_faculty', string='Professors', readonly=True)

    @api.depends('professor_ids')
    @api.model
    def _compute_professor_count(self):
        self.professor_number = len(self.professor_ids)

    manager_number = fields.Integer(string='Number of Managers', compute='_compute_manager_count', store=True, readonly=True)
    manager_ids = fields.One2many('student.manager', "manager_faculty", string='Program Managers', readonly=True)

    @api.depends('manager_ids')
    @api.model
    def _compute_manager_count(self):
        self.manager_number = len(self.manager_ids)

    supervisor_number = fields.Integer(string='Number of Supervisors', compute='_compute_supervisor_count', store=True, readonly=True)
    supervisor_ids = fields.One2many('student.supervisor', 'supervisor_faculty', string='Supervisors', readonly=True)

    @api.depends('supervisor_ids')
    @api.model
    def _compute_supervisor_count(self):
        self.supervisor_number = len(self.supervisor_ids)

    student_number = fields.Integer(string='Number of Students', compute='_compute_student_count', store=True, readonly=True)
    student_ids = fields.One2many('student.student', 'student_faculty', string='Students', readonly=True)

    @api.depends('student_ids')
    @api.model
    def _compute_student_count(self):
        self.student_number = len(self.student_ids)

    project_number = fields.Integer(string='Number of Projects', compute='_compute_project_count', store=True, readonly=True)
    project_ids = fields.Many2many('student.project', string='Faculty Projects', readonly=True, domain=[('state_publication','!=','ineligible')])

    @api.depends('project_ids')
    @api.model
    def _compute_project_count(self):
        self.project_number = len(self.project_ids)