# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class MaintenanceOperation(models.Model):
    _name = 'maintenance_planning.operation'
    _description = 'Maintenance operation'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    maintenance_duration = fields.Float(help="Maintenance Duration in hours.")

    periodicity = fields.Selection([('7', 'Week'), ('15', '2 Weeks'), ('30', 'Month'), 
                                    ('60', 'Two months'), ('90', 'Three months'), 
                                    ('180', 'Six months'),('365', 'Year')], 
                                    string='Periodicity', required=True)

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment',
                                   ondelete='cascade', index=True, required=True)

    # required_material_ids = fields.One2many('maintenance_planning.required_material', 
    #                                         'operation_id', ondelete='cascade',
    #                                          help='Required material for maintenance operation')

    note = fields.Text('Note')


class MaintenancePlanningEquipement(models.Model):
    _inherit = 'maintenance.equipment'

    maintenance_operation_ids = fields.One2many('maintenance_planning.operation', 
                                        'equipment_id', ondelete='cascade',
                                        help='Related maintenance operation')
    

class MaintenanceRequestMaterialLine(models.Model):
    _name = 'maintenance_planning.required_material'
    _description = 'Required material for maintenance'

    
    sequence = fields.Integer(string='Sequence', default=10)
    request_id = fields.Many2one('maintenance.request', string='Request',
                                ondelete='cascade', index=True)

    product_id = fields.Many2one('product.product', 'Material',
                                domain="[('type', 'in', ['product', 'consu'])]", 
                                required=True)

    qty_required = fields.Integer('Quantity')
    comment = fields.Char('Comment') 

    qty_available_today = fields.Float(compute='_compute_qty_at_date')
    forecasted_issue = fields.Boolean(compute='_compute_qty_at_date')

    @api.depends('product_id', 'qty_required')
    def _compute_qty_at_date(self):
        for line in self:
            line.qty_available_today = line.product_id.qty_available - line.qty_required
            line.forecasted_issue = True if line.qty_available_today <= 0 else False

class MaintenancePlanningRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_operation_id = fields.Many2one('maintenance_planning.operation', 'Operation',
                                        help='Related maintenance operation')
        
    required_material_ids = fields.One2many('maintenance_planning.required_material', 
                                            'request_id', ondelete='cascade',
                                            help='Required material for maintenance operation')



