from odoo import fields, models, api
from datetime import date

class Event(models.Model):
    _name = "student.event"
    _description = "OpenLMS - Events"

    _current_date = fields.Date.today()

    common = fields.Boolean('Common event?')
    complete = fields.Boolean('Event complete?', readonly=True)

    name = fields.Char('Event Name', required=True, translate=True)
    description = fields.Text('Description', required=True)
    # tasks = 
    initiator = fields.Many2one('res.users', string='Initiated By', required=True)
    assignee = fields.Many2one('res.users', string='Assigned To', required=True)
    watchers = fields.Many2many('res.users', string='Watchers')
    creation_date = fields.Date("Creation Date", default=lambda self: fields.Datetime.now(), readonly=True)
    due_date = fields.Date("Due Date", required=True)
    related_projects = fields.Many2many('student.project', string='Related Projects')
    additional_files = fields.Many2many(comodel_name="ir.attachment", string="Attachments") 
    type = fields.Selection([('asm', 'Assignment'),('mtn', 'Meeting'),('prs', 'Presentation'),('otr', 'Other')], default='mtn', string='Event Type', required=True)

    def action_view_event_complete(self):
        self.complete = True

    # Updates the ownership of files for other users to access them
    @api.onchange('additional_files')
    def update_ownership(self):
        for attachment in self.additional_files:
            attachment.write({'res_model': self._name, 'res_id': self.id})