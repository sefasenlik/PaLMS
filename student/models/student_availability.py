from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError

class ProjectAvailability(models.Model):
    _name = 'student.availability'
    _description = 'PaLMS - Project Availability'

    state = fields.Selection([('waiting', 'Waiting for submission'),
                              ('pending', 'Pending'), 
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('returned','Returned')], group_expand='_expand_state_groups', default='waiting', string='State')
    type = fields.Selection([('cw', 'Course Work (Курсовая работа)'), ('fqw', 'Final Qualifying Work (ВКР)'), ('both', 'Both (КР/ВКР)')], string="Type", required=True)

    @api.depends_context('project_id')
    def _compute_access(self):
        self.access_from_project = bool(self._context.get('project_id', False))
    
    access_from_project = fields.Boolean('Used to hide project details when accessed from the project itself (TECHNICAL)', default=True, compute=_compute_access, store=False)    

    def _set_default_project(self):
        return self._context.get('project_id', False)

    project_id = fields.Many2one('student.project', string='Project', default=_set_default_project)

    # ♥ Might be better to implement a view-based approach (e.g. iframes, <form>, etc.) to not duplicate the values below.
    @api.depends('project_id')
    def _set_default_project_values(self):
        project_source = self.env['student.project'].sudo().search([('id', '=', self._context.get('project_id', False))], limit=1) if self._context.get('project_id', False) else self.project_id
        
        if project_source:
            self.name = project_source.name
            self.format = project_source.format
            self.language = project_source.language
            self.description = project_source.description
            self.requirements = project_source.requirements
            self.results = project_source.results
            self.additional_files = project_source.additional_files
            self.professor_id = project_source.professor_id
        else:
            raise ValidationError("Error! Cannot find the source project.")

    name = fields.Char('Project Name', compute=_set_default_project_values, store=True, translate=True)
    format = fields.Selection([('research', 'Research'), ('project', 'Project'), ('startup', 'Start-up')], string="Format", compute=_set_default_project_values, store=True)
    language = fields.Selection([('en', 'English'), ('ru', 'Russian')], string="Language", compute=_set_default_project_values, store=True)
    professor_id = fields.Many2one('student.professor', string='Professor', compute=_set_default_project_values, store=True)

    description = fields.Text('Detailed Description', compute=_set_default_project_values, store=True)
    requirements = fields.Text('Application Requirements', compute=_set_default_project_values, store=True)
    results = fields.Text('Expected Results', compute=_set_default_project_values, store=True)

    reason = fields.Text(string='Return/Rejection Reason')

    additional_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_availability_additional_files_rel',
        column1='availability_id',
        column2='attachment_id',
        string='Attachments',
        compute=_set_default_project_values, store=True
    )

    def _set_default_program_domain(self):
        if self._context.get('project_faculty_id', False):
            return self._context.get('project_faculty_id', False)[0]

    program_id = fields.Many2one('student.program', string='Program', required=True)
    program_id_faculty_domain = fields.Integer(string='Program - Faculty Domain', default=_set_default_program_domain, help="Dynamic domain used for program choice.")

    program_supervisor_account = fields.Many2one('res.users', string='Program Supervisor', compute="_set_program_supervisor", store=True)

    @api.depends('program_id')
    def _set_program_supervisor(self):
        for availability in self:
            availability.program_supervisor_account = availability.program_id.supervisor.supervisor_account

    degree_ids = fields.Many2many('student.degree', string='Degree', required=True)
    degree_ids_level_domain = fields.Char(string="Degree - Level Domain", help="Dynamic domain used for degree choice.")

    @api.onchange('program_id')
    def _set_up_degree(self):
        self.degree_ids = [(6, 0, [])] # Purge all degrees
        self.degree_ids_level_domain = self.program_id.degree # Limit degrees based on the program degree

    color_supervision = fields.Integer(string="Supervision Card Color", compute='_compute_supervision_color_value', store=True)

    @api.depends('state')
    def _compute_supervision_color_value(self):
        for availability in self:
            match availability.state:
                case 'pending': 
                    self.color_supervision = 4
                case 'returned':
                    self.color_supervision = 5
                case 'approved':
                    self.color_supervision = 10
                case 'rejected':
                    self.color_supervision = 1
                case _:
                    ValidationError("This project has an invalid supervision state. Please contact the system administrator.")
   
    @api.model
    def _expand_state_groups(self, states, domain, order):
        return ['pending', 'approved', 'rejected', 'returned'] # 'waiting' is hidden
        
    def _check_supervisor_identity(self,check=False):
        if check and not self.env.user.has_group('student.group_administrator'):
            if self.env.user != self.program_supervisor_account:
                raise AccessError("You can only react to projects sent to the program that you are supervising.")
            
    # BUTTON ACTIONS
    def action_view_availability_approve(self):
        if self.state == "pending":
            self._check_supervisor_identity(True)

            # Create grading entries 
            for degree in self.degree_ids:
                new_approval = self.env['student.approval'].sudo().create({
                    'type': self.type,
                    'program_id': self.program_id.id,
                    'degree_id': degree.id
                }).id
                self.project_id.approval_ids = [(4, new_approval)]
            
            self.state = "approved"
            self.project_id.action_view_project_approve(self.program_id.id)
        else:
            raise UserError("You can only approve project submissions in 'Pending' status.")
    
    def _check_reason(self,check=False):
        if check:
            if not self.reason:
                raise UserError("You need to provide a reason for rejection/return.")
            if len(self.reason) < 20:
                raise UserError("Please provide a more detailed reason (at least 20 characters).")

    def action_view_availability_reject(self):
        if self.state == "pending":
            self._check_supervisor_identity(True)
            self._check_reason(True)           

            self.state = "rejected"
            self.project_id.action_view_project_reject(self)
        else:
            raise UserError("You can only reject project submissions in 'Pending' status.")

    def action_view_availability_return(self):
        self._check_supervisor_identity(True)
        self._check_reason(True)          

        self.state = "returned"
        self.project_id.action_view_project_return(self)

    def action_view_availability_branch(self):
        if self.env.user.has_group('student.group_professor'):   
            new_project = self.env['student.project'].browse(self.project_id.id).copy({'name': self.project_id.name + " ⎇ " + self.program_id.name,
                                                                                       'state_evaluation': 'draft',
                                                                                       'state_publication': 'ineligible'})
            new_availability = self.env['student.availability'].browse(self.id).copy({'state': 'waiting',
                                                                                      'project_id': new_project.id})
            new_project.availability_ids = [(4, new_availability.id)]

            return {
                'type': 'ir.actions.act_window',
                'name': 'Create a New Project Branch',
                'res_model': 'student.project',
                'view_mode': 'form',
                'res_id': new_project.id,
                'target': 'current'
            }
        else:
            raise UserError("Only the professor who submitted this project can create a new branch.")
        
    # Define the action to open the form view of student.availability
    def action_view_availability_open_full(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Student Availability',
            'res_model': 'student.availability',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'res_id': self.id,
            'context': {'project_id': False}
        }
        return action

    # RESTRICTIONS #
    @api.constrains("reason")
    def _check_reason_modified(self):
        for availability in self:
            if availability.state == 'pending':
                if not availability.env.user.has_group("student.group_supervisor"):
                    raise UserError("Only academic supervisors can modify the feedback!")
                elif availability.env.user != availability.program_supervisor_account:
                    raise UserError("This project is not sent to a program you are supervising.")
            
    @api.constrains("degree_ids")
    def _check_degree_ids_modified(self):
        for record in self:
            if record.env.user.has_group("student.group_professor"):
                if record.project_id.professor_account.id != record.env.user.id:
                    raise ValidationError("You cannot modify the details of projects of other professors!")
                elif record.state == "pending":
                    raise UserError("This project is already submitted, cancel the submission to modify this section.")
            elif record.env.user.has_group("student.group_supervisor") and record.program_id.supervisor.supervisor_account.id != record.env.user.id:
                raise UserError("This project is not sent to a program you are supervising.")
    
    _sql_constraints = [('check_uniqueness', 'UNIQUE(program_id, project_id)', 'You have specified duplicate target programs.')]