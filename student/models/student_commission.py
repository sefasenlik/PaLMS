from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class Commission(models.Model):
    _name = "student.commission"
    _description = "PaLMS - Commissions"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    viewer_member = fields.Boolean(string="The viewing user is a commission member (TECHNICAL)", compute="_compute_viewer_member")
    def _compute_viewer_member(self):
        professor_account_ids = self.professor_ids.mapped('professor_account.id')
        if self.env.user.id in professor_account_ids:
            self.viewer_member = True
        else: 
            self.viewer_member = False

	# Assigns the faculty of the manager creating this commission
    def _default_faculty(self):
        manager = self.env['student.manager'].sudo().search([('manager_account.id', '=', self.env.uid)], limit=1)
        if manager:
            return manager.manager_faculty 
        else: 
            raise ValidationError("Manager account could not be found. Please contact the system administrator.")
        
    lock = fields.Boolean(string="Commission is set (TECHNICAL)", default=False)

    def action_view_commission_lock(self):
        if not self.lock:
            self.lock = True

            for defense in self.defense_ids:
                # Set defense project commissions
                defense.project_id.commission_id = self.id
                defense.show_grades = True

                # Create grading entries 
                for professor in self.professor_ids:
                    if not self.env['student.grade'].sudo().search([('project_id', '=', defense.project_id.id), ('grading_professor', '=', professor.id)]):
                        member_grade = self.env['student.grade'].sudo().create({
                            'project_id': defense.project_id.id,
                            'grading_professor': professor.id
                        }).id

                        defense.member_grades = [(4, member_grade)]

            # Log the action --------------------
            body = _('The commission №' + str(self.commission_number) + ' is set. Commission members are free to grade projects after the defense presentations.')
            self.message_post(body=body)
            
            # Send the email --------------------
            subtype_id = self.env.ref('student.student_message_subtype_email')
            template = self.env.ref('student.email_template_commission_set')
            template.send_mail(self.id, 
                               email_values={'email_to': ','.join([professor.professor_account.email for professor in self.professor_ids]),
                                             'subtype_id': subtype_id.id}, 
                               force_send=True)
        else:
            self.lock = False
            for defense in self.defense_ids:
                defense.project_id.commission_id = False

            # Log the action --------------------
            body = _('The commission №' + str(self.commission_number) + ' is unset.')
            self.message_post(body=body)
        
    commission_number = fields.Integer(string='Commission Number', default=lambda self: len(self.env['student.commission'].sudo().search([]))+1, readonly=True)
    commission_faculty = fields.Many2one('student.faculty', default=_default_faculty, string='Faculty', required=True)
    name = fields.Char('Commission Name', compute="_compute_commission_name", store=True)
    defense_ids = fields.One2many('student.defense', 'commission_id', string='Defenses', required=True)
    commission_head = fields.Many2one('student.professor', string='Head of the Commission', required=True)
    professor_ids = fields.Many2many('student.professor', string='Commission Members', required=True)
    additional_files = fields.Many2many(comodel_name="ir.attachment", string="Additional Files") 
    
    @api.onchange("additional_files")
    def _update_additional_ownership(self):
        # Makes the files public, may implement user-specific ownership in the future
        for attachment in self.additional_files:
            attachment.write({'public': True})

    @api.depends('commission_faculty')
    def _compute_commission_name(self):
        self.name = self.commission_faculty.name + " - Commission №" + str(self.commission_number)

    meeting_type = fields.Selection([('online', 'Online'), ('offline', 'Offline')], string="Meeting Type", default='online', required=True)
    meeting_location = fields.Char('Location')
    meeting_link = fields.Char('Link')
    meeting_date = fields.Datetime('Date & Time', required=True)
    meeting_other_details = fields.Text('Other Details')

    def unlink(self):
        for record in self:
            if not record.env.user.has_group('student.group_administrator'): 
                for defense in self.defense_ids:
                    for grade in defense.member_grades:
                        if grade.project_grade:
                            raise UserError(_('It is not possible to delete graded project defenses and their commissions!'))

            record.defense_ids.unlink()
        
        return super(Commission, self).unlink()

class CommissionDefense(models.Model):
    _name = "student.defense"
    _description = "PaLMS - Commission Defenses"

    commission_id = fields.Many2one('student.commission', string='Commission', required=True)
    project_student = fields.Many2one('student.student', string='Defending Student', compute="_compute_project_student", store=True)
    project_id = fields.Many2one('student.project', string='Defense Project', required=True)
    defense_time = fields.Float(string='Defense Presentation Time', required=True)

    show_grades = fields.Boolean('Show grading section?', default=False)

    member_grades = fields.Many2many('student.grade', string='Commission Member Grades', required=True)
    final_grade = fields.Selection([('1', '1'),       
                                    ('2', '2'),
                                    ('3', '3'),
                                    ('4', '4'),
                                    ('5', '5'),
                                    ('6', '6'),
                                    ('7', '7'),  
                                    ('8', '8'),  
                                    ('9', '9'),  
                                    ('10', '10')], string='Final Commission Grade (1-10)')       
    final_grade_lock = fields.Boolean(string="Final grade can be set", default=False)
    personal_grade = fields.Selection([('1', '1'),       
                                       ('2', '2'),
                                       ('3', '3'),
                                       ('4', '4'),
                                       ('5', '5'),
                                       ('6', '6'),
                                       ('7', '7'),  
                                       ('8', '8'),  
                                       ('9', '9'),  
                                       ('10', '10')], default='5', string='Your Grade (1-10)') 
    
    def action_view_defense_grade(self):
        for grade in self.member_grades:
            if grade.grading_professor.professor_account.id == self.env.user.id:
                old_grade = grade.project_grade
                grade.project_grade = self.personal_grade

                # Check if the grading is complete when a new professor grades a defense
                self._unlock_final_grade_set()

                # Log the action --------------------
                if old_grade:
                    body = _(self.env.user.name + ' has regraded a project.')
                    self.commission_id.sudo().message_post(body=body)
                else:
                    body = _(self.env.user.name + ' has graded a project.')
                    self.commission_id.sudo().message_post(body=body)
                return         
        raise ValidationError("You are not entitled to grade this project.") 

    def _unlock_final_grade_set(self):
        member_grades_list = list()
        for grade in self.member_grades:
            if grade.project_grade:
                member_grades_list.append(int(grade.project_grade))
            else:
                # Abort if a professor hasn't graded the defense
                return          
        self.final_grade_lock = True
        self.final_grade = str(round(sum(member_grades_list)/len(member_grades_list)))  
        self._update_project_grade(True)

    @api.depends('project_id')
    def _compute_project_student(self):
        for record in self:
            if record.project_id:
                if record.project_id.student_elected:
                    record.project_student = record.project_id.student_elected
                else:
                    raise ValidationError("The chosen project is not assigned to a student.") 
            
    @api.onchange('final_grade')
    def _update_project_grade(self, auto = False):
        if self.final_grade_lock and not auto and self.env.uid != self.commission_id.commission_head.professor_account.id:
            raise ValidationError("Only the commission head can modify the final grade.") 
        else:
            self.env['student.project'].sudo().browse(self.project_id.id).grade = self.final_grade

    # RESTRICTIONS #
    _sql_constraints = [('check_uniqueness', 'UNIQUE(project_id)', 'A project defense cannot be added to multiple commissions or duplicated.')]

    def unlink(self):
        for record in self:
            if not record.env.user.has_group('student.group_administrator'): 
                for grade in self.member_grades:
                    if grade.project_grade:
                        raise UserError(_('It is not possible to delete graded project defenses!'))

            record.member_grades.unlink()
        
        return super(CommissionDefense, self).unlink()

class CommissionGrade(models.Model):
    _name = "student.grade"
    _description = "PaLMS - Commission Grades"

    project_id = fields.Many2one('student.project', string='Graded Project', required=True)
    grading_professor = fields.Many2one('student.professor', string='Grading Professor', required=True)
    project_grade = fields.Selection([('1', '1'),       
                                      ('2', '2'),
                                      ('3', '3'),
                                      ('4', '4'),
                                      ('5', '5'),
                                      ('6', '6'),
                                      ('7', '7'),  
                                      ('8', '8'),  
                                      ('9', '9'),  
                                      ('10', '10')], string='Member Grade (1-10)', readonly=False) 
    
    user_can_grade = fields.Boolean(string="Current user is the grading professor", compute='_compute_professor_account')

    def _compute_professor_account(self):
        for grade in self:
            grade.user_can_grade = True if grade.grading_professor.professor_account.id == self.env.user.id else False