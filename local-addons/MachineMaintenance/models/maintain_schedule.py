"""MAINTAIN SCHEDULE MODEL"""
from odoo import fields, api, models


class MaintainSchedule(models.Model):
    _name = "maintain.schedule"
    _description = "Maintain Schedule"

    name = fields.Char(string="Name", required=True, default="New Schedule")
    machine_id = fields.Many2one('maintenance.equipment', string='Machine', required=True)

