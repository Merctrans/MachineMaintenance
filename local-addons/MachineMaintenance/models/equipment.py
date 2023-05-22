from odoo import fields, api, models


# TODO: Sheet san demo data vao file xml
class Department(models.Model):
    _name = "machine.department"
    _rec_name = "code"

    name = fields.Char("Name", required=True)
    code = fields.Char("Department Code", required=True)
    active = fields.Boolean("Active", default=True)

    @api.onchange("code")
    def _onchange_code(self):
        for rec in self:
            if rec.code:
                rec.code = rec.code.upper()


# TODO: Sheet san demo data vao file xml
class Factory(models.Model):
    _name = "factory"
    _description = "Factory model"
    _rec_name = "code"

    name = fields.Char("Name", required=True)
    code = fields.Char("Factory Code", required=True)
    active = fields.Boolean("Active", default=True)

    @api.onchange("code")
    def _onchange_code(self):
        for rec in self:
            if rec.code:
                rec.code = rec.code.upper()


class MachineGroup(models.Model):
    _name = "machine.group"
    _rec_name = "mc_group_name"

    mc_group_code = fields.Char(string="Machine Group Code")
    mc_group_name = fields.Char(string="Machine Group name")
    status_flag = fields.Boolean(string="Active", default=True)


class MaintenanceDevice(models.Model):
    _name = "machine.device"
    _description = "Device used in maintenance"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True)
    purchase_order = fields.Char(string="PO", required=True)
    device_type = fields.Char(string="Type")
    serial_number = fields.Char(string="Serial Number")
    quantity = fields.Integer(string="Quantity")
    lcl = fields.Float(string="LCL", default=0.0)
    ucl = fields.Float(string="UCL", default=0.0)
    old_new = fields.Selection(
        string="Old/New", selection=[("old", "Old"), ("new", "New")]
    )
    replace = fields.Boolean(string="To be replaced", default=False)
    terminal = fields.Char(string="Terminal/IP", default="0.0.0.0")
    equipment_id = fields.Many2one("maintenance.equipment", string="Equipment")


class MachineManagement(models.Model):
    _inherit = "maintenance.equipment"

    machine_code = fields.Char(string="Machine Code")
    machine_group_id = fields.Many2one("machine.group", string="Machine Group")
    department_id = fields.Many2one("machine.department", string="Department")
    status_flag = fields.Boolean(string="Active", default=False)
    terminal_name = fields.Char(string="Terminal Name")
    device_ids = fields.One2many("machine.device", "equipment_id", string="Device List")
