from odoo import api, fields, models, _ #_ is for translations
from odoo.exceptions import UserError, ValidationError

class StudentUtils(models.AbstractModel):
    _name = 'student.utils'
    _description = 'PaLMS - Utility Methods'

    @api.model
    def send_message(context, source, message_text, recipients, author, data_tuple = -1):
        tuple_id, tuple_name = data_tuple
        
        if source == 'project':
            channel_name = "Project №" + tuple_id + " (" + tuple_name + ")"
        elif source == 'application':
            channel_name = "Applicaton №" + tuple_id + " for " + tuple_name
        elif source == 'proposal':
            channel_name = "Project Proposal №" + tuple_id + " (" + tuple_name + ")"
        else:
            channel_name = source + " №" + id

        # Search the channel to avoid duplicates
        channel = context.env['mail.channel'].sudo().search([('name', '=', channel_name)],limit=1,)

        # If no suitable channel is found, create a new channel
        if not channel:
            channel = context.env['mail.channel'].with_context(mail_create_nosubscribe=True).sudo().create({
                'channel_partner_ids': [(6, 0, author.id+1)],
                'channel_type': 'channel',
                'name': channel_name,
                'display_name': channel_name
            })

            # ♦ For some reason, I need to add 1 to all user ids. Strange...
            channel.write({
                'channel_partner_ids': [(4, recipient.id+1) for recipient in recipients]
            })

        # Send a message to the related user
        channel.sudo().message_post(
            body=message_text,
            author_id=author.id+1,
            message_type="comment",
            subtype_xmlid='mail.mt_comment'
        )

    # Displays notification messages
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

class StudentDegree(models.Model):
    _name = 'student.degree'
    _description = 'PaLMS - Degrees of Education'

    name = fields.Char('Degree Description', readonly=True, compute="_form_name", store=True)
    level = fields.Selection([('ba', "Bachelor's"),('ms', "Master's"),('phd', 'PhD')], default="ba", string='Level of Education', required=True)
    year = fields.Selection([('prep', 'Preparatory Year'), 
                             ('1', '1st Year'), 
                             ('2', '2nd Year'), 
                             ('3', '3rd Year'), 
                             ('4', '4th Year'), 
                             ('5', '5th Year'), 
                             ('6', '6th Year')], default='1', string='Academic Year', required=True)
    project_ids = fields.Many2many('student.project', string='Projects for This Degree', readonly=True)

    @api.depends('level', 'year')
    def _form_name(self):
        text_dictionary = {
            "ba": "Bachelor's",
            "ms": "Master's",
            "phd": "PhD",
            "1": "1st Year",
            "2": "2nd Year",
            "3": "3rd Year",
            "4": "4th Year",
            "5": "5th Year",
            "6": "6th Year",
            "prep": "Preparatory Year"
        }

        self.name = text_dictionary[self.level] + ' - ' + text_dictionary[self.year]

class StudentCampus(models.Model):
    _name = 'student.campus'
    _description = 'PaLMS - Campuses'

    name = fields.Char('City Name')
    university_name = fields.Char('University Name')
    legal_address = fields.Text('Legal Address')

    faculty_id = fields.One2many('student.faculty', 'campus', string='Faculties', readonly=True)
    project_ids = fields.Many2many('student.project', string='Projects', readonly=True)

class ProjectAvailability(models.Model):
    _name = 'student.availability'
    _description = 'PaLMS - Project Availability'

    def _set_default_project(self):
        return self._context.get('project_id', False)

    project_id = fields.Many2one('student.project', string='Project', default=_set_default_project)
    state = fields.Selection([('waiting', 'Waiting for submission'),
                              ('pending', 'Pending'), 
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('returned','Returned')], default='waiting', string='State')
    program_id = fields.Many2one('student.program', string='Program', required=True)
    type = fields.Selection([('cw', 'Course Work (Курсовая работа)'), ('fqw', 'Final Qualifying Work (ВКР)')], string="Type", required=True)

    degree_ids = fields.Many2many('student.degree', string='Degree', required=True)
    degree_ids_domain = fields.Binary(string="Degree Domain", help="Dynamic domain used for degree choice.", compute="_compute_degree_ids_domain")
    @api.depends('program_id')
    def _compute_degree_ids_domain(self):
        self.degree_ids_domain = [('level', '=', self.program_id.degree)]

    reason = fields.Text(string='Return/Rejection Reason')
    
    # RESTRICTIONS #
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
    
    _sql_constraints = [
        ('check_uniqueness', 'UNIQUE(program_id, project_id)', 'You have specified duplicate target programs.')
	]

class CustomMessageSubtype(models.Model):
    _name = 'student.message.subtype'
    _description = 'Student - Message Subtype'
    _inherit = 'mail.message.subtype'

class ResUsers(models.Model):
    _inherit = 'res.users'

    faculty = fields.Many2one('student.faculty', string='Faculty', compute='_compute_faculty', store=True)

    # Distributed this operation to professor, student and supervisor models
    @api.depends('groups_id')
    def _compute_faculty(self):
        for user in self:
            self.faculty = False

            if user.has_group('student.group_supervisor'):
                self.faculty = self.env['student.faculty'].sudo().search([('supervisor_ids', 'in', user.id)], limit=1)
            elif user.has_group('student.group_professor'):
                self.faculty = self.env['student.faculty'].sudo().search([('professor_ids', 'in', user.id)], limit=1)
            elif user.has_group('student.group_student'):
                self.faculty = self.env['student.faculty'].sudo().search([('student_ids', 'in', user.id)], limit=1)