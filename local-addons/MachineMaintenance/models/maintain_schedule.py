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

                # Set the date for the first initial work order equal to the date_start of the schedule
                first_work_order = work_orders[0]
                first_work_order.date = schedule.date_start
                next_dates = {first_work_order: fields.Date.from_string(schedule.date_start)}

                # Calculate the dates for the subsequent initial work orders based on the difference in frequency
                for i in range(1, len(work_orders)):
                    delta_days = work_orders[i].frequency - work_orders[i - 1].frequency
                    next_date = fields.Date.from_string(work_orders[i - 1].date) + timedelta(days=delta_days)
                    work_orders[i].date = fields.Date.to_string(next_date)
                    next_dates[work_orders[i]] = next_date

                min_frequency = min(wo.frequency for wo in work_orders)  # smallest frequency among initial work orders

                while True:
                    # Find the minimum next_date and corresponding work_order to process next
                    next_work_order, next_date = min(((wo, date) for wo, date in next_dates.items()),
                                                     key=lambda x: x[1])

                    if next_date > fields.Date.from_string(schedule.date_end):
                        break

                    new_date = next_date + timedelta(
                        days=min_frequency)  # use the smallest frequency to calculate the new_date

                    # Check if the new_date is already taken by another work order, if so, adjust it to the next available date
                    existing_dates = [fields.Date.from_string(wo.date) for wo in schedule.work_order_ids]
                    while new_date in existing_dates:
                        new_date += timedelta(days=1)

                    new_work_order = self.env['work.order'].create({
                        'name': next_work_order.name,
                        'check_sheet_template_id': next_work_order.check_sheet_template_id.id,
                        'machine_id': next_work_order.machine_id.id,
                        'date': fields.Date.to_string(new_date),
                        'frequency': next_work_order.frequency,  # inherit the frequency from the original work order
                        'frequency_type': next_work_order.frequency_type,
                        'machine_check_sheet_id': next_work_order.machine_check_sheet_id.id,
                    })

                    _logger.info('Created new work order %s with date %s and frequency %d',
                                 new_work_order.name, new_work_order.date, new_work_order.frequency)

                    self.write({'work_order_ids': [(4, new_work_order.id)]})

                    # Creating entry_data_details for the new_work_order
                    for entry_data_detail in next_work_order.entry_data_details:
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

                    next_dates[next_work_order] = new_date
                    created_count += 1

        except Exception as e:
            _logger.error('Error creating work orders: %s', e)
            failed_count += 1

        _logger.info('Created %d work orders with %d failures.', created_count, failed_count)

