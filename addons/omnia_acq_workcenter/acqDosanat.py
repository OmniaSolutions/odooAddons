from openerp import models, fields, api

class omnia_acq_dosanat_row(models.Model):
    _name = "acq.dosanat.row"
    name=fields.Char('Name', required=True)
    pos=fields.Char('Posizione')
    prod=fields.Char('Produzione')
    field1=fields.Char('Campo 1')
    field2=fields.Char('Campo 2')
    fieldn=fields.Char('Campo n')
    acq_dosanat_row = fields.Many2one('acq.dosanat.row', string='Row')
    
    @api.onchange('acq_dosanat_row')
    def onchange_dosanat(self):
        if self.acq_dosanat_row:
            objBrwse = self.browse(self.acq_dosanat_row.id)
            self.name = objBrwse.name
            self.field1 = objBrwse.field1
            self.field2 = objBrwse.field2
            self.fieldn = objBrwse.fieldn
            self.prod = objBrwse.prod
            self.pos = objBrwse.pos