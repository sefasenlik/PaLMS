from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Committee(models.Model):
    _name = "student.committee"
    _description = "PaLMS - Committees"

	# Assigns the faculty of the manager creating this committee
    def _default_faculty(self):
        manager = self.env['student.manager'].sudo().search([('manager_account.id', '=', self.env.uid)], limit=1)
        if manager:
            return manager.manager_faculty 
        else: 
            raise ValidationError("Manager account could not be found. Please contact the system administrator.")

    committee_number = fields.Integer(string='Committe Number', default=lambda self: len(self.env['student.committee'].sudo().search([]))+1, readonly=True)
    committee_faculty = fields.Many2one('student.faculty', default=_default_faculty, string='Faculty', required=True)
    name = fields.Char('Committee Name', compute="_compute_committee_name", store=True)
    defense_ids = fields.One2many('student.defense', 'committee_id', string='Defenses', required=True)
    professor_ids = fields.Many2many('student.professor', string='Professors', required=True)

    @api.depends('committee_faculty')
    def _compute_committee_name(self):
        self.name = self.committee_faculty.name + " - Committee №" + str(self.committee_number)

    meeting_type = fields.Selection([('online', 'Online'), ('offline', 'Offline')], string="Meeting Type", default='online', required=True)
    meeting_location = fields.Char('Meeting Location')
    meeting_link = fields.Char('Meeting Link')
    meeting_date = fields.Date('Meeting Date', required=True)
    meeting_other_details = fields.Text('Other Details')

class CommitteeDefense(models.Model):
    _name = "student.defense"
    _description = "PaLMS - Committee Defenses"

    committee_id = fields.Many2one('student.committee', string='Committee', required=True)
    project_student = fields.Many2one('student.student', string='Defending Student', compute="_compute_project_student", store=True)
    project_id = fields.Many2one('student.project', string='Defense Project', required=True)
    defense_time = fields.Datetime(string='Defense Presentation Time', required=True)

    @api.depends('project_id')
    def _compute_project_student(self):
        if self.project_id:
            if self.project_id.student_elected:
                self.project_student = self.project_id.student_elected
            else:
                raise ValidationError("The chosen project is not assigned to a student.")