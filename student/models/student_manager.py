from odoo import api, fields, models

class Manager(models.Model):
    _name = "student.manager"
    _description = "PaLMS - Managers"

    name = fields.Char('Manager Name', required=True, default=lambda self: self.env.user.name, compute="_compute_name", store=True, readonly=True)
    active = fields.Boolean(default=True)

    program_ids = fields.One2many('student.program', 'manager', string='Managed Programs', readonly=True)

    manager_account = fields.Many2one('res.users', string='User Account', default=lambda self: self.env.user, required=True)
    manager_faculty = fields.Many2one('student.faculty', string='Faculty', required=True)

    @api.depends("manager_account")
    def _compute_name(self):
        self.name = self.manager_account.name

    @api.onchange("manager_account")
    def _set_manager_faculty(self):
        self.manager_account.faculty = self.manager_faculty