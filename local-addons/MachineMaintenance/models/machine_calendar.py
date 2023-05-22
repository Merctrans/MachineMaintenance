from odoo import models, fields, api
import logging


logger = logging.getLogger(__name__)


class MachineCalendar(models.Model):
    _inherit = ["calendar.event"]
    _description = "Work Order Calendar"

    name = fields.Char(
        string="Work Order Name",
        default="New Work Order",
        readonly=True,
        index=True,
        required=True,
        copy=False,
    )

    machine = fields.Many2one(
        "maintenance.equipment",
        string="Machine",
        compute="_compute_machine_id",
        recursive=True,
        store=True,
        readonly=False,
        precompute=True,
        index=True,
        tracking=True,
        change_default=True,
    )
    id_display = fields.Char(compute="_compute_id")
    machine_id = fields.Integer(string="Machine ID", compute="_get_machine_id")
    device_list = fields.Many2many(
        "machine.device",
        string="Device List",
    )
    checksheet = fields.Many2many("check.sheet", string="Checksheet")
    entry_data = fields.One2many("entry.data", "calendar_event", string="Entry")

    def _compute_id(self):
        for event in self:
            if event.id or event._origin.id:
                event.id_display = event._origin.id or event.id
            else:
                event.id_display = 0

    @api.depends("machine")
    def _compute_machine_id(self):
        for x in self:
            if x.machine:
                x.machine = x.machine.id

    @api.onchange("machine")
    def _get_machine_id(self):
        for record in self:
            if record.machine:
                record.machine_id = record.machine.id
            else:
                record.machine_id = 0

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code(
                    "increment_machine_calendar_number_order"
                )
                or "New"
            )
        res = super(MachineCalendar, self).create(vals)
        for sheet in res.checksheet:
            self.env["entry.data"].sudo().create(
                {
                    "calendar_event": res.id,
                    "check_sheet": sheet.id,
                    "device": sheet.device,
                }
            )

        return res

    def write(self, vals):
        res = super().write(vals)
        if self.checksheet:
            for sheet in self.checksheet:
                record = self.env["entry.data"].search(
                    [("calendar_event", "=", self.id), ("check_sheet", "=", sheet.id)]
                )

                if not record:
                    self.env["entry.data"].sudo().create(
                        {
                            "calendar_event": self.id,
                            "check_sheet": sheet.id,
                            "device": sheet.device,
                        }
                    )
        return True
