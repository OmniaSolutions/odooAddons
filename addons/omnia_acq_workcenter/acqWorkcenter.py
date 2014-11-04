from openerp import models, fields, api

class omnia_acq_workcenter(models.Model):
    _name = "mrp.workcenter"
    _inherit = 'mrp.workcenter'
    workcenter_type = fields.Selection([('drumview', 'Drumview'),
                                  ('dosanat','Dosanat'),
                                  ('bilPolveri','Bilancia Polveri'),
                                  ('deadline','Deadline'),
                                  ('acquamat','Acquamat')
                                  ], 'Tipo Workcenter')
    dosanat_row = fields.Many2many('acq.dosanat.row', 'acq_dosanat_row_rel', 'pos', 'row_id', 'Dosanat row', copy=True)
    
    locationRel = fields.Many2one('mrp.routing', string = 'Location')