
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from random import randrange

import logging

_logger = logging.getLogger(__name__)

class MaintenacePlannigPlan(models.TransientModel):
    _name = 'maintenance_planning.plan.requests.wizard'
    _description = 'Plan maintenance requests'

    start_date = fields.Date('Start date', default=fields.Date.today())
    end_date = fields.Date('End date', default=fields.Date.add(fields.Date.today(), months = 1))

    def confirm_plan(self):

        equipments = self.env['maintenance.equipment'].search([])
        requests = self.env['maintenance.request']

        for equipment in equipments:
            for ops in equipment.maintenance_operation_ids:
                period = int(ops.periodicity)
                ops_number = (self.end_date - self.start_date).days // period
                if ops_number < 1 :
                        continue
                ops_type = dict(ops._fields['periodicity'].selection).get(ops.periodicity)
                for delta in range(0, ops_number):
                    schedule_date = fields.Datetime.add(self.start_date, days = period * (delta + 1))
                    request_dict = {
                            'name': equipment.display_name + " - Preventive",
                            'category_id': equipment.category_id.id,
                            'equipment_id': equipment.id,
                            'maintenance_type': 'preventive',
                            'duration': ops.maintenance_duration,
                            'maintenance_operation_id': ops.id,
                            'schedule_date': schedule_date,
                            'color': equipment.id,
                            'description': ops.name + " - " + ops_type + ' - ' + str(ops.note)
                            }
                    requests.create(request_dict)
       
        return self.env.ref("maintenance.hr_equipment_request_action_cal").read()[0]