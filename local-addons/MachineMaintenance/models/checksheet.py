"""CHECK SHEET MODELS"""
from odoo import fields, api, models


class Department(models.Model):
    _name = "department"
    _description = "Department in the company"
    _rec_name = "code"

    name = fields.Char('Name', required=True)
    code = fields.Char('Department Code', required=True)
    active = fields.Boolean('Active', default=True)

    @api.onchange('code')
    def _onchange_code(self):
        """Code field to be capitalized"""
        new_code = self.code
        self.code = new_code.upper()


class Factory(models.Model):
    _name = "factory"
    _description = "Factory model"
    _rec_name = "code"

    name = fields.Char('Name', required=True)
    code = fields.Char('Factory Code', required=True)
    active = fields.Boolean('Active', default=True)

    @api.onchange('code')
    def _onchange_code(self):
        """Code field to be capitalized"""
        new_code = self.code
        self.code = new_code.upper()


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
    increment_number = fields.Integer(string='Number Incremented', default=lambda self: self.env['ir.sequence'].next_by_code('increment_your_field'))

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
