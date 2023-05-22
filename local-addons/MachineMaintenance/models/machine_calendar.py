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

    checksheet = fields.Many2one("check.sheet", string="Checksheet Parent")

    entry_data = fields.One2many("entry.data", "calendar_event", string="Entry")

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
        if res.checksheet.device_list:
            for device in res.checksheet:
                self.env["entry.data"].sudo().create(
                    {
                        "calendar_event": res.id,
                        "check_sheet": res.checksheet.id,
                        "work_detail": f"Work Order {res.name} for device {device.name}",
                        "device_id": device.id,
                    }
                )

        return res

    def write(self, vals):
        res = super().write(vals)
        if self.checksheet:
            for device in self.checksheet.device_list:
                record = self.env["entry.data"].search(
                    [("calendar_event", "=", self.id), ("device_id", "=", device.id)]
                )

                if not record:
                    self.env["entry.data"].sudo().create(
                        {
                            "calendar_event": self.id,
                            "check_sheet": self.checksheet.id,
                            "work_detail": f"Work Order {self.name} for device {device.name}",
                            "device_id": device.id,
                        }
                    )
        return True
