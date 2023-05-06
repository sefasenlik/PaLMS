from odoo import fields, models, api

class Faculty(models.Model):
    _name = "student.faculty"
    _description = "OpenLMS - Faculties"

    name = fields.Char('Faculty Name', required=True, translate=True)
    dean = fields.Many2one('res.users', string='Faculty Dean', required=True)
    manager = fields.Many2one('res.users', string='Faculty Manager', required=True)
    address = fields.Text('Address', required=True)
    city = fields.Selection([('msk', 'Moscow'),('spb', 'Saint-Petersburg'),('prm', 'Perm'),('mc', 'Minecraft')], default='msk', string='City', required=True)

    program_number = fields.Integer(string='Number of Programs', compute='_compute_program_count', store=True, readonly=True)
    program_ids = fields.One2many('student.program', 'program_faculty_id', string='Programs', readonly=True)

    @api.depends('program_ids')
    @api.model
    def _compute_program_count(self):
        self.program_number = len(self.program_ids)

    staff_number = fields.Integer(string='Number of Faculty Members', compute='_compute_staff_count', store=True, readonly=True)
    staff_ids = fields.One2many('student.professor', 'professor_faculty', string='Staff', readonly=True)

    @api.depends('staff_ids')
    @api.model
    def _compute_staff_count(self):
        self.staff_number = len(self.staff_ids)

    project_number = fields.Integer(string='Number of Projects', compute='_compute_project_count', store=True, readonly=True)
    project_ids = fields.Many2many('student.project', string='Faculty Projects', readonly=True)

    @api.depends('project_ids')
    @api.model
    def _compute_project_count(self):
        self.project_number = len(self.project_ids)