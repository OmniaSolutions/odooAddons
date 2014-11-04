from openerp import models, fields, api

class omnia_acq_miscele(models.Model):
    _name = "acq.miscele"
    name=fields.Char('Nome', required=True)
    line_ids= fields.One2many('acq.miscele.row', 'acq_miscele_rel', string = 'Righe Miscela')
    acq_vaschette_miscela = fields.Many2one('acq.vaschette', string = 'Vaschetta')
     
class omnia_acq_miscele_row(models.Model):
    _name = "acq.miscele.row"
    description=fields.Many2one('product.template', string = 'Descrizione', required = True)
    percentual=fields.Char('Percentuale',size=128)
    tAgitazione=fields.Char('T. Agit.',size=128)
    acq_miscele_rel = fields.Many2one('acq.miscele', string='Miscele Rel', invisible = 1)
    
    @api.onchange('description')
    def onchange_dosanat(self):
        if self.description:
            prodTmpltObj = self.pool.get('product.template')
            objBrwse = prodTmpltObj.browse(self.env.cr, self.env.uid, self.description.id)
            self.percentual = objBrwse.correzione
            self.tAgitazione = objBrwse.manuale