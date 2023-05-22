"""CHECK SHEET MODELS"""
from odoo import fields, api, models


class CheckSheet(models.Model):
    _name = "check.sheet"
    _description = "Check Sheet Template"

    frequency_list = [('one_month', '1 Month'),
                      ('three_months', '3 Months'),
                      ('six_months', '6 Months'),
                      ('twelve_months', '12 Months'),
                      ('trouble', 'Trouble'),
                      ('other', 'Other')]

    code = fields.Char('Check Sheet Code', compute="_generate_check_sheet_code")
    name = fields.Char('Check Sheet Name*', required=True)
    department = fields.Many2one('department', string='Department*', required=True)
    factory = fields.Many2one('factory', string='Factory*', required=True)
    created_by = fields.Many2one('res.users', string='Created By*', required=True)
    create_date = fields.Datetime(readonly=True)
    increment_number = fields.Integer(string='Number Incremented',
                                      default=lambda self: self.env['ir.sequence'].next_by_code('increment_your_field'))

    @api.onchange('department')
    def _generate_check_sheet_code(self):
        for rec in self:
            if rec.department:
                rec.code = f"{rec.department.code}_{self.increment_number}"

    """Frequency Combo Box"""
    frequency_type = fields.Selection(selection=frequency_list, string='Check sheet Frequency', required=True,
                                      default='one_month')
    frequency = fields.Integer('Frequency in Days', compute="_get_frequency_days")

    @api.depends('frequency_type')
    @api.onchange('frequency_type')
    def _get_frequency_days(self):
        for rec in self:
            if rec.frequency_type:
                if rec.frequency_type == 'one_month':
                    rec.frequency = 30
                elif rec.frequency_type == 'three_months':
                    rec.frequency = 60
                elif rec.frequency_type == 'six_months':
                    rec.frequency = 180
                elif rec.frequency_type == 'twelve_months':
                    rec.frequency = 360
                else:
                    rec.frequency = 0

    entry_data = fields.One2many('entry.data', 'check_sheet', string="Entry Data")
    device = fields.Many2many('maintenance.device', string='Device')


class EntryData(models.Model):
    _name = 'entry.data'
    _description = 'Data Entry for Check sheet'

    check_sheet = fields.Many2one('check.sheet', string='Check Sheet')
    work_detail = fields.Char('Detailed Work', required=True)
    action = fields.Selection(selection=[("check", "Check"),
                                         ("check_and_replace", "Check/Replace"),
                                         ("check_and_adjust", "Check/Adjust")], string='Action', required=True,
                              default='check')
    entry_type = fields.Selection(selection=[("number", "number"),
                                             ("text", "Text")])

    lcl = fields.Float(string='LCL', default=0.0)
    ucl = fields.Float(string='UCL', default=0.0)
    value_show = fields.Char(string='Value Show')
    result_check = fields.Selection(selection=[('ok', 'OK'), ('ng', 'NG')], default='ok',
                                    compute='_auto_judgement', inverse='_inverse_compute')

    """Auto Judgement"""

    def is_float(element: any) -> bool:
        # If you expect None to be passed:
        if element is None:
            return False
        try:
            float(element)
            return True
        except ValueError:
            return False

    @api.depends('ucl', 'lcl')
    @api.onchange('ucl', 'lcl', 'value_show')
    def _auto_judgement(self):
        for rec in self:
            if self.is_float(self.value_show):
                if float(self.value_show) < self.lcl or float(self.value_show) > self.ucl:
                    self.update({'result_check': 'ng'})
                else:
                    self.update({'result_check': 'ok'})
            else:
                raise ValueError("Value is not float, cannot use auto judgement")

    def _inverse_compute(self):
        return

    action_ng = fields.Char(string='Action when NG')
    value_show_after_action = fields.Char(string='Value Showed After Action')
    result_check_after_action = fields.Selection(selection=[('ok', 'OK'), ('ng', 'NG')], default='ok',
                                                 compute='_auto_judgement_after_action',
                                                 inverse='_inverse_compute_after_action')

    """Auto Judgement after action"""

    @api.depends('ucl', 'lcl')
    @api.onchange('ucl', 'lcl', 'value_show_after_action')
    def _auto_judgement_after_action(self):
        for rec in self:
            if self.is_float(self.value_show_after_action):
                if float(self.value_show_after_action) < self.lcl or float(self.value_show_after_action) > self.ucl:
                    self.update({'result_check': 'ng'})
                else:
                    self.update({'result_check': 'ok'})
            else:
                raise ValueError("Value is not float, cannot use auto judgement")

    def _inverse_compute_after_action(self):
        return
