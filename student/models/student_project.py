from markupsafe import Markup
from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import copy, ast

class Project(models.Model):
    _name = "student.project"
    _description = "PaLMS - Projects"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'student.utils']

    current_user_follower = fields.Boolean(string="Is the current user among the project followers?", compute='_compute_current_user_follower')
    def _compute_current_user_follower(self):
        if self.state_publication not in ['ineligible', 'published', 'applied'] and self.project_project_id:
            partner_ids = self.env['project.project'].sudo().browse(self.project_project_id.id).message_follower_ids.mapped('partner_id.id')
            self.current_user_follower = True if self.env['res.users'].browse(self.env.user.id).partner_id.id in partner_ids else False
        else:
            self.current_user_follower = False
        
    proposal_id = fields.Many2one('student.proposal', string="Proposal", readonly=True)

    state_evaluation = fields.Selection([('draft', 'Draft'),       
                                         ('progress', 'In Progress'),
                                         ('approved', 'Approved'),
                                         ('mixed', 'Mixed Evaluation'),
                                         ('rejected', 'Rejected')],           
                                         group_expand='_expand_evaluation_groups', default='draft', string='Evaluation State', readonly=True, tracking=True)
    state_publication = fields.Selection([('ineligible', 'Ineligible'),
                                          ('published', 'Published'),       
                                          ('applied', 'Application Received'),
                                          ('assigned', 'Assigned'),
                                          ('completed', 'Completed'),
                                          ('dropped', 'Dropped')],           
                                          group_expand='_expand_publication_groups', default='ineligible', string='Publication State', readonly=True, tracking=True)

    name = fields.Char('Project Name', required=True, translate=True)
    format = fields.Selection([('research', 'Research'), ('project', 'Project'), ('startup', 'Start-up')], string="Format", default="research", required=True)
    language = fields.Selection([('en', 'English'), ('ru', 'Russian')], default="en", string="Language", required=True)

    create_date = fields.Datetime("Created", readonly=True)
    create_date_date = fields.Date("Creation Date", default=lambda self: fields.Datetime.now(), readonly=True)
    write_date = fields.Datetime("Last Update", readonly=True)
    write_date_date = fields.Date("Last Update Date", compute="_compute_write_date", store=True, readonly=True)

    @api.depends('write_date')
    def _compute_write_date(self):
        for record in self:
            record.write_date_date = record.write_date.date()

    description = fields.Text('Detailed Description', required=True, translate=True)
    requirements = fields.Text('Application Requirements', required=True, translate=True)
    results = fields.Text('Expected Results', required=True, translate=True)

    # ♥ You can merge these functions.
    # Assigns the professor's faculty
    @api.model
    def _default_campus(self):
        professor = self.env['student.professor'].sudo().search([('professor_account.id', '=', self.env.uid)], limit=1)
        return professor.professor_faculty.campus if professor else False
    campus_id = fields.Many2many('student.campus', string='Campus', default=_default_campus, required=True)

    # Assigns the professor's faculty
    @api.model
    def _default_faculty(self):
        professor = self.env['student.professor'].sudo().search([('professor_account.id', '=', self.env.uid)], limit=1)
        return professor.professor_faculty if professor else False
    faculty_id = fields.Many2many('student.faculty', string='Faculty', default=_default_faculty, required=True) 
      
    program_ids = fields.Many2many(comodel_name='student.program',
                                   relation='student_project_program_rel',
                                   column1='project_id',
                                   column2='program_id',
                                   string='Target Programs',
                                   store=True,
                                   readonly=False)
    program_ids_count = fields.Integer('Number of Total Submissions', compute="_compute_program_counts", store=True, readonly=True)
    pending_program_ids = fields.Many2many(comodel_name='student.program',
                                           relation='student_project_pending_program_rel',
                                           column1='project_id',
                                           column2='program_id',
                                           string='Pending Programs (TECHNICAL)',
                                           readonly=True)
    pending_program_ids_count = fields.Integer('Number of Pending Submissions', compute="_compute_program_counts", store=True, readonly=True)
    returned_program_ids = fields.Many2many(comodel_name='student.program',
                                           relation='student_project_returned_program_rel',
                                           column1='project_id',
                                           column2='program_id',
                                           string='Returned Programs (TECHNICAL)',
                                           readonly=True)
    returned_program_ids_count = fields.Integer('Number of Returned Programs', compute="_compute_program_counts", store=True, readonly=True)
    approved_program_ids = fields.Many2many(comodel_name='student.program',
                                            relation='student_project_approved_program_rel',
                                            column1='project_id',
                                            column2='program_id',
                                            string='Applicable Programs',
                                            readonly=True)
    approved_program_ids_count = fields.Integer('Number of Approved Submissions', compute="_compute_program_counts", store=True, readonly=True)

    @api.depends('program_ids','pending_program_ids','approved_program_ids')
    def _compute_program_counts(self):
        self.program_ids_count = len(self.program_ids)
        self.pending_program_ids_count = len(self.pending_program_ids)
        self.returned_program_ids_count = len(self.returned_program_ids)
        self.approved_program_ids_count = len(self.approved_program_ids)
    
    availability_ids = fields.One2many('student.availability', 'project_id', string='Target Programs')

    reason = fields.Text(string='Return/Rejection Reason')

    program_supervisors = fields.Many2many('res.users', compute='_compute_program_supervisors', string='Program Supervisors', store=True, readonly=True)

    @api.depends('program_ids')
    def _compute_program_supervisors(self):
        for record in self:
            supervisor_ids = record.program_ids.mapped('supervisor.supervisor_account.id')
            record.program_supervisors = [(6, 0, supervisor_ids)]
    
    assigned = fields.Boolean('Assigned to a student?', default=False, readonly=True)
    student_elected = fields.One2many('student.student', 'current_project', string='Elected Student', readonly=True)

    additional_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_project_additional_files_rel',
        column1='project_id',
        column2='attachment_id',
        string='Attachments'
    )
    file_count = fields.Integer('Number of attached files', compute='_compute_file_count', readonly=True)

    project_report_file = fields.Binary(string='Project Report')
    project_report_filename = fields.Char()
    project_preview_toggle = fields.Boolean('Show Preview', default=False)

    plagiarism_check_file = fields.Binary(string='Plagiarism Check')
    plagiarism_check_filename = fields.Char()

    professor_review_file = fields.Binary(string='Professor Review')
    professor_review_filename = fields.Char()

    @api.onchange("additional_files")
    def _update_additional_ownership(self):
        # Makes the files public, may implement user-specific ownership in the future
        for attachment in self.additional_files:
            attachment.write({'public': True})

    @api.depends('additional_files')
    def _compute_file_count(self):
        self.file_count = len(self.additional_files)

    result_text = fields.Text(string='Results')    
    result_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_project_result_files_rel',
        column1='project_id',
        column2='attachment_id',
        string='Add Files'
    )

    student_feedback = fields.Text(string='Feedback from the Student')   
    notes = fields.Text(string='Notes & Comments')        
    grade = fields.Selection([('1', '1'),       
                              ('2', '2'),
                              ('3', '3'),
                              ('4', '4'),
                              ('5', '5'),
                              ('6', '6'),
                              ('7', '7'),  
                              ('8', '8'),  
                              ('9', '9'),  
                              ('10', '10')], string='Project Grade (Out of 10)')

    # Assigns the professor account created for this user
    @api.model
    def _default_professor(self):
        professor = self.env['student.professor'].sudo().search([('professor_account.id', '=', self.env.uid)], limit=1)
        if professor:
            return professor.id 
        else:
            raise ValidationError("The user is not registered as a professor. Contact the administrator for the fix.")

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
            if project.applications > 0 and project.state_publication == 'published':
                project.state_publication = 'applied'

    # Show projects from the same faculty
    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        active_view_type = self.env.context.get('view_type', False)

        # ♥♥ REVISE THIS SECTION FOR THE NEW BOARD SYSTEM
        # FACULTY FILTER in 'Project Board'
        if active_view_type == 'project_board':
            user_faculty = False
            viewing_professor = False

            # Get the current user's faculty_id
            if self.env.user.has_group('student.group_manager'):
                user_faculty = self.env['student.manager'].sudo().search([('manager_account', '=', self.env.user.id)], limit=1).manager_faculty
            if self.env.user.has_group('student.group_supervisor'):
                user_faculty = self.env['student.supervisor'].sudo().search([('supervisor_account', '=', self.env.user.id)], limit=1).supervisor_faculty
            elif self.env.user.has_group('student.group_professor'):
                viewing_professor = self.env['student.professor'].sudo().search([('professor_account', '=', self.env.user.id)], limit=1)
                user_faculty = viewing_professor.professor_faculty
            elif self.env.user.has_group('student.group_student'):
                user_faculty = self.env['student.student'].sudo().search([('student_account', '=', self.env.user.id)], limit=1).student_faculty

            # If the user has a faculty, add a domain to filter projects
            if not self.env.user.has_group('student.group_administrator'):
                if user_faculty:
                    # ♥ Currently disabled functionality: Professor can see their projects if they sent it to another faculty
                    if viewing_professor:
                        args.append('|')
                        args.append(('faculty_id', 'in', [user_faculty.id]))
                        args.append(('professor_id', '=', viewing_professor.id))
                    else:
                        args.append(('faculty_id', 'in', [user_faculty.id]))
                else:
                    raise AccessError("The user is not correctly registered in any of the faculties. Contact the administrator for the fix.")
        
        # AVAILABILITY FILTER for students in 'Available Projects'
        if active_view_type == 'available_projects':
            if self.env.user.has_group('student.group_student'):
                student_program = self.env['student.student'].sudo().search([('student_account', '=', self.env.user.id)], limit=1).student_program
    
            # Students can view projects only if they are applied for their programs
            if not self.env.user.has_group('student.group_administrator'):  
                if student_program:
                    args.append(('approved_program_ids', 'in', [student_program.id]))
                else:
                    raise AccessError("Student account or program is not registered. Contact the administrator for the fix.")

        # ACTION FILTER for supervisors in 'Pending Project Submissions'
        if active_view_type == 'pending_submissions':
            if self.env.user.has_group('student.group_supervisor'):
                supervisor_program = self.env['student.supervisor'].sudo().search([('supervisor_account', '=', self.env.user.id)], limit=1).program_ids.ids

            # Supervisors view projects as pending only if they haven't processed them yet
            if not self.env.user.has_group('student.group_administrator'): 
                if supervisor_program:
                    args.append(('pending_program_ids', '=', supervisor_program[0]))
                else:
                    raise AccessError("This supervisor account is not registered or not supervising any programs. Contact the administrator for the fix.")

        return super(Project, self).search(args, offset=offset, limit=limit, order=order)

    # COLORING #        
    # Handle the coloring of the project
    color_evaluation = fields.Integer(string="Evaluation Card Color", default=4, compute='_compute_evaluation_color_value', store=True)
    color_publication = fields.Integer(string="Publication Card Color", compute='_compute_publication_color_value', store=True)

    # Updates color based on the state
    # 1 - Red | 2 - Orange | 3 - Yellow | 4 - Cyan | 5 - Purple | 6 - Almond | 7 - Teal | 8 - Blue | 9 - Raspberry | 10 - Green | 11 - Violet
    @api.depends('state_evaluation')
    def _compute_evaluation_color_value(self):
        # ♥ Why does 'self' bring multiple projects?
        for project in self:
            match project.state_evaluation:
                case 'draft': 
                    self.color_evaluation = 4
                case 'progress':
                    self.color_evaluation = 3
                case 'approved':
                    self.color_evaluation = 10
                case 'mixed':
                    self.color_evaluation = 6
                case 'rejected':
                    self.color_evaluation = 1
                case _:
                    ValidationError("This project has an invalid evaluation state. Please contact the system administrator.")

    @api.depends('state_publication')
    def _compute_publication_color_value(self):
        for project in self:
            match project.state_publication:
                case 'published': 
                    self.color_publication = 4
                case 'applied':
                    self.color_publication = 5
                case 'assigned':
                    self.color_publication = 8
                case 'completed':
                    self.color_publication = 10
                case 'dropped':
                    self.color_publication = 1
                case _:
                    ValidationError("This project has an invalid publication state. Please contact the system administrator.")

    # Orders kanban groups/stages
    @api.model
    def _expand_evaluation_groups(self, states, domain, order):
        return ['draft', 'progress', 'approved', 'mixed', 'rejected']
    
    @api.model
    def _expand_publication_groups(self, states, domain, order):
        return ['published', 'applied', 'assigned', 'completed', 'dropped'] # 'ineligible' is hidden

    # UTILITY #
    # Prevents the creation of the default log message
    @api.model
    def create(self, vals):
        project = super(Project, self.with_context(tracking_disable=True)).create(vals)

        # ♥ Customizes the creation log message
        if self.proposal_id:
            message = _("A new project has been created upon the proposal of %s.") % (self.student_elected)
        else:
            message = _("A new project has been created by %s.") % (self.env.user.name)
        project.message_post(body=message)

        # ID/save check is used to unlock file addition and submission eligibility sections
        return project

    # BUTTON LOGIC #
    def _check_professor_identity(self):
        if not self.env.user.has_group('student.group_administrator') and not self.env.user.has_group('student.group_supervisor'):
            if self.professor_account != self.env.user:
                raise AccessError("You can only modify your projects.")

    # ♥ You may send different messages submission and re-submission.
    def action_view_project_submit(self):
        self._check_professor_identity()
        
        if len(self.availability_ids) <= 0:
            raise AccessError("You need to choose programs to submit first!")
        elif self.state_evaluation == 'draft':
            self.write({'state_evaluation': 'progress'})
            self._update_additional_ownership()

            # Assign availability record programs to the project
            availability_program_ids = self.availability_ids.mapped('program_id.id')
            self.program_ids = [(6, 0, availability_program_ids)]
            self.pending_program_ids = [(6, 0, availability_program_ids)]

            availabilities_to_mark = self.env['student.availability'].search([('project_id', '=', self.id)])
            for availability in availabilities_to_mark:
                availability.state = "pending"

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            supervisor_name_list = [supervisor.name for supervisor in self.program_supervisors]
            body = f"The project is submitted for the approval of supervisor(s). <br> <i><b>Supervisor(s):</b> {', '.join(supervisor_name_list)}</i>"
            self.message_post(body=Markup(body), subtype_id=subtype_id.id)
            
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
            self.env['student.utils'].send_message('project', Markup(message_text), self.program_supervisors, self.professor_account, (str(self.id),str(self.name)))

            return self.env['student.utils'].message_display('Confirmation', 'The project is successfully submitted.', False)
            # ♥ This strangely prevents the project status to be immediately updated in the UI.
        else:
            raise AccessError("Projects in this state cannot be submitted!")
    
    def action_view_project_cancel(self, automatic=False):
        if not automatic:
            self._check_professor_identity()

            if self.state_evaluation == 'progress':
                if self.env['student.availability'].search([('project_id', '=', self.id), ('state', 'not in', ['waiting','pending'])]):
                    raise UserError("It is not possible cancel processed projects! Contact system administrator for changes.")
                else:
                    self.write({'state_evaluation': 'draft'})

                    availabilities_to_mark = self.env['student.availability'].search([('project_id', '=', self.id)])
                    for availability in availabilities_to_mark:
                        availability.state = "waiting"

                    # Log the action --------------------
                    subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
                    body = _('The project submission is cancelled.')
                    self.message_post(body=body, subtype_id=subtype_id.id)

                    return self.env['student.utils'].message_display('Cancellation', 'The project submission is cancelled.', False)
        else:
            if self.env['student.availability'].search([('project_id', '=', self.id), ('state', '!=', 'returned')]):
                raise ValidationError("Not all supervisors returned the project. Automatic cancellation is invalid, please contact the system administrator.")
            else:
                self.write({'state_evaluation': 'draft'})

                availabilities_to_mark = self.env['student.availability'].search([('project_id', '=', self.id)])
                for availability in availabilities_to_mark:
                    availability.state = "waiting"

                # Log the action --------------------
                subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
                body = _("The project is returned from all submitted programs, so it is automatically reverted to 'Draft' status.")
                self.message_post(body=body, subtype_id=subtype_id.id)

                return self.env['student.utils'].message_display('Automatic Cancellation', 'The project submission is automatically cancelled.', False)

         
    # Check if all supervisors have decided. If yes, mark the project accordingly.      
    def _check_decisions(self):
        if len(self.pending_program_ids) == 0:
            if len(self.approved_program_ids) == len(self.program_ids):
                return 'approved'
            elif len(self.returned_program_ids) == len(self.program_ids):
                return 'draft'
            elif len(self.approved_program_ids) == 0:
                return 'rejected'
            else:
                return 'mixed'
        else:
            return 'progress'

    def action_view_project_approve(self, approved_program_id):
        if self.state_evaluation == "progress":
            if self.proposal_id:              
                self.write({'state_evaluation': 'approved', 'state_publication': 'assigned'})
                self.sudo().create_project_project()

                # Assign the user to the special group for them to view "My Project" menu
                group_id = self.env.ref('student.group_elected_student') 
                group_id.users = [(4, self.student_elected.student_account.id)]
            else:                
                self.approved_program_ids = [(4, approved_program_id)]
                self.pending_program_ids = [(3, approved_program_id)]

                self.write({'state_evaluation': self._check_decisions(), 'state_publication': 'published'})

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
            self.env['student.utils'].send_message('project', Markup(message_text), self.professor_account, self.env.user, (str(self.id),str(self.name)))

            return self.env['student.utils'].message_display('Approval', 'The project is successfully approved.', False)
        else:
            raise UserError("You can only reject projects submissions in 'Pending' status.")
	
    # RESTRICTIONS #            
    @api.constrains("result_text", "notes", "grade")
    def _check_modifier_faculty_member(self):
        if self.env.user.has_group("student.group_student"):
            raise UserError("Only faculty members can change these fields.")
            
    @api.constrains("name", "format", "language", "description", "requirements", "results", "additional_files", "professor_review_file")
    def _check_modifier_professor(self):
        if self.env.user.id != self.professor_account.id:
            raise UserError("You cannot modify projects of other professors.")
        
    @api.constrains("project_report_file", "project_check_file", "student_feedback")
    def _check_modifier_student(self):
        if self.state_publication == "assigned" and self.env.user.id != self.student_elected.student_account.id:
            raise UserError("These fields can be modified by the assigned student.")
        
    def unlink(self):
        for record in self:
            if not record.env.user.has_group('student.group_administrator'): 
                if record.state_publication == "assigned":
                    raise UserError(_('Only administrators can delete assigned projects!'))
                elif record.env.uid != record.professor_account.id or record.env.uid in record.program_supervisors.ids:
                    raise UserError(_('Only its professor or related supervisors can delete this project!'))

            # Remove the student from the group
            group_id = record.env.ref('student.group_elected_student') 
            group_id.users = [(3, record.student_elected.id)]

            record.availability_ids.unlink()
        
        return super(Project, self).unlink()
        
    def action_view_project_reject(self, rejected_availability_id):
        if self.state_evaluation == "progress":            
            self.pending_program_ids = [(3, rejected_availability_id.program_id.id)]
            self.write({'state_evaluation': self._check_decisions()})

            # Log the action --------------------
            subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
            body = _('The project is rejected by ' + self.env.user.name + '.<br><b>Rejection reason: </b>' + rejected_availability_id.reason)
            self.message_post(body=Markup(body), subtype_id=subtype_id.id)

            # Send the email --------------------
            subtype_id = self.env.ref('student.student_message_subtype_email')
            template = self.env.ref('student.email_template_project_rejection')
            template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
            # -----------------------------------

            # Construct the message that is to be sent to the user
            message_text = f'<strong>Project Proposal Rejected</strong><p> ' + self.env.user.name + ' has rejected your project «' + self.name + '».</p><p>You can check the <b>project log</b> to learn about the reason.</p>'

            # Use the send_message utility function to send the message
            self.env['student.utils'].send_message('project', Markup(message_text), self.professor_account, self.env.user, (str(self.id),str(self.name)))

            return self.env['student.utils'].message_display('Rejection', 'The project is rejected.', False)
        else:
            raise UserError("This project cannot be processed. Please contact the administrator.")
    
    def action_view_project_return(self, returned_availability_id):
        if self.state_evaluation == "progress":     
            self.returned_program_ids = [(4, returned_availability_id.program_id.id)]
            self.pending_program_ids = [(3, returned_availability_id.program_id.id)]
            if self._check_decisions() == 'draft':
                self.action_view_project_cancel(True)
            else:
                self.write({'state_evaluation': self._check_decisions()})

                # Log the action --------------------
                subtype_id = self.env.ref('student.student_message_subtype_professor_supervisor')
                body = _('The project is returned by ' + self.env.user.name + ' for the reason below. Resubmission after applying requested modifications is possible.<br><b>Return reason: </b>' + returned_availability_id.reason)
                self.message_post(body=Markup(body), subtype_id=subtype_id.id)

                # Send the email --------------------
                subtype_id = self.env.ref('student.student_message_subtype_email')
                template = self.env.ref('student.email_template_project_return')
                template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
                # -----------------------------------

                # Construct the message that is to be sent to the user
                message_text = f'<strong>Project Proposal Returned</strong><p> ' + self.env.user.name + ' has returned your proposal "' + self.name + '".</p><p>You can check the <b>Supervisor Feedback</b> section on the project page to learn about the reason. After making necessary changes, you can resubmit the project.</p>'

                # Use the send_message utility function to send the message
                self.env['student.utils'].send_message('project', Markup(message_text), self.professor_account, self.env.user, (str(self.id),str(self.name)))

                return self.env['student.utils'].message_display('Return', 'The project is returned.', False)
            
    def action_view_project_complete(self):
        if self.project_report_file and self.plagiarism_check_file and self.professor_review_file:
            self.state_publication = 'completed'
        else:
            raise ValidationError("Project report, plagiarism check and professor's review file required to complete the project.")

    # The reset button functionality for development purposes
    def action_view_project_reset(self):
        self.state_evaluation = "draft"
        self.state_publication = "ineligible"

        self.student_elected = None
        self.student_elected.current_project = None
        self.reason = ""

        # Reset all project availabilities
        project_availabilities = self.env['student.availability'].search([('project_id', '=', self.id)])
        for availability in project_availabilities:
            availability.state = "waiting"

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
            elif student_record.degree.id in self.env['student.availability'].search([('project_id','=',self.id),
                                                                                   ('program_id','=',student_record.student_program.id), 
                                                                                   ('state','=','approved')]).degree_ids.ids:
                self.ensure_one()
                
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Create Application',
                    'res_model': 'student.application',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {
                        'default_project_id': self.id
                    }
                }
            else:
                raise UserError("This project is not applicable for your level of education, please use filters to find another one.")
    
    # Navigates to events of this project
    def action_view_project_events(self):
        action = self.env.ref('student.action_open_project_tasks').read()[0]
        action['context'] = {'default_project_id': self.project_project_id.id}
        action['domain'] = [('project_id', '=', self.project_project_id.id)]
        return action

    project_project_tasks = fields.One2many('project.task', compute="_compute_project_project_tasks")
    project_project_id = fields.Many2one('project.project', string="Odoo Project")
    # Creates the project.project for student.project
    def create_project_project(self):
        self.project_project_id = self.env['project.project'].create({
            'name': self.name,
            'privacy_visibility': 'followers'
        }).id

        student_follower = self.env['mail.followers'].create({
            'res_model': "project.project",
            'partner_id': self.student_elected.student_account.partner_id.id,
            'res_id': self.project_project_id.id,
            'subtype_ids': self.env['mail.message.subtype'].search([('id', '=', 1)])
        }).id

        professor_follower = self.env['mail.followers'].create({
            'res_model': "project.project",
            'partner_id': self.professor_account.partner_id.id,
            'res_id': self.project_project_id.id,
            'subtype_ids': self.env['mail.message.subtype'].search([('id', '=', 1)])
        }).id

        # Create stages
        stages_data = [
            {'name': 'Backlog', 'sequence': 10, 'fold': False},
            {'name': 'In Progress', 'sequence': 20, 'fold': False},
            {'name': 'Complete', 'sequence': 30, 'fold': False},
            {'name': 'Approved', 'sequence': 40, 'fold': False},
            {'name': 'Canceled', 'sequence': 50, 'fold': True}
        ]
        stages = self.env['project.task.type'].create(stages_data)

        self.project_project_id.write({'type_ids': [(6, 0, stages.ids)]})
        self.project_project_id.message_follower_ids = [student_follower, professor_follower]

    def _compute_project_project_tasks(self):
        self.project_project_tasks = self.env['project.project'].sudo().browse(self.project_project_id.id).tasks