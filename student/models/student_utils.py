from odoo import api, fields, models

class StudentUtils(models.AbstractModel):
    _name = 'student.utils'
    _description = 'OpenLMS - Utility Methods'

    @api.model
    def send_message(context, send_email, message_text, recipients, author):
        # If send_email is True, send an email to recipients!

        for recipient in recipients:
            # Find if a channel was opened for this user before
            channel = context.env['mail.channel'].sudo().search([
                ('name', '=', 'Application Notifications'),
                ('channel_partner_ids', 'in', [recipient.partner_id.id])
            ],
                limit=1,
            )

            if not channel:
                # Create a new channel
                channel = context.env['mail.channel'].with_context(mail_create_nosubscribe=True).sudo().create({
                    'channel_partner_ids': [(4, recipient.partner_id.id)],
                    'channel_type': 'chat',
                    'name': f'Application Notifications',
                    'display_name': f'Application Notifications',
                })

            # Get the current partner IDs in the channel
            partner_ids = channel.channel_partner_ids.ids

            # Add the ID of the new partner to the list
            if recipient.partner_id.id not in partner_ids:
                partner_ids.append(recipient.partner_id.id)

            # Update the channel with the new partner IDs
            channel.write({'channel_partner_ids': [(6, 0, partner_ids)]})

            # Send a message to the related user
            channel.sudo().message_post(
                body=message_text,
                author_id=author.id,
                message_type="comment",
                subtype_xmlid='mail.mt_comment'
            )

class StudentDegree(models.Model):
    _name = 'student.degree'
    _description = 'OpenLMS - Degrees of Education'

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