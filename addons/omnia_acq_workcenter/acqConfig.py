#from openerp.osv import osv, fields
from openerp import models, fields, api
    
class omnia_acq_product(models.Model):
    _name = "product.template"
    _inherit = "product.template"
    manuale=fields.Boolean('Manuale')
    colorante=fields.Boolean('Colorante')
    correzione=fields.Boolean('Correzione')
    dosanat_row =fields.Many2many('acq.dosanat.row', 'dosanat_row_rel_prod', 'pos', 'row_id', 'Dosanat row')
    is_visible = fields.Boolean('Is Visible', default= False, invisible=True)
#     def onchange_dosanat(self, cr, uid, ids, field = None, context= None):
#         objBrwse = self.browse(cr, uid, ids, context)
#         if objBrwse.manuale or objBrwse.correzione or objBrwse.colorante:
#             self.write(cr,uid,ids[0], {'is_visible':True})
#         else:
#             self.write(cr,uid,ids[0], {'is_visible':False})
#     
     
    def write(self, cr, uid, ids, vals, context):
        super(omnia_acq_product, self).write(cr, uid, ids, vals, context)
        objBrwse = self.browse(cr, uid, ids, context)
        if objBrwse.manuale or objBrwse.correzione or objBrwse.colorante:
            return super(omnia_acq_product, self).write(cr,uid,ids, {'is_visible':True}, context=context)
        else:
            return super(omnia_acq_product, self).write(cr,uid,ids, {'is_visible':False}, context=context)
     
class omnia_acq_miscele(models.Model):
    _name = "acq.miscele"
    name=fields.Char('Nome', required=True)
    line_ids= fields.One2many('acq.miscele.row', 'acq_miscele_rel', string = 'Righe Miscela')
     
class omnia_acq_miscele_row(models.Model):
    _name = "acq.miscele.row"
    description=fields.Char('Descrizione',size=128)
    percentual=fields.Char('Percentuale',size=128)
    tAgitazione=fields.Char('T. Agit.',size=128)
    acq_miscele_rel = fields.Many2one('acq.miscele', string='Miscele Rel', invisible = 1)
     
class omnia_acq_recipes(models.Model):
    _name = "acq.recipes"
    name=fields.Char('Nome')
    category=fields.One2many('acq.category', 'acq_recipes_rel', string = 'Categoria')
    line_ids= fields.One2many('acq.recipes.row', 'recipes_rel', string = 'Righe Ricetta')
     
class omnia_acq_recipes_row(models.Model):
    _name = "acq.recipes.row"
    dur=fields.Integer('dur')
    ava=fields.Integer('ava' )
    pau=fields.Integer('pau' )
    ind=fields.Integer('ind' )
    dura=fields.Integer('dur.')
    h2o=fields.Integer('h2o')
    col=fields.Integer('col')
    scarico= fields.Selection([('nessuno', 'Nessuno'),('canaletta','Canaletta')], string = 'Scarico') 
    velocita= fields.Selection([('veloce', 'Veloce'),('lento','Lento')], string = 'Velocita')
    percentual=fields.Char(string = 'Percentuale')
    tAgitazione=fields.Char(string = 'T. Agit.')
    vaschetta1= fields.Many2one('acq.vaschette', string = 'Vaschetta 1')
    vaschetta2= fields.Many2one('acq.vaschette', string = 'Vaschetta 2')
    vaschetta3= fields.Many2one('acq.vaschette', string = 'Vaschetta 3')
    vaschetta4= fields.Many2one('acq.vaschette', string = 'Vaschetta 4')
    vaschetta5= fields.Many2one('acq.vaschette', string = 'Vaschetta 5')
    manuali= fields.One2many('acq.manuali.row', 'recipes_row_rel', string = 'Manuali')
    recipes_rel = fields.Many2one('acq.recipes', string='Recipes Rel', invisible = 1)
     
class omnia_acq_vaschette(models.Model):
    _name = "acq.vaschette"
    name=fields.Char('Nome', required=True)
    comp1=fields.Char('Comp1')
    comp2=fields.Char('Comp2')
    comp3=fields.Char('Comp3')
    comp4=fields.Char('Comp4')
    acq_recipes_row_rel = fields.Many2one('acq.recipes.row', string='Recipes Row Rel', invisible = 1)
     
class omnia_acq_manuali_row(models.Model):
    _name = "acq.manuali.row"
    recipes_row_rel = fields.Many2one('acq.recipes.row', string='Recipes Row Rel', invisible = 1)
    description=fields.Char('Descrizione', required=True)
    percentuale=fields.Char('Percentuale')
    destinazione=fields.Char('Destinazione')
    introduzione=fields.Char('Introduzione')
     
class omnia_acq_dosanat_row(models.Model):
    _name = "acq.dosanat.row"
    pos=fields.Char('Posizione', required=True)
    prod=fields.Char('Produzione')
    field1=fields.Char('Campo 1')
    field2=fields.Char('Campo 2')
    fieldn=fields.Char('Campo n')

class omnia_categoria(models.Model):
    _name = "acq.category"
    nome = fields.Char('Nome')
    field1 = fields.Char('Campo 1')
    acq_recipes_rel = fields.Many2one('acq.recipes', string='Recipes Rel', invisible = 1)