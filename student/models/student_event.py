from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
from datetime import date

class Event(models.Model):
    _name = "student.event"
    _description = "PaLMS - Events"

    _current_date = fields.Date.today()

    # ♦ Common event logic is not implemented yet.
    common = fields.Boolean('Common event?')
    complete = fields.Boolean('Event complete?', default=False, readonly=True)

    name = fields.Char('Event Name', required=True, translate=True)
    description = fields.Text('Description', required=True)
    initiator = fields.Many2one('res.users', string='Initiated by', default=lambda self: self.env.user, readonly=True, required=True)
    assignee = fields.Many2one('res.users', string='Assigned to', required=True)
    watchers = fields.Many2many('res.users', string='Watchers')
    creation_date = fields.Date("Creation Date", default=lambda self: fields.Datetime.now(), readonly=True)
    due_date = fields.Date("Due Date", required=True)
    completion_date = fields.Date("Completion Date", readonly=True)
    related_projects = fields.Many2many('student.project', string='Related Projects')
    additional_files = fields.Many2many(comodel_name="ir.attachment", string="Attachments") 
    type = fields.Selection([('asm', 'Assignment'),('mtn', 'Meeting'),('prs', 'Presentation'),('otr', 'Other')], default='mtn', string='Event Type', required=True)
    
    # RESTRICTIONS #
    @api.constrains("due_date")
    def _check_due_date_past(self):
        if self.due_date < fields.Date.today():
            raise UserError("You cannot specify a past due date!")
        
    @api.constrains('common', 'name', 'description', 'assignee', 'due_date', 'related_projects', 'type')
    def _check_initiator_identity(self):
        if self.env.uid != self.initiator.id:
            raise ValidationError("Only the initiator can modify event details.")

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
            self.color = 4
        elif self.status == 'late':
            self.color = 3
        elif self.status == 'complete':
            self.color = 10
        elif self.status == 'past':
            self.color = 9

    # Updates the ownership of files for other users to access them
    @api.onchange('additional_files')
    def update_ownership(self):
        for attachment in self.additional_files:
            attachment.write({'res_model': self._name, 'res_id': self.id})

    def action_view_event_complete(self):
        if self.env.user != self.initiator and self.env.user != self.assignee:
            raise ValidationError("Only the initiator or the assignee can complete the project.")
        
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
        if self.env.user != self.initiator or self.env.user != self.assignee:
            raise ValidationError("Only the initiator or the assignee can reinitiate the project.")
        
        self.complete = False
        self.completion_date = None
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