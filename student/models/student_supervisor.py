from odoo import api, fields, models
from datetime import datetime, timedelta


class Supervisor(models.Model):
    _name = "student.supervisor"
    _description = "PaLMS - Supervisors"

    name = fields.Char('Supervisor Name', required=True, default=lambda self: self.env.user.name, compute="_compute_name", store=True, readonly=True)
    active = fields.Boolean(default=True)

    program_ids = fields.One2many('student.program', 'supervisor', string='Supervised Programs', readonly=True)

    supervisor_account = fields.Many2one('res.users', string='User Account', default=lambda self: self.env.user, required=True)
    supervisor_faculty = fields.Many2one('student.faculty', string='Faculty', required=True)

    @api.depends("supervisor_account")
    def _compute_name(self):
        self.name = self.supervisor_account.name

    @api.onchange("supervisor_account")
    def _set_supervisor_faculty(self):
        self.supervisor_account.faculty = self.supervisor_faculty
