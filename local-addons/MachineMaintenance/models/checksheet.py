"""CHECK SHEET MODELS"""
from odoo import fields, api, models


class CheckSheet(models.Model):
    _name = "check.sheet"
    _description = "Check Sheet Template"

    frequency_list = [
        ("one_month", "1 Month"),
        ("three_months", "3 Months"),
        ("six_months", "6 Months"),
        ("twelve_months", "12 Months"),
        ("trouble", "Trouble"),
        ("other", "Other"),
    ]

    code = fields.Char("Check Sheet Code", compute="_generate_check_sheet_code")
    name = fields.Char("Check Sheet Name*", required=True)
    equipment_id = fields.Many2one("maintenance.equipment", string="Equipment*")
    device_list = fields.Many2many("machine.device", string="Device List")
    department = fields.Many2one(
        "machine.department", string="Department*", required=True
    )
    factory = fields.Many2one("factory", string="Factory*", required=True)
    created_by = fields.Many2one("res.users", string="Created By*", required=True)
    create_date = fields.Datetime(readonly=True)
    number_order = fields.Char(
        string="Number Incremented",
        default=lambda self: "New",
        readonly=True,
        index=True,
        required=True,
        copy=False,
    )

    @api.model
    def create(self, vals):
        if vals.get("number_order", "New") == "New":
            vals["number_order"] = (
                    self.env["ir.sequence"].next_by_code("increment_number_order") or "New"
            )
        return super(CheckSheet, self).create(vals)

    @api.onchange("department")
    def _generate_check_sheet_code(self):
        for rec in self:
            if rec.department:
                rec.code = f"{rec.department.code}_{self.number_order}"

    """Frequency Combo Box"""
    frequency_type = fields.Selection(
        selection=frequency_list,
        string="Check sheet Frequency",
        required=True,
        default="one_month",
    )
    frequency = fields.Integer("Frequency in Days", compute="_get_frequency_days", inverse="_inverse_get_freq", store=True)

    @api.depends("frequency_type")
    @api.onchange("frequency_type")
    def _get_frequency_days(self):
        for rec in self:
            if rec.frequency_type:
                if rec.frequency_type == "one_month":
                    rec.frequency = 30
                elif rec.frequency_type == "three_months":
                    rec.frequency = 60
                elif rec.frequency_type == "six_months":
                    rec.frequency = 180
                elif rec.frequency_type == "twelve_months":
                    rec.frequency = 360
                else:
                    rec.frequency = 0

    def _inverse_get_freq(self):
        return

    entry_data = fields.One2many("entry.data", "check_sheet", string="Entry Data")


class EntryData(models.Model):
    _name = "entry.data"
    _description = "Data Entry for Check sheet"

    check_sheet = fields.Many2one("check.sheet", string="Check Sheet")
    device_id = fields.Many2one("machine.device", string="Device")
    calendar_event = fields.Many2one("calendar.event", string="Work Order")
    work_detail = fields.Char("Detailed Work", required=True)
    action = fields.Selection(
        selection=[
            ("check", "Check"),
            ("check_and_replace", "Check/Replace"),
            ("check_and_adjust", "Check/Adjust"),
        ],
        string="Action",
        required=True,
        default="check",
    )
    entry_type = fields.Selection(selection=[("number", "Number"), ("text", "Text")])

    lcl = fields.Float(string="LCL", default=0.0)
    ucl = fields.Float(string="UCL", default=0.0)
    value_show = fields.Char(string="Value Show")
    result_check = fields.Selection(
        selection=[("ok", "OK"), ("ng", "NG")],
        default="ok",
        compute="_auto_judgement",
        inverse="_inverse_compute",
        store=True
    )

    """Auto Judgement"""

    @api.depends("ucl", "lcl")
    @api.onchange("ucl", "lcl", "value_show")
    def _auto_judgement(self):
        for rec in self:
            if rec.entry_type == "number":
                if float(rec.value_show) < rec.lcl or float(rec.value_show) > rec.ucl:
                    rec.update({"result_check": "ng"})
                else:
                    rec.update({"result_check": "ok"})
            if rec.entry_type == "text":
                return

    def _inverse_compute(self):
        return

    action_ng = fields.Char(string="Action when NG")
    value_show_after_action = fields.Char(string="Value Showed After Action")
    result_check_after_action = fields.Selection(
        selection=[("ok", "OK"), ("ng", "NG")],
        default="ok",
        compute="_auto_judgement_after_action",
        inverse="_inverse_compute_after_action",
    )
    image = fields.Image(string="Image", stored=True, max_width=1024, max_height=1024, verify_resolution=False)

    """Auto Judgement after action"""

    @api.depends("ucl", "lcl")
    @api.onchange("ucl", "lcl", "value_show_after_action")
    def _auto_judgement_after_action(self):
        for rec in self:
            if rec.entry_type == "number":
                if (
                        float(rec.value_show_after_action) < rec.lcl
                        or float(rec.value_show_after_action) > rec.ucl
                ):
                    rec.update({"result_check_after_action": "ng"})
                else:
                    rec.update({"result_check_after_action": "ok"})
            if rec.entry_type == "text":
                return

    def _inverse_compute_after_action(self):
        return

    remark = fields.Char(string="Remark")
