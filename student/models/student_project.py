from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError

class Project(models.Model):
    _name = "student.project"
    _description = "PaLMS - Projects"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'student.utils']

    # Locks fields upon submitting
    locked = fields.Boolean(default=False)

    name = fields.Char('Project Name', required=True, translate=True)
    name_ru = fields.Char('Название проекта', required=True, translate=True)
    create_date = fields.Datetime("Created", readonly=True)
    create_date_date = fields.Date("Creation Date", default=lambda self: fields.Datetime.now(), readonly=True)
    write_date = fields.Datetime("Last Update", readonly=True)
    write_date_date = fields.Date("Last Update Date", compute="_compute_write_date", store=True, readonly=True)
    description = fields.Text('Detailed Description', required=True)
    requirements = fields.Text('Application Requirements')
    results = fields.Text('Expected Results')

    campus_ids = fields.Many2many('student.campus', string='Campus', required=True)
    faculty_ids = fields.Many2many('student.faculty', 
                                   string='Target Faculties', 
                                   required=True)    
    program_ids = fields.Many2many(comodel_name='student.program',
                                   relation='student_project_program_rel',
                                   column1='project_id',
                                   column2='program_id',
                                   string='Target Programs',
                                   compute="_find_programs",
                                   store=True,
                                   readonly=False,
                                   required=True)
    degree_ids = fields.Many2many('student.degree', string='Available for', required=True)

    approved_program_ids = fields.Many2many(comodel_name='student.program',
                                            relation='student_project_approved_program_rel',
                                            column1='project_id',
                                            column2='program_id',
                                            string='Applicable Programs',
                                            readonly=True)
    rejected_program_ids = fields.Many2many(comodel_name='student.program',
                                            relation='student_project_rejected_program_rel',
                                            column1='project_id',
                                            column2='program_id',
                                            string='Non-Applicable Programs',
                                            readonly=True)
            
    proposal_id = fields.Many2one('student.proposal', string="Proposal", readonly=True)
    
    type = fields.Selection([('cw', 'Course Work (Курсовая работа)'), ('fqw', 'Final Qualifying Work (ВКР)')], string="Project Type", required=True)
    format = fields.Selection([('research', 'Research'), ('project', 'Project'), ('startup', 'Start-up')], string="Format", required=True)
    language = fields.Selection([('en', 'English'), ('ru', 'Russian')], default="en", string="Language", required=True)
    assigned = fields.Boolean('Assigned to a student?', default=False, readonly=True)
    student_elected = fields.One2many('student.student', 'current_project', string='Elected Student', readonly=True)
    state = fields.Selection([('draft', 'Draft'),       
                              ('pending', 'Pending'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('returned','Returned'),
                              ('applied', 'Application Received'),  
                              ('assigned', 'Assigned')],           
                              group_expand='_expand_groups', default='draft', string='State', readonly=True, store=True, tracking=False)
    reason = fields.Text(string='Return/Rejection Reason')
    project_events = fields.Many2many('student.event', string="Project Events")

    additional_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_project_additional_files_rel',
        column1='project_id',
        column2='attachment_id',
        string='Attachments'
    )
    file_count = fields.Integer('Number of attached files', compute='_compute_file_count', readonly=True)

    result_text = fields.Text(string='Results')    
    result_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_project_result_files_rel',
        column1='project_id',
        column2='attachment_id',
        string='Result Files'
    )

    @api.onchange("result_files")
    def _update_ownership(self):
        # Updates the ownership of files for other users to access them
        for attachment in self.result_files:
            attachment.write({'res_model': self._name, 'res_id': self.id})

    # Show projects from the same faculty
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        pass_filters = False
        user_faculty = False
        viewing_professor = False

        # Get the current user's faculty_id
        if self.env.user.has_group('student.group_administrator'):
            pass_filters = True
        elif self.env.user.has_group('student.group_supervisor'):
            user_faculty = self.env['student.supervisor'].sudo().search([('supervisor_account', '=', self.env.user.id)], limit=1).supervisor_faculty
        elif self.env.user.has_group('student.group_professor'):
            viewing_professor = self.env['student.professor'].sudo().search([('professor_account', '=', self.env.user.id)], limit=1)
            user_faculty = viewing_professor.professor_faculty
        elif self.env.user.has_group('student.group_student'):
            user_faculty = self.env['student.student'].sudo().search([('student_account', '=', self.env.user.id)], limit=1).student_faculty

        # If the user has a faculty, add a domain to filter projects
        if not pass_filters:
            if user_faculty:
                # Professor can see their projects if they sent it to another faculty
                if viewing_professor:
                    args.append('|')
                    args.append(('faculty_ids', 'in', [user_faculty.id]))
                    args.append(('professor_id', '=', viewing_professor.id))
                else:
                    args.append(('faculty_ids', 'in', [user_faculty.id]))
            else:
                raise AccessError("The user is not correctly registered in any of the faculties. Contact the manager for the fix.")

        return super(Project, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.depends('additional_files')
    def _compute_file_count(self):
        self.file_count = len(self.additional_files)

    program_supervisors = fields.Many2many('res.users', compute='_compute_program_supervisors', string='Program Supervisors', store=True, readonly=True)

    @api.depends('program_ids')
    def _compute_program_supervisors(self):
        for record in self:
            supervisor_ids = record.program_ids.mapped('supervisor.supervisor_account.id')
            record.program_supervisors = [(6, 0, supervisor_ids)]

    # Assigns the professor account created for this user
    @api.model
    def _default_professor(self):
        professor = self.env['student.professor'].sudo().search([('professor_account.id', '=', self.env.uid)], limit=1)
        return professor.id if professor else False

    # ♦ What if an administrator creates a project?
    professor_id = fields.Many2one('student.professor', default=_default_professor, string='Professor', readonly=True, required=True)
    professor_account= fields.Many2one('res.users', string="Professor Account", compute='_compute_professor_account', store=True)

    @api.depends('professor_id')
    def _compute_professor_account(self):
        for project in self:
            project.professor_account = project.professor_id.professor_account
    
    applications = fields.Integer('Number of Applications', compute='_compute_application_count', readonly=True)
    application_ids = fields.One2many('student.application', 'project_id', string='Applications', domain=[('state','in',['sent','accepted','rejected'])])

    @api.depends('application_ids')
    @api.model
    def _compute_application_count(self):
        for project in self:
            project.applications = len(project.application_ids)
            if project.applications > 0 and project.state == 'approved':
                project.state = 'applied'

    @api.depends('write_date')
    def _compute_write_date(self):
        for record in self:
            record.write_date_date = record.write_date.date()

    # COLORING #        
    # Handle the coloring of the project
    color = fields.Integer(string="Box Color", default=4, compute='_compute_color_value', store=True)

    # Updates color based on the state
    @api.depends('state')
    def _compute_color_value(self):
        if self.state == 'draft':
            self.color = 4
        elif self.state == 'pending':
            self.color = 3
        elif self.state == 'approved':
            self.color = 10
        elif self.state == 'rejected':
            self.color = 9
        elif self.state == 'returned':
            self.color = 11
        elif self.state == 'applied':
            self.color = 6
        elif self.state == 'assigned':
            self.color = 8

    # Orders kanban groups/stages
    @api.model
    def _expand_groups(self, states, domain, order):
        return ['draft', 'pending', 'returned', 'approved', 'applied', 'assigned', 'rejected']
    
    # RESTRICTIONS #
    @api.constrains("reason")
    def _check_reason_modified(self):
        if not self.env.user.has_group("student.group_supervisor") and self.state == 'pending':
            raise UserError("Only academic supervisors can modify the feedback!")
        
        if self.env.user.id not in self.program_supervisors.mapped('id') and self.state == 'pending':
            raise UserError("This project is not sent to a program you are supervising.")

    # UTILITY #
    # Prevents the creation of the default log message
    @api.model
    def create(self, vals):
        project = super(Project, self.with_context(tracking_disable=True)).create(vals)

        # Customizes the creation log message
        if self.proposal_id:
            message = _("A new project has been created upon the proposal of %s.") % (self.student_elected)
        else:
            message = _("A new project has been created by %s.") % (self.env.user.name)
        project.message_post(body=message)

        return project

    # BUTTON LOGIC #
    def _check_professor_identity(self):
        if not self.env.user.has_group('student.group_administrator') and not self.env.user.has_group('student.group_supervisor'):
            if self.professor_account != self.env.user:
                raise AccessError("You can only modify your projects.")

    # You may send different messages submission and re-submission.
    def action_view_project_submit(self):
        self._check_professor_identity()
                
        if self.state in ['draft', 'returned']:
            self.locked = True
            self.write({'state': 'pending'})

            # Updates the ownership of files for other users to access them
            for attachment in self.additional_files:
                attachment.write({'res_model': self._name, 'res_id': self.id})

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            supervisor_name_list = [supervisor.name for supervisor in self.program_supervisors]
            body = f"The project is submitted for the approval of supervisor(s). <br> <i><b>Supervisor(s):</b> {', '.join(supervisor_name_list)}</i>"
            self.message_post(body=body, subtype_id=subtype_id.id)
            
            # Send the email --------------------
            subtype_id = self.env.ref('student.student_message_subtype_email')
            template = self.env.ref('student.email_template_project_submission')
            template.send_mail(self.id, 
                               email_values={'email_to': ','.join([supervisor.email for supervisor in self.program_supervisors]),
                                             'subtype_id': subtype_id.id}, 
                               force_send=True)
            # -----------------------------------

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Received</strong><p> {self.professor_account.name} sent a project proposal: <b><a href="/web#id={self.id}&model=student.project">{self.name}</a></b></p> <p><i>Please evaluate the submission.</i></p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message('project', message_text, self.program_supervisors, self.professor_account, str(self.id))

            return self.env['student.utils'].message_display('Confirmation', 'The project is successfully submitted.', False)
            # ♦ This strangely prevents the project status to be immediately updated in the UI.
    
    def action_view_project_cancel(self):
        self._check_professor_identity()

        if self.state == 'pending':
            self.locked = False
            self.write({'state': 'draft'})

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            body = _('The project submission is cancelled.')
            self.message_post(body=body, subtype_id=subtype_id.id)

            return self.env['student.utils'].message_display('Cancellation', 'The project submission is cancelled.', False)
        
    def _check_supervisor_identity(self):
        if not self.env.user.has_group('student.group_administrator'):
            if self.env.user not in self.program_supervisors:
                raise AccessError("You can only react to projects sent to the program that you are supervising.")
    
    # Check if all supervisors have decided. If yes, mark the project accordingly.            
    def _check_decisions(self):
        if len(self.program_ids) == (len(self.approved_program_ids) + len(self.rejected_program_ids)):
            if self.student_elected:
                return 'assigned'
            
            if len(self.approved_program_ids) > 0:
                return 'approved'
            else:
                return 'rejected'
        
        return 'pending'

    def action_view_project_approve(self):
        self._check_supervisor_identity()

        if self.state == 'pending':
            if self.proposal_id:              
                self.write({'state': 'assigned'})
            else:                
                supervisor_programs = self.env['student.supervisor'].search([('supervisor_account', '=', self.env.uid)]).program_ids
                for program in supervisor_programs:
                    self.approved_program_ids = [(4, program.id)] 

                self.write({'state': self._check_decisions()})

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            body = _('The project is approved by ' + self.env.user.name + '.')
            self.message_post(body=body, subtype_id=subtype_id.id)

            # Send the email --------------------
            subtype_id = self.env.ref('student.student_message_subtype_email')
            template = self.env.ref('student.email_template_project_approval')
            template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
            # -----------------------------------

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Approved</strong><p> ' + self.env.user.name + ' has accepted your project «' + self.name + '».</p><p>Eligible students can see and apply for the project after all supervisors complete their evaluation.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message('project', message_text, self.professor_account, self.env.user, str(self.id))

            return self.env['student.utils'].message_display('Approval', 'The project is successfully approved.', False)
        else:
            raise UserError("You can only approve projects submissions in 'Pending' status.")
	
    def _check_reason(self):
        if not self.reason:
            raise UserError("You need to provide a reason for rejection/return.")
        if len(self.reason) < 20:
            raise UserError("Please provide a more detailed reason (at least 20 characters).")
        
    def action_view_project_reject(self):
        self._check_supervisor_identity()

        if self.state == 'pending':
            self._check_reason()           

            supervisor_programs = self.env['student.supervisor'].search([('supervisor_account', '=', self.env.uid)]).program_ids
            for program in supervisor_programs:
                self.rejected_program_ids = [(4, program.id)] 
                
            self.write({'state': self._check_decisions()})

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            body = _('The project is rejected by ' + self.env.user.name + '.<br><b>Rejection reason: </b>' + self.reason)
            self.message_post(body=body, subtype_id=subtype_id.id)

            # Reset the reason after logging it.
            self.reason = ""

            # Send the email --------------------
            subtype_id = self.env.ref('student.student_message_subtype_email')
            template = self.env.ref('student.email_template_project_rejection')
            template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
            # -----------------------------------

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Rejected</strong><p> ' + self.env.user.name + ' has rejected your project «' + self.name + '».</p><p>You can check the <b>project log</b> to learn about the reason.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message('project', message_text, self.professor_account, self.env.user, str(self.id))

            return self.env['student.utils'].message_display('Rejection', 'The project is rejected.', False)
        else:
            raise UserError("You can only reject projects submissions in 'Pending' status.")
    
    def action_view_project_return(self):
        self._check_supervisor_identity()

        if self.state == 'pending':
            self._check_reason()

            self.locked = False
            self.write({'state': 'returned'})

            # When a supervisor returns the project, all approval progress is reset
            self.approved_program_ids = [(5, 0, 0)]  
            self.rejected_program_ids = [(5, 0, 0)]

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            body = _('The project is returned by ' + self.env.user.name + ' for the reason below. Resubmission after applying requested modifications is possible.<br><b>Rejection reason: </b>' + self.reason)
            self.message_post(body=body, subtype_id=subtype_id.id)

            # Reset the reason after logging it.
            self.reason = ""

            # Send the email --------------------
            subtype_id = self.env.ref('student.student_message_subtype_email')
            template = self.env.ref('student.email_template_project_return')
            template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
            # -----------------------------------

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Returned</strong><p> ' + self.env.user.name + ' has returned your proposal "' + self.name + '".</p><p>You can check the <b>Supervisor Feedback</b> section on the project page to learn about the reason. After making necessary changes, you can resubmit the project.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message('project', message_text, self.professor_account, self.env.user, str(self.id))

            return self.env['student.utils'].message_display('Return', 'The project is returned.', False)

    # The reset button functionality for development purposes
    def action_view_project_reset(self):
        self.state = "draft"
        self.locked = False
        self.student_elected = None
        self.student_elected.current_project = None
        self.reason = ""

        # Erase all applications for this project
        applications = self.env['student.application'].search([('project_id', '=', self.id)])
        applications.unlink()

    # Creates an application upon clicking "Apply"
    def action_view_project_apply(self):
        student_record = self.env['student.student'].sudo().search([('student_account.id', '=', self.env.uid)], limit=1)
        if not student_record:
            raise AccessError("You are not registered as a student in the system, please contact your academic supervisor.")
        else:
            if student_record.student_program not in self.approved_program_ids:
                raise UserError("This project is not applicable for your program, please use filters to find another one.")
            elif student_record.degree not in self.degree_ids:
                raise UserError("This project is not applicable for your level of education, please use filters to find another one.")
            else:
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
    
    # Navigates to events of this project
    def action_view_project_events(self):
        action = self.env.ref('student.action_event').read()[0]
        action['domain'] = [('related_projects', 'in', self.ids)]
        return action

    # UI ASSIST # 
    # Makes adding/removing programs in bulk easier for the user
    @api.depends('faculty_ids')
    def _find_programs(self):
        program_ids = self.faculty_ids.mapped('program_ids')
        self.program_ids = program_ids