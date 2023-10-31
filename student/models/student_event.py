from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date

class Event(models.Model):
    _name = "student.event"
    _description = "PaLMS - Events"

    _current_date = fields.Date.today()    
    # ♦ Current user is not correctly assigned, but the main button logic works. Strange...
    _current_user = fields.Many2one('res.users', string="Current User Account")
    def _compute_current_user(self):
        self._current_user = self.env.user.id
        return self._current_user
            
    button_control = fields.Selection([('initiator', 'Initiator'),('assignee', 'Assignee'),('others', 'Others')], string='Viewing User', compute='_compute_button_control', store=False)
    @api.depends('_current_user')
    def _compute_button_control(self):
        current_user = self._compute_current_user()

        if current_user == self.initiator:
            self.button_control = "initiator"
        elif current_user == self.assignee:
            self.button_control = "assignee"
        else:
            self.button_control = "others"

    def _compute_supervisor_response(self):
        self.user_supervisor_response = self.env.user.id in self.pending_program_ids.mapped('supervisor.supervisor_account.id')

    # ♦ Common event logic is not implemented yet.
    common = fields.Boolean('Common event?')
    complete = fields.Boolean('Event complete?', default=False, readonly=True)
    progress = fields.Selection([('draft', 'Draft'),('progress', 'In progress'),('complete', 'Complete')], default='draft', string='Event Progress')

    name = fields.Char('Event Name', required=True, translate=True)
    description = fields.Text('Description', required=True)
    type = fields.Selection([('asm', 'Assignment'),('mtn', 'Meeting'),('prs', 'Presentation'),('otr', 'Other')], default='asm', string='Event Type', required=True)
    initiator = fields.Many2one('res.users', string='Initiated by', default=lambda self: self.env.user, readonly=True, required=True)

    def _set_default_assignee(self):
        return self.env['student.project'].sudo().search([('id', '=', self.env.context.get('project_id', False))], limit=1).student_elected.student_account
    
    assignee = fields.Many2one('res.users', default=_set_default_assignee, string='Assigned to', required=True)
    watchers = fields.Many2many('res.users', string='Watchers')
    creation_date = fields.Date("Creation Date", default=lambda self: fields.Datetime.now(), readonly=True)
    due_date = fields.Date("Due Date", required=True)
    completion_date = fields.Date("Completion Date", readonly=True)

    def _set_default_projects(self):
        return self.env['student.project'].sudo().search([('id', '=', self.env.context.get('project_id', False))], limit=1)
    
    related_projects = fields.Many2many('student.project', default=_set_default_projects, string='Related Projects')
    additional_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_event_additional_files_rel',
        column1='event_id',
        column2='attachment_id',
        string='Add a file for description'
    )

    outcomes = fields.Text('Outcomes')
    result_files = fields.Many2many(
        comodel_name='ir.attachment',
        relation='student_event_result_files_rel',
        column1='event_id',
        column2='attachment_id',
        string='Add a file with results'
    )

    # RESTRICTIONS #
    @api.constrains("due_date")
    def _check_due_date_past(self):
        if self.due_date < self.creation_date:
            raise UserError("You cannot specify a past due date!")
        
    @api.constrains('common', 'name', 'description', 'type', 'assignee', 'watchers', 'due_date', 'related_projects', 'additional_files')
    def _check_initiator_identity(self):
        if self.env.uid != self.initiator.id:
            raise ValidationError("Only the initiator can modify event details.")
        
    @api.constrains('outcomes', 'result_files')
    def _check_initiator_identity(self):
        if self.env.uid not in [self.initiator.id, self.assignee.id]:
            raise ValidationError("Only the assignee or initiator can modify results.")
    
    def unlink(self):
        if not self.env.user.has_group('student.group_administrator') and self.env.uid != self.initiator.id:
            raise UserError(_('Only the initiator can delete their event!'))
        return super(Event, self).unlink()

    # Computed completion status to categorize events into groups
    status = fields.Selection([
        ('progress', 'In progress'),
        ('past', 'Past Due'),
        ('late', 'Late Completion'),
		('complete', 'Complete')
    ], default='progress', string='Event Status')
    color = fields.Integer(string="Calendar Item Color", default=4, compute='_compute_color_value', store=True)

    # Updates color based on the state
    @api.depends('status')
    def _compute_color_value(self):
        if self.status == 'progress':
            self.color = 4  # Light blue
        elif self.status == 'late':
            self.color = 1  # Red
        elif self.status == 'complete':
            self.color = 10 # Green
        elif self.status == 'past':
            self.color = 9  # Fushia    

    def action_view_event_complete(self):
        if self.env.user != self.initiator and self.env.user != self.assignee:
            raise ValidationError("Only the initiator or the assignee can complete the project.")
        if not self.outcomes:
            raise ValidationError("You need to specify the achievements/outcomes of the event at least.")
        
        self.complete = True
        self.completion_date = fields.Date.today()

        # Send the email --------------------
        subtype_id = self.env.ref('student.student_message_subtype_email')
        if self.completion_date > self.due_date:
            self.status = "late"
            template = self.env.ref('student.email_template_event_late')
        else:
            self.status = "complete"
            template = self.env.ref('student.email_template_event_complete')
        template.send_mail(self.id, email_values={'email_to': self.initiator.email, 'subtype_id': subtype_id.id}, force_send=True)
        template.send_mail(self.id, 
                            email_values={'email_to': ','.join([watcher.email for watcher in self.watchers]),
                                            'subtype_id': subtype_id.id}, 
                            force_send=True)
        # -----------------------------------
		
        return self.env['student.utils'].message_display('Event Complete', 'You successfully completed the event.', False)
    
    def action_view_event_reopen(self):
        if self.env.user != self.initiator and self.env.user != self.assignee:
            raise ValidationError("Only the initiator or the assignee can reinitiate the project.")
        
        self.complete = False
        self.completion_date = None
        if fields.Date.today() > self.due_date:
            self.status = 'past'
        else:
            self.status = "progress"

        # Send the email --------------------
        subtype_id = self.env.ref('student.student_message_subtype_email')
        template = self.env.ref('student.email_template_event_reopen')
        template.send_mail(self.id, email_values={'email_to': self.assignee.email, 'subtype_id': subtype_id.id}, force_send=True)
        template.send_mail(self.id, 
                            email_values={'email_to': ','.join([watcher.email for watcher in self.watchers]),
                                            'subtype_id': subtype_id.id}, 
                            force_send=True)
        # -----------------------------------
		
        return self.env['student.utils'].message_display('Event Reopened', 'You reinitiated the event.', False)
    
    # SCHEDULED ACTIONS #
    def _update_event_status(self):
        incomplete_events = self.env['student.event'].sudo().search([('complete', '=', False)])
        for event in incomplete_events:
            if fields.Date.today() > event.due_date:
                event.status = 'past'