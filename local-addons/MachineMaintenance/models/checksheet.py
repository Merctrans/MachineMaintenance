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

    code = fields.Char("Check Sheet Code", required=True)
    name = fields.Char("Check Sheet Name*", required=True)
    created_by = fields.Many2one("res.users", string="Created By*", required=True, default=lambda self: self.env.user)
    create_date = fields.Datetime(readonly=True, default=fields.Datetime.now)
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

    """Frequency Combo Box"""
    frequency_type = fields.Selection(
        selection=frequency_list,
        string="Check sheet Frequency",
        required=True,
        default="one_month",
    )
    frequency = fields.Integer("Frequency in Days", compute="_get_frequency_days", inverse="_inverse_get_freq",
                               store=True)

    @api.depends("frequency_type")
    @api.onchange("frequency_type")
    def _get_frequency_days(self):
        for rec in self:
            if rec.frequency_type:
                if rec.frequency_type == "one_month":
                    rec.frequency = 30
                elif rec.frequency_type == "three_months":
                    rec.frequency = 90
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
    # device_id = fields.Many2one("machine.device", string="Device")
    # calendar_event = fields.Many2one("calendar.event", string="Work Order")
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
    work_order_id = fields.Many2one('work.order', string='Work Order')


class MachineEntryData(models.Model):
    _name = "machine.entry.data"
    _inherit = "entry.data"

    machine_check_sheet_id = fields.Many2one('machine.check.sheet', string='Machine Check Sheet')
    work_order_id = fields.Many2one('work.order', string='Work Order')

    @api.depends("ucl", "lcl", "value_show")
    @api.onchange("ucl", "lcl", "value_show")
    def _auto_judgement(self):
        super(MachineEntryData, self)._auto_judgement()  # Calling the parent class method

    @api.depends("ucl", "lcl", "value_show_after_action")
    @api.onchange("ucl", "lcl", "value_show_after_action")
    def _auto_judgement_after_action(self):
        super(MachineEntryData, self)._auto_judgement_after_action()  # Calling the parent class method


class MachineCheckSheet(models.Model):
    _name = 'machine.check.sheet'
    _rec_name = 'check_sheet_template_id'

    machine_id = fields.Many2one('maintenance.equipment', string='Machine')
    check_sheet_template_id = fields.Many2one('check.sheet', string='Check Sheet Template')
    entry_data_details = fields.One2many('machine.entry.data', compute='_compute_entry_data_details', readonly=False,
                                         string='Entry Data Details', ondelete='cascade')

    def unlink(self):
        # Delete related machine.entry.data records manually before deleting machine.check.sheet.
        for record in self:
            self.env['machine.entry.data'].search([('machine_check_sheet_id', '=', record.id)]).unlink()
        return super(MachineCheckSheet,
                     self).unlink()  # Call the original unlink to delete the machine.check.sheet record.


class WorkOrder(models.Model):
    _name = 'work.order'
    _description = 'Work Order'
    _rec_name = 'name'

    name = fields.Char(string='Work Order Name', default='New Work Order', index=True, required=True)
    check_sheet_template_id = fields.Many2one('check.sheet', string='Check Sheet Template')
    machine_id = fields.Many2one('maintenance.equipment', string='Machine')
    machine_check_sheet_id = fields.Many2one('machine.check.sheet', string='Machine Check Sheet')
    date = fields.Date(string='Date')
    entry_data_details = fields.One2many('machine.entry.data', 'work_order_id', string='Entry Data Details',
                                         ondelete='cascade')
    frequency_type = fields.Selection(
        selection=[("one_month", "1 Month"),
                   ("three_months", "3 Months"),
                   ("six_months", "6 Months"),
                   ("twelve_months", "12 Months"),
                   ("trouble", "Trouble"),
                   ("other", "Other")],
        string='Frequency Type',
        store=True, )

    frequency = fields.Integer("Frequency in Days", store=True)

    @api.onchange('check_sheet_template_id', 'machine_id')
    def _onchange_check_sheet_template_id(self):
        if self.check_sheet_template_id and self.machine_id:
            self.frequency_type = self.check_sheet_template_id.frequency_type
            self.frequency = self.check_sheet_template_id.frequency

            # Removing the existing entry data details from the database
            for entry_data_detail in self.entry_data_details:
                entry_data_detail.unlink()

            # Clearing the existing entry data details
            self.entry_data_details = []

            # Creating a new machine.check.sheet record
            machine_sheet = self.env['machine.check.sheet'].create({
                'machine_id': self.machine_id.id,
                'check_sheet_template_id': self.check_sheet_template_id.id,
            })

            # Fetching entry.data from the selected check_sheet_template_id
            entry_data_records = self.env['entry.data'].search([('check_sheet', '=', self.check_sheet_template_id.id)])

            # Creating new machine.entry.data records linked to this work.order
            new_entry_data_records = []
            for record in entry_data_records:
                values = {
                    'machine_check_sheet_id': machine_sheet.id,
                    'check_sheet': record.check_sheet.id,
                    'work_detail': record.work_detail,
                    'action': record.action,
                    'entry_type': record.entry_type,
                    'lcl': record.lcl,
                    'ucl': record.ucl,
                    'value_show': record.value_show,
                    'result_check': record.result_check,
                    'action_ng': record.action_ng,
                    'value_show_after_action': record.value_show_after_action,
                    'result_check_after_action': record.result_check_after_action,
                    'remark': record.remark,
                }

                entry_data_record = self.env['machine.entry.data'].create(values)
                new_entry_data_records.append((4, entry_data_record.id))

            self.entry_data_details = new_entry_data_records
            self.machine_check_sheet_id = machine_sheet.id

    def unlink(self):
        for record in self:
            if record.machine_check_sheet_id:
                record.machine_check_sheet_id.unlink()
        return super(WorkOrder, self).unlink()
