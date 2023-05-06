from odoo import fields, models, api, _ #_ is for translations
from odoo.exceptions import UserError

class Project(models.Model):
    _name = "student.project"
    _description = "OpenLMS - Projects"
    _inherit = ['mail.thread', 'student.utils']

    locked = fields.Boolean(default=False)

    name = fields.Char('Project Name', required=True, translate=True)
    name_ru = fields.Char('Название проекта', required=True, translate=True)
    creation_date = fields.Date("Creation Date", default=lambda self: fields.Datetime.now(), readonly=True)
    description = fields.Text('Detailed Description', required=True)
    faculty_ids = fields.Many2many('student.faculty', string='Applicable Faculties', required=True)
    program_ids = fields.Many2many('student.program', string='Applicable Programs', required=True)
    type = fields.Selection([('cw', 'Course Work (Курсовая работа)'), ('fqw', 'Final Qualifying Work (ВКР)')], string="Project Type")
    format = fields.Selection([('research', 'Research'), ('project', 'Project'), ('startup', 'Start-up')], string="Project Format")
    degree_ids = fields.Many2many('student.degree', string='Available for', required=True)
    applications = fields.Integer('Number of Applications', compute='_compute_application_count', readonly=True)
    assigned = fields.Boolean('Assigned to a student?', default=False, readonly=True)
    student_elected = fields.One2many('student.student', 'current_project', string='Elected Student', readonly=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', 'Draft'),       
                              ('pending', 'Pending'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('returned','Returned'),
                              ('applied', 'Application Received'),  
                              ('assigned', 'Assigned')],           
                              group_expand='_expand_groups', default='draft', string='State', readonly=True, store=True)
    reason = fields.Text(string='Return/Rejection Reason')
    additional_files = fields.Many2many(comodel_name="ir.attachment", string="Attachments") 

	# Updates the ownership of files for users to access them
    @api.model
    @api.onchange("additional_files")
    def _fix_files(self):
        for attachment in self.additional_files:
            attachment.write({'res_model': self._name, 'res_id': self.id})
                        
    # Handle the coloring of the project
    color = fields.Integer(string="Box Color", default=4, compute='_compute_color_value', store=True)

    @api.depends('state')
    def _compute_color_value(self):
        if self.state == 'draft':
            self.color = 4
        if self.state == 'pending':
            self.color = 3
        if self.state == 'approved':
            self.color = 10
        if self.state == 'rejected':
            self.color = 9
        if self.state == 'returned':
            self.color = 11
        if self.state == 'applied':
            self.color = 6
        if self.state == 'assigned':
            self.color = 8

    # Orders kanban groups/stages
    @api.model
    def _expand_groups(self, states, domain, order):
        return ['draft', 'pending', 'returned', 'approved', 'applied', 'assigned', 'rejected']

    program_supervisors = fields.Many2many('res.users', compute='_compute_program_supervisors', string='Program Supervisors', readonly=True)

    @api.depends('program_ids')
    def _compute_program_supervisors(self):
        for record in self:
            supervisor_ids = record.program_ids.mapped('supervisor.id')
            record.program_supervisors = [(6, 0, supervisor_ids)]

    # Assigns the professor account created for this user
    @api.model
    def _default_professor(self):
        professor = self.env['student.professor'].sudo().search([('professor_account.id', '=', self.env.uid)], limit=1)
        return professor.id if professor else False

    # ♦ What if a supervisor creates a project?
    professor_id = fields.Many2one('student.professor', default=_default_professor, string='Professor', readonly=True, required=True)
    
    professor_account= fields.Many2one('res.users', string="Professor Account", compute='_compute_professor_account', store=True)

    @api.depends('professor_id')
    def _compute_professor_account(self):
        for project in self:
            project.professor_account = project.professor_id.professor_account

    # Prevents the creation of the default log message
    @api.model
    def create(self, vals):
        project = super(Project, self.with_context(tracking_disable=True)).create(vals)

        # Customizes the creation log message
        message = _("A new project has been created by %s.") % (self.env.user.name)
        project.message_post(body=message)

        return project
    
    application_ids = fields.One2many('student.application', 'project_id', string='Applications', domain=[('state','in',['sent','accepted','rejected'])])

    @api.depends('application_ids')
    @api.model
    def _compute_application_count(self):
        for project in self:
            project.applications = len(project.application_ids)
            if project.applications > 0 and project.state == 'approved':
                project.state = 'applied'

    # Set the default filter to show only projects for the current user
    # @api.model
    # def default_get(self, fields):
    #     res = super(Project, self).default_get(fields)
    #     res['domain'] = [('professor_id', '=', self.env.user.id)]
    #     return res
    
    def message_display(self, title, message, sticky_bool):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': message,
                'sticky': sticky_bool,
                'next': {
                    'type': 'ir.actions.act_window_close',
                }
            }
        }

    def action_view_project_submit(self):
        if self.state in ['draft', 'returned']:
            self.locked = True
            self.write({'state': 'pending'})

            # Log the action
            for supervisor in self.program_supervisors:
                body = _("The project is submitted for %s's approval.", supervisor.name)
                self.message_post(body=body)

            # Get the Odoo Bot user
            odoobot = self.env.ref('base.partner_root')

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Received</strong><p> ' + self.professor_account.name + " sent a project proposal: <b>" + self.name + "</b></p><p><i>Please evaluate the submission.</i></p>"

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message(False, message_text, self.program_supervisors, odoobot)

            return self.message_display('Confirmation', 'Project is successfully submitted.', False)
            # ♦ This strangely prevents the project status to be immediately updated in the UI.
    
    def action_view_project_cancel(self):
        if self.state == 'pending':
            self.locked = False
            self.write({'state': 'draft'})

            # Log the action
            body = _('The project submission is cancelled.')
            self.message_post(body=body)

            return self.message_display('Cancellation', 'The project submission is cancelled.', False)
    
    # ♦ What if supervisors make different decisions?
    def action_view_project_approve(self):
        if self.state == 'pending':
            self.write({'state': 'approved'})

            # Log the action
            body = _('The project is approved by ' + self.env.user.name + '.')
            self.message_post(body=body)

            # Get the Odoo Bot user
            odoobot = self.env.ref('base.partner_root')

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Approved</strong><p> ' + self.env.user.name + ' has accepted your project "' + self.name + '".</p><p>Eligible students can now see and apply for the project.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message(False, message_text, [self.professor_account], odoobot)

            return self.message_display('Approval', 'The project is successfully approved.', False)
	
    def _check_reason(self):
        if not self.reason:
            raise UserError("You need to provide a reason for rejection/return.")
        if len(self.reason) < 20:
            raise UserError("Please provide a more detailed reason (at least 20 characters).")
        
    def action_view_project_reject(self):
        if self.state == 'pending':
            self._check_reason()

            self.write({'state': 'rejected'})

            # Log the action
            body = _('The project is rejected by ' + self.env.user.name + '.')
            self.message_post(body=body)

            # Get the Odoo Bot user
            odoobot = self.env.ref('base.partner_root')

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Rejected</strong><p> ' + self.env.user.name + ' has rejected your project "' + self.name + '".</p><p>You can check the <b>Supervisor Feedback</b> section on the project page to learn about the reason.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message(False, message_text, [self.professor_account], odoobot)

            return self.message_display('Rejection', 'The project is rejected.', False)
    
    def action_view_project_return(self):
        if self.state == 'pending':
            self._check_reason()

            self.locked = False
            self.write({'state': 'returned'})

            # Log the action
            body = _('The project is returned by ' + self.env.user.name + '. Resubmission after applying requested modifications is possible.')
            self.message_post(body=body)

            # Get the Odoo Bot user
            odoobot = self.env.ref('base.partner_root')

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Returned</strong><p> ' + self.env.user.name + ' has returned your proposal "' + self.name + '".</p><p>You can check the <b>Supervisor Feedback</b> section on the project page to learn about the reason. After making necessary changes, you can resubmit the project.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message(False, message_text, [self.professor_account], odoobot)

            return self.message_display('Return', 'The project is returned.', False)

    def action_view_project_reset(self):
        self.state = "draft"
        self.student_elected = None
        self.student_elected.current_project = None

        # Erase all applications for this project
        project_id = self.id  
        applications = self.env['student.application'].search([('project_id', '=', project_id)])
        applications.unlink()


    # Creates an application upon clicking "Apply"
    def action_view_project_apply(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Application',
            'res_model': 'student.application',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id
            }
        }