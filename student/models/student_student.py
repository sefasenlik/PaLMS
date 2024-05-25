from odoo import fields, models, api
from odoo.exceptions import ValidationError
import datetime
from unidecode import unidecode

class Student(models.Model):
    _name = "student.student"
    _description = "PaLMS - Students"

    name = fields.Char('Student Name', default="N/A", compute="_get_from_account", store=True)
    student_id = fields.Char(string='Student ID', default="N/A", compute="_get_from_account", store=True)
    active = fields.Boolean(default=True)

    student_account = fields.Many2one('res.users', store=True, string='User Account', required=True)
    student_email = fields.Char("Email", default="N/A", compute="_get_from_account", store=True, required=True)
    student_phone = fields.Char("Phone")

    # ♥ Why can I not add 'required' attribute to computed fields?
    student_faculty = fields.Many2one('student.faculty', compute="_compute_faculty", store=True, string='Faculty')
    student_program = fields.Many2one('student.program', string='Enrolled Program', required=True)
    enrolled = fields.Char(string='Year of Enrollment', help='Enter year in yyyy format.')
    progress = fields.Selection([('prep', 'Preparatory Year'), 
                                 ('1', 'First Year'), 
                                 ('2', 'Second Year'), 
                                 ('3', 'Third Year'), 
                                 ('4', 'Fourth Year'), 
                                 ('5', 'Fifth Year'), 
                                 ('6', 'Sixth Year')], string="Progress", required=True)
    graduation = fields.Char("Expected Graduation Year", compute='_compute_graduation', store=False, readonly=True)
    current_project = fields.Many2one('student.project', string="Assigned Project")

    degree = fields.Many2one('student.degree', string='Student Academic Degree', compute="_compute_degree", store=True)

    @api.depends('student_program')
    def _compute_faculty(self):
        # Use id to correctly assign the value to Many2one field
        self.student_faculty = self.student_program.program_faculty_id.id

    @api.depends('student_program', 'progress')
    def _compute_degree(self):
        self.degree = self.env['student.degree'].sudo().search(['&',('year', '=', self.progress), ('level', '=', self.student_program.degree)], limit=1)

    @api.onchange('current_project')
    def _onchange_current_project(self):
        for application in self.application_ids:
            application.action_view_application_cancel()

    @api.onchange("student_account")
    def _set_student_faculty(self):
        self.student_account.faculty = self.student_faculty

    _sql_constraints = [
        ('check_uniqueness', 'UNIQUE(student_id, student_account)', 'This student is already registered.'),
        ('check_enrollment_max', 'CHECK(enrolled::int <= EXTRACT(YEAR FROM NOW())::int)', 'The enrollment date should not exceed the current year.'),
        ('check_enrollment_min', 'CHECK(enrolled::int >= 1992)', 'The enrollment date cannot be older than 1992.')
    ]

    @api.onchange('enrolled', 'student_program', 'progress')
    def _compute_graduation(self):
        if self.progress != 'prep' and int(self.progress) > int(self.student_program.length):    
            raise ValidationError("The student progress exceeds the program length, please input a correct value.")

        if self.progress == 'prep':
            self.graduation = str(datetime.date.today().year + int(self.student_program.length) + 1)
        else:
            self.graduation = str(datetime.date.today().year + int(self.student_program.length) - int(self.progress))

    @api.depends("student_account")
    def _get_from_account(self):
        self.student_email = self.student_account.login
        self.name = self.student_account.name
        self.student_id = unidecode(''.join([word[0].upper() for word in self.name.split()[:2]]) + str(self.student_account.id).zfill(4))

    application_number = fields.Integer(string='Number of Applications', compute='_compute_application_count', store=True, readonly=True)
    application_ids = fields.One2many('student.application', 'applicant', string='Applications of the Student', readonly=True)

    @api.depends('application_ids')
    def _compute_application_count(self):
        self.application_number = len(self.application_ids)

    proposal_number = fields.Integer(string='Number of Proposals', compute='_compute_proposal_count', store=True, readonly=True)
    proposal_ids = fields.One2many('student.proposal', 'proponent', string='Proposals of the Student', readonly=True)

    @api.depends('proposal_ids')
    def _compute_proposal_count(self):
        self.proposal_number = len(self.proposal_ids)