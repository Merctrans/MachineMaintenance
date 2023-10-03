import logging
from datetime import timedelta
from odoo import models, fields

_logger = logging.getLogger(__name__)


class MaintainSchedule(models.Model):
    _name = "maintain.schedule"
    _description = "Maintain Schedule"

    name = fields.Char(string="Name", required=True, default="New Schedule")
    machine_id = fields.Many2one('maintenance.equipment', string='Machine', required=True)
    work_order_ids = fields.Many2many('work.order', 'maintain_schedule_id', string='Work Orders',
                                      domain="[('machine_id', '=', machine_id)]")
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)

    def create_work_orders(self):
        created_count = 0
        failed_count = 0

        try:
            for schedule in self:
                work_orders = schedule.work_order_ids.sorted(key=lambda r: r.frequency)
                if not work_orders:
                    _logger.warning('No work orders found for schedule %s', schedule.name)
                    continue

                # Generate the frequency pattern
                frequencies = [wo.frequency for wo in work_orders]
                generated_frequencies = []
                while len(generated_frequencies) * 30 <= (
                        fields.Date.from_string(schedule.date_end) - fields.Date.from_string(schedule.date_start)).days:
                    for freq in frequencies:
                        generated_frequencies.extend([30] * (freq // 30))
                        generated_frequencies.append(freq)

                # Create Work Orders based on the generated frequency pattern
                for freq in generated_frequencies:
                    matching_wo = next((wo for wo in work_orders if wo.frequency == freq), None)
                    if matching_wo:
                        self._create_new_work_order(matching_wo, None)  # Date will be added later
                        created_count += 1

                # Assign dates to the Work Orders
                current_date = fields.Date.from_string(schedule.date_start)
                for wo in self.work_order_ids:
                    wo.date = fields.Date.to_string(current_date)
                    current_date += timedelta(days=30)

        except Exception as e:
            _logger.error('Error creating work orders: %s', e)
            failed_count += 1

        _logger.info('Created %d work orders with %d failures.', created_count, failed_count)

    def _create_new_work_order(self, template_wo, date):
        new_work_order = self.env['work.order'].create({
            'name': template_wo.name,
            'check_sheet_template_id': template_wo.check_sheet_template_id.id,
            'machine_id': template_wo.machine_id.id,
            'date': fields.Date.to_string(date),
            'frequency': template_wo.frequency,
            'frequency_type': template_wo.frequency_type,
            'machine_check_sheet_id': template_wo.machine_check_sheet_id.id,
        })

        self.write({'work_order_ids': [(4, new_work_order.id)]})

        # Creating entry_data_details for the new_work_order
        for entry_data_detail in template_wo.entry_data_details:
            self.env['machine.entry.data'].create({
                'machine_check_sheet_id': new_work_order.machine_check_sheet_id.id,
                'check_sheet': entry_data_detail.check_sheet.id,
                'work_detail': entry_data_detail.work_detail,
                'action': entry_data_detail.action,
                'entry_type': entry_data_detail.entry_type,
                'lcl': entry_data_detail.lcl,
                'ucl': entry_data_detail.ucl,
                'value_show': entry_data_detail.value_show,
                'result_check': entry_data_detail.result_check,
                'action_ng': entry_data_detail.action_ng,
                'value_show_after_action': entry_data_detail.value_show_after_action,
                'result_check_after_action': entry_data_detail.result_check_after_action,
                'remark': entry_data_detail.remark,
                'work_order_id': new_work_order.id,
            })