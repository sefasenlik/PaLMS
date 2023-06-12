from odoo import api, fields, models
from datetime import datetime, timedelta


class Professor(models.Model):
    _name = "student.professor"
    _description = "OpenLMS - Professors"

    name = fields.Char('Professor Name', required=True, default=lambda self: self.env.user.name, compute="_compute_name", store=True, readonly=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('online', 'Online'),('offline', 'Offline'),('on_vacation', 'On vacation')], default='online', string='State')
    last_seen = fields.Datetime("Last Seen", default=lambda self: fields.Datetime.now())
    visiting_professor = fields.Boolean('Visiting professor?', default=False)

    professor_account = fields.Many2one('res.users', string='User Account', default=lambda self: self.env.user, required=True)
    professor_faculty = fields.Many2one('student.faculty', string='Faculty', required=True)
    project_ids = fields.One2many('student.project', 'professor_id', string='Projects')

    @api.depends("professor_account")
    def _compute_name(self):
        self.name = self.professor_account.name

    # Computed Fields
    offered_projects = fields.Integer(string='Number of Offered Projects', compute='_compute_project_count', store=True, readonly=True)

    _sql_constraints = [
        ('check_offered_projects', 'CHECK(offered_projects >= 0)', 'The number of offered projects can\'t be negative.'),
    ]
    
    @api.depends('project_ids')
    @api.model
    def _compute_project_count(self):
        for professor in self:
            professor.offered_projects = len(professor.project_ids)

    def action_view_professor_projects(self):
        action = self.env.ref('student.action_project').read()[0]
        action['domain'] = [('professor_id', '=', self.id)]
        return action