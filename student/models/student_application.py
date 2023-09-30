from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from dateutil.relativedelta import relativedelta

class Application(models.Model):
	_name = 'student.application'
	_description = 'PaLMS - Application for Project'
	_rec_name = 'applicant'
	_inherit = ['mail.thread', 'student.utils']
		
	@api.depends('applicant')
	def _compute_student_details(self):
		self.email = self.applicant.student_email
		self.phone = self.applicant.student_phone
		self.student_program = self.applicant.student_program.name
		self.student_degree = self.applicant.progress
		self.student_id = self.applicant.student_id

	# Assigns the student account created for this user
	def _default_applicant(self):
		student = self.env['student.student'].sudo().search([('student_account.id', '=', self.env.uid)], limit=1)
		self._compute_student_details()
		if student:
			return student.id 
		else: 
			raise ValidationError("Student account could not be found. Please contact the supervisor.")
	
	applicant = fields.Many2one('student.student', string='Applicant', default=_default_applicant, readonly=True, required=True)
	applicant_account= fields.Many2one('res.users', string="Applicant Account", compute='_compute_applicant_account', store=True)

	email = fields.Char('Email', compute="_compute_student_details", store=True, readonly=True)
	additional_email = fields.Char('Additional Email', required=False)
	phone = fields.Char('Phone', compute="_compute_student_details", store=True, readonly=True)
	additional_phone = fields.Char('Additional Phone', required=False)
	telegram = fields.Char('Telegram ID', required=False)
	student_program = fields.Char("Student Track", compute="_compute_student_details", store=True, readonly=True)
	student_degree = fields.Char("Academic Year", compute="_compute_student_details", store=True, readonly=True)
	student_id = fields.Char("Student ID", compute="_compute_student_details", store=True, readonly=True)

	message = fields.Text('Application Message', required=True)
	feedback = fields.Text('Professor Feedback')
	additional_files = fields.Many2many(comodel_name="ir.attachment", string="Additional Files") 

	state = fields.Selection([('draft', 'Draft'),('sent', 'Sent'),('accepted', 'Accepted'),('rejected', 'Rejected')], default='draft', readonly=True, string='Application State', store=True)
	sent_date = fields.Date(string='Sent Date')
    
    # Computed field to categorize records into groups
	urgency_category = fields.Selection([
        ('pending', 'Pending'),
        ('urgent', 'Urgent'),
        ('missed', 'Missed'),
		('handled', 'Handled')
    ], string='Urgency', compute='_compute_urgency_category', store=True)

	def _compute_urgency_category(self):
		today = fields.Date.today()
		for record in self:
			if record.state == 'accepted' or record.state == 'rejected':
				record.urgency_category = 'handled'
			elif (record.sent_date + relativedelta(days=3)) > today:
				record.urgency_category = 'pending'
			elif (record.sent_date + relativedelta(days=3)) == today:
				record.urgency_category = 'urgent'
			else:
				record.urgency_category = 'missed'

	project_id = fields.Many2one('student.project', string='Project', required=True, domain=[('state','in',['approved','applied'])])

	@api.depends('applicant')
	def _compute_applicant_account(self):
		for application in self:
			application.applicant_account = application.applicant.student_account

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

	_sql_constraints = [
        ('check_uniqueness', 'UNIQUE(applicant, project_id)', 'You have already applied to this project.')
	]

	# Handle the coloring of application
	color = fields.Integer(string="Box Color", default=4, compute='_compute_color_value', store=True)

    # Updates color based on the state
	@api.depends('state')
	def _compute_color_value(self):
		if self.state == 'draft':
			self.color = 4
		if self.state == 'sent':
			self.color = 3
		if self.state == 'accepted':
			self.color = 10
		if self.state == 'rejected':
			self.color = 9

	application_professor = fields.Many2one('res.users', string='Professor of the Applied Project', default=lambda self: self.project_id.professor_account)

	@api.constrains('feedback')
	def _feedback_control(self):
		if self.env.user.has_group('student.group_student') and self.state != 'draft':
			raise AccessError("You don't have permission to edit the feedback. Please use the log or send a message to the project creator.")

	@api.depends('project_id')
	def _check_professor(self):
		self.application_professor = self.project_id.professor_account
	
	def _check_feedback(self):
		if not self.feedback:
			raise UserError("You have to provide a reason for rejection.")
		if len(self.feedback) < 20:
			raise UserError("Please provide a more detailed feedback (at least 20 characters).")
		
	# Prevent the creation of the default log message
	@api.model
	def create(self, vals):
		application = super(Application, self.with_context(tracking_disable=True)).create(vals)

		# Customize the creation log message
		message = _("A new application has been created by %s.") % (self.env.user.name)
		application.message_post(body=message)

		return application
	    
	@api.onchange('email', 'message', 'project_id', 'additional_email', 'additional_phone', 'telegram')
	def _check_user_identity(self):
		if not self.env.user.has_group('student.group_supervisor'):
			if self.applicant_account != self.env.user:
				raise AccessError("You can only modify applications that you created. If you require assistance, contact the supervisor.")

	@api.depends('project_id.state')
	def action_view_application_send(self):
		self._check_user_identity()

		if self.state != 'draft':
			raise UserError("The application is already sent!")
		elif self.project_id.state != 'applied' and self.project_id.state != 'approved':
			raise UserError("The chosen project is not available for applications, please try another one.")
		else:
			self.write({'state': 'sent'})
			self.application_professor = self.project_id.professor_account

			# Updates the ownership of files for other users to access them
			for attachment in self.additional_files:
				attachment.write({'res_model': self._name, 'res_id': self.id})

			# Log the action --------------------
			body = _('The application is sent to the professor, %s, for evaluation.', self.project_id.professor_account.name)
			self.message_post(body=body)
            
			# Send the email --------------------
			subtype_id = self.env.ref('student.student_message_subtype_email')
			template = self.env.ref('student.email_template_application_send')
			template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
			# -----------------------------------

			# Construct the message that is to be sent to the user
			message_text = f'<strong>Application Received</strong><p> ' + self.applicant_account.name + " sent an application for " + self.project_id.name + ". Please evaluate the application.</p>"

			# Use the send_message utility function to send the message
			self.env['student.utils'].send_message('application', message_text, self.application_professor, self.applicant_account, str(self.project_id.id), str(self.id))

			self.sent_date = fields.Date.today()

			return self.message_display('Sent', 'The application is submitted for review.', False)

	def action_view_application_cancel(self):
		self._check_user_identity()

		if self.state == 'sent':
			self.write({'state': 'draft'})

			# Log the action --------------------
			body = _('The application submission is cancelled.')
			self.message_post(body=body)

			return self.message_display('Cancellation', 'The application submission is cancelled.', False)
		else:
			raise UserError("The application is already processed!")

	@api.model
	def mark_other_applications(self):
		if self.project_id and self.state == 'accepted':
			other_apps = self.env['student.application'].search([
				('project_id', '=', self.project_id.id),
				('id', '!=', self.id),
			])
			for app in other_apps:
				app.action_view_application_auto_reject()
			
	def _check_professor_identity(self):
		if not self.env.user.has_group('student.group_supervisor'):
			if self.project_id.professor_account != self.env.user:
				raise AccessError("You can only respond to the applications sent to your projects.")

	def action_view_application_accept(self):
		self._check_professor_identity()

		if self.applicant.current_project:
			raise ValidationError("This student is already assigned to another project.")

		if self.state == 'sent':
			self.write({'state': 'accepted'})
			# ♦ self.project_id.write({'state': 'assigned', 'assigned': True, 'student_elected': self.applicant})
			self.project_id.write({'state': 'assigned', 'assigned': True})

			# Log the action --------------------
			body = _('This application is accepted by the professor.')
			self.message_post(body=body)
            
			# Send the email --------------------
			subtype_id = self.env.ref('student.student_message_subtype_email')
			template = self.env.ref('student.email_template_application_accept')
			template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
			# -----------------------------------

			# Construct the message that is to be sent to the user
			message_text = f'<strong>Application Accepted</strong><p> This application submitted for <i>' + self.project_id.name + '</i> is accepted by the professor. You can contact the project professor to start working on it.</p>'

			# Use the send_message utility function to send the message
			self.env['student.utils'].send_message('application', message_text, self.applicant_account, self.application_professor, str(self.project_id.id), str(self.id))

			self.mark_other_applications()

			return self.message_display('Accepted', 'The selected application is chosen for the project, remaining ones are automatically rejected.', False)
		else:
			raise UserError("The application is already processed or still a draft!")

	def action_view_application_reject(self):
		self._check_professor_identity()

		if self.state == 'sent':
			self._check_feedback()

			self.write({'state': 'rejected'})

			# Log the action --------------------
			body = _('This application is rejected by the professor.')
			self.message_post(body=body)
            
			# Send the email --------------------
			subtype_id = self.env.ref('student.student_message_subtype_email')
			template = self.env.ref('student.email_template_application_reject')
			template.send_mail(self.id, email_values={'subtype_id': subtype_id.id}, force_send=True)
			# -----------------------------------

			# Construct the message that is to be sent to the user
			message_text = f'<strong>Application Rejected</strong><p> This application submitted for <i>' + self.project_id.name + '</i> is rejected by the professor. Please check the <b>Feedback</b> section to learn about the reason.</p>'

			# Use the send_message utility function to send the message
			self.env['student.utils'].send_message('application', message_text, self.applicant_account, self.application_professor, str(self.project_id.id), str(self.id))

			return self.message_display('Rejection', 'The application is rejected.', False)
		else:
			raise UserError("The application is already processed or still a draft!")

	def action_view_application_auto_reject(self):
		if self.state == 'sent':
			self.write({'state': 'rejected'})

			# Log the action
			body = _('This application is rejected as another one is accepted by the professor.')
			self.message_post(body=body)

			# Get the Odoo Bot user
			odoobot = self.env.ref('base.partner_root')

			# Construct the message that is to be sent to the user
			message_text = f'<strong>Application Rejected</strong><p> This application submitted for <i>' + self.project_id.name + '</i> is automatically rejected since another one is chosen by the professor.</p>'

			# Use the send_message utility function to send the message
			self.env['student.utils'].send_message('Auto Reject', message_text, self.applicant_account, odoobot, str(self.project_id.id))