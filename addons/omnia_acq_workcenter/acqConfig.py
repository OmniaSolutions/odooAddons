from openerp import models, fields, api
    
class omnia_acq_product(models.Model):
    _name = "product.template"
    _inherit = "product.template"
    manuale=fields.Boolean('Manuale')
    colorante=fields.Boolean('Colorante')
    correzione=fields.Boolean('Correzione')
    percentual=fields.Char('Percentuale',size=128)
    tAgitazione=fields.Char('T. Agit.',size=128)
    dosanat_row = fields.Many2many('acq.dosanat.row', 'acq_dosanat_row_rel_prod', 'pos', 'row_id', 'Dosanat row', copy=True)
#    is_visible = fields.Boolean('Is Visible') 
     
#     def write(self, cr, uid, ids, vals, context):
#         super(omnia_acq_product, self).write(cr, uid, ids, vals, context)
#         objBrwse = self.browse(cr, uid, ids, context)
#         if objBrwse.manuale or objBrwse.correzione or objBrwse.colorante:
#             return super(omnia_acq_product, self).write(cr,uid,ids, {'is_visible':True}, context=context)
#         else:
#             return super(omnia_acq_product, self).write(cr,uid,ids, {'is_visible':False}, context=context)
     
class omnia_mrp_routing(models.Model):
    _inherit = "mrp.routing"
    
    workcenter = fields.Many2one('mrp.workcenter', string = 'Workcenter')
    
#     def create(self, cr, uid, vals, context):
#         pass

class omnia_mrp_bom(models.Model):
    _inherit = "mrp.bom"
    
#     def create(self, cr, uid, vals, context):
#         pass
    
class omnia_acq_recipes(models.Model):
    _name = "acq.recipes"
    name=fields.Char('Nome', required = True)
    category=fields.Many2many('acq.category', 'acq_category_rel', 'field1', 'row_idd', 'Categoria')
    line_ids= fields.One2many('acq.recipes.row', 'acq_recipes_rel', string = 'Righe Ricetta', copy=True)
    #locationRel = fields.Many2one('mrp.routing.workcenter', string = 'Location')

    def write(self, cr, uid, ids, vals, context):
        return super(omnia_acq_recipes,self).write(cr,uid,ids,vals,context)
    
#     def locationChoice(self, cr, uid, ids, context=None):
#         mod_obj = self.pool.get('ir.model.data')
#         result = mod_obj.get_object_reference(cr, uid, 'omnia_acq_workcenter', 'acq_location_form_view')
#         idd = result and result[1] or False
#         if idd:
#             return {
#                   'name': 'Manuali',
#                   'view_type': 'form',
#                   "view_mode": 'form',
#                   'res_model': 'acq.location',
#                   'type': 'ir.actions.act_window',
#                   'target': 'new',
#                   }
        
    def populateMrp(self, cr, uid, ids, context=None):
        prodObj = self.pool.get('product.template')
        sequence = self.pool.get('ir.sequence')
        bomObj = self.pool.get('mrp.bom')
        bomRoutingObj = self.pool.get('mrp.routing')
        mrpProdObj = self.pool.get('mrp.production')
        
        computedName = self.browse(cr,uid,ids).name+'-'+str(sequence.get(cr,uid,'acq.recipes'))
        
        '''create product'''
        prodVals = {'name':computedName,'route_ids':[[6, False, [5]]]} #set type manufacturing
        product_id = prodObj.create(cr, uid, prodVals, context)
        
        '''create routing'''
        workcenter_lines = []
        currentObjBrws = self.browse(cr,uid,ids,context)
        i = 0
        for line in currentObjBrws.line_ids:
            def appendLine(name, i):
                #[[0, False, {'cycle_nbr': 1, 'name': 'fgfdgf', 'sequence': 0, 'note': False,'workcenter_id': 2, 'hour_nbr': 0}]]
                workcenter_lines.append([0, False, {'cycle_nbr': 1, 
                                                    'name': computedName+'-'+str(i), 
                                                    'sequence': 0, 
                                                    'note': False, 
                                                    'workcenter_id': 1, 
                                                    'hour_nbr': 0}])
                return i+1
            
            i = appendLine(line.dur, i)
            if line.vaschetta1.id:
                i = appendLine(line.vaschetta1.name, i)
            if line.vaschetta2.id:
                i = appendLine(line.vaschetta2.name, i)
            if line.vaschetta3.id:
                i = appendLine(line.vaschetta3.name, i)
            if line.vaschetta4.id:
                i = appendLine(line.vaschetta4.name, i)
            if line.vaschetta5.id:
                i = appendLine(line.vaschetta5.name, i)    
               
        routingVals = {'workcenter_lines': workcenter_lines, 
                     'code': False, 
                     'name': computedName, 
                     'company_id': 1, 
                     'workcenter': 1,   #id workcenter
                     'note': False, 
                     'active': True, 
                     'location_id': 1}  #id location
        routing_id = bomRoutingObj.create(cr, uid, routingVals, context)
        
        '''create bill of materials'''
        bomVals = {'product_rounding': 0, 
                   'property_ids': [[6, False, []]], 
                   'date_stop': False, 
                   'code': False, 
                   'name': 'vg', 
                   'product_uom': 1, 
                   'sequence': 0, 
                   'date_start': False, 
                   'bom_line_ids': [], 
                   'company_id': 1, 
                   'product_efficiency': 1, 
                   'sub_products': [], 
                   'product_tmpl_id': product_id,    #id prodotto
                   'active': True, 
                   'message_follower_ids': False, 
                   'product_qty': 1, 
                   'routing_id': routing_id, 
                   'position': False, 
                   'type': 'normal', 
                   'message_ids': False, 
                   'product_id': False}
        bom_id = bomObj.create(cr, uid, bomVals, context)
        
        '''create manufacturing order'''
        manOrdVals = {'origin': False, 
                      'product_uos_qty': 0, 
                      'location_src_id': 12, 
                      'user_id': 1, 
                      'product_uom': 1,
                      'company_id': 1, 
                      'move_lines': [], 
                      'workcenter_lines': [], 
                      'routing_id': routing_id, 
                      'priority': '1', 
                      'bom_id': bom_id, 
                      'message_follower_ids': False, 
                      'receiptRel': 1, 
                      'location_dest_id': 12, 
                      'product_qty': 1, 
                      'product_uos': False, 
                      'message_ids': False, 
                      'allow_reorder': False, 
                      'product_id': product_id,
                      'receiptRell':ids[0]}
        manOrdId = mrpProdObj.create(cr, uid, manOrdVals, context)
        
        '''<act_window name="Manda in produzione"
        res_model="mrp.production"
        src_model="acq.recipes"
        view_mode="form"
        key2="client_action_multi"
        context="{'nome': name}"
        id="acq_create_man_order_action"/>'''
        
        mod_obj =self.pool.get('ir.model.data')
        result = mod_obj.get_object_reference(cr, uid, 'mrp', 'mrp_production_form_view')
        idd = result and result[1] or False
        if idd:
            return {
                  'name': 'Manuali',
                  'view_type': 'form',
                  "view_mode": 'form',
                  'res_model': 'mrp.production',
                  'type': 'ir.actions.act_window',
                  'nodestroy': True,
                  'res_id':manOrdId,
                  }
    
class omnia_acq_recipes_row(models.Model):
    _name = "acq.recipes.row"
    dur=fields.Integer('dur', required = 1)
    velocita= fields.Selection([('veloce', 'Veloce'),('lento','Lento')], string = 'Velocita')
    ava=fields.Integer('ava' )
    pau=fields.Integer('pau' )
    ind=fields.Integer('ind' )
    scarico= fields.Selection([('nessuno', 'Nessuno'),('canaletta','Canaletta')], string = 'Scarico') 
    h2o=fields.Integer('h2o')
    temp=fields.Integer('T')
    s=fields.Integer('S%')
    col=fields.Integer('col')
    vaschetta1 = fields.Many2one('acq.vaschette', string = 'Vaschetta 1')
    vaschetta2 = fields.Many2one('acq.vaschette', string = 'Vaschetta 2')
    vaschetta3 = fields.Many2one('acq.vaschette', string = 'Vaschetta 3')
    vaschetta4 = fields.Many2one('acq.vaschette', string = 'Vaschetta 4')
    vaschetta5 = fields.Many2one('acq.vaschette', string = 'Vaschetta 5')
    manuali = fields.One2many('acq.manuali.row', 'acq_manuali_rel', string = 'Manuali')
    acq_recipes_rel = fields.Many2one('acq.recipes', string='Recipes Rel', invisible = 1)
    createdId = {}
    
    def write(self, cr, uid, ids, vals, context):
        super(omnia_acq_recipes_row,self).write(cr,uid, ids, vals,context)
    
    def compute_vaschette_action1(self, cr, uid, ids, context=None):
        return self.compute_vaschette_action_general(cr, uid, ids, context)
        
    def compute_vaschette_action2(self, cr, uid, ids, context=None):
        return self.compute_vaschette_action_general(cr, uid, ids, context)
        
    def compute_vaschette_action3(self, cr, uid, ids, context=None):
        return self.compute_vaschette_action_general(cr, uid, ids, context)
        
    def compute_vaschette_action4(self, cr, uid, ids, context=None):
        return self.compute_vaschette_action_general(cr, uid, ids, context)
        
    def compute_vaschette_action5(self, cr, uid, ids, context=None):
        return self.compute_vaschette_action_general(cr, uid, ids, context)
    
    def compute_vaschette_action_general(self, cr, uid, ids, context=None):
        '''
        <record id="acq_vaschette_action" model="ir.actions.act_window">
            <field name="name">Vaschette</field>
            <field name="type">ir.actions.act_window</field>
            <field name="res_model">acq.vaschette</field>
            <field name="view_type">form</field>
            <field name="view_mode">form</field>
            <field name="view_id" ref="acq_vaschette_form_view"/>
        </record>
        '''
        res_id = False
        button = context.get('buttonNamee',False)
        objBrws = self.browse(cr, uid, ids[0])
        context.update({'recipeId':objBrws.acq_recipes_rel.id, 'recipe_row_id':objBrws.id})
        if button:
            if button == '1':
                if objBrws.vaschetta1.id:
                    res_id = objBrws.vaschetta1.id
                    context.update({'newVaschetta':False})
            elif button == '2':
                if objBrws.vaschetta2.id:
                    res_id = objBrws.vaschetta2.id
                    context.update({'newVaschetta':False})
            elif button == '3':
                if objBrws.vaschetta3.id:
                    res_id = objBrws.vaschetta3.id
                    context.update({'newVaschetta':False})
            elif button == '4':
                if objBrws.vaschetta4.id:
                    res_id = objBrws.vaschetta4.id
                    context.update({'newVaschetta':False})
            elif button == '5':
                if objBrws.vaschetta5.id:
                    res_id = objBrws.vaschetta5.id
                    context.update({'newVaschetta':False})
            
            mod_obj =self.pool.get('ir.model.data')
            result = mod_obj.get_object_reference(cr, uid, 'omnia_acq_workcenter', 'acq_vaschette_form_view')
            idd = result and result[1] or False
            if idd:
                return {
                      'name': 'Vaschette',
                      'view_type': 'form',
                      "view_mode": 'form',
                      'res_model': 'acq.vaschette',
                      'type': 'ir.actions.act_window',
                      'nodestroy': True,
                      'res_id':res_id,
                      'context':context,
                      'target':'new',
                      }

    def compute_manuali_action(self, cr, uid, ids, context=None):
        '''        
        <record id="acq_manuali_actionn" model="ir.actions.act_window">
            <field name="name">Manuali</field>
            <field name="type">ir.actions.act_window</field>
            <field name="res_model">acq.manuali.row</field>
            <field name="view_type">form</field>
            <field name="view_mode">form</field>
            <field name="view_id" ref="acq_manuali_form_view"/>
        </record>'''
        
        #pass
        res_id = False
        objBrws = self.browse(cr, uid, ids[0])
        context.update({'recipeId':objBrws.acq_recipes_rel.id, 'recipe_row_id':objBrws.id})
        if objBrws.manuali.id:
            res_id = objBrws.manuali.id
            context.update({'newManuale':False})
        mod_obj =self.pool.get('ir.model.data')
        result = mod_obj.get_object_reference(cr, uid, 'omnia_acq_workcenter', 'acq_manuali_form_view')
        idd = result and result[1] or False
        if idd:
            return {
                  'name': 'Manuali',
                  'view_type': 'form',
                  "view_mode": 'form',
                  'res_model': 'acq.manuali.row',
                  'type': 'ir.actions.act_window',
                  'nodestroy': True,
                  'res_id':res_id,
                  'target':'new',
                  }
    
class omnia_acq_vaschette(models.Model):
    _name = "acq.vaschette"
    name=fields.Char('Nome', required=True)
    comp1=fields.Char('Comp1')
    comp2=fields.Char('Comp2')
    comp3=fields.Char('Comp3')
    comp4=fields.Char('Comp4')
    buttonName = fields.Char('Button pressed', invisible = 1)
    workcenterType = fields.Selection([('drumview', 'Drumview'),
                                  ('dosanat','Dosanat'),
                                  ('bilPolveri','Bilancia Polveri'),
                                  ('deadline','Deadline'),
                                  ('acquamat','Acquamat')
                                  ], 'Tipo Workcenter')
    
    misceleRel = fields.One2many('acq.miscele', 'acq_vaschette_miscela', string = 'Relazione Miscela', copy=True)
    
    def deleteButton(self, cr, uid, ids, context):
        button = context.get('buttonNamee',False)
        if button:
            rowId = context.get('active_id',False)
            recipesRowObj = self.pool.get('acq.recipes.row')
            newVaschetta = context.get('newVaschetta', True)
            if rowId:
                vaschettaName = 'vaschetta'+button
                '''scrive nella ricetta row'''
                recipesRowObj.write(cr,uid,rowId,{vaschettaName:False},context)
                '''elimina vaschetta'''
                self.unlink(cr, uid, ids, context)

    def saveOkButton(self, cr, uid, ids, context):
        button = context.get('buttonNamee',False)
        if button:
            rowId = context.get('recipeId',False)
            rowLineId = context.get('recipe_row_id',False)
            recipesObj = self.pool.get('acq.recipes')
            newVaschetta = context.get('newVaschetta', True)
            if rowId and rowLineId:
                vaschettaName = 'vaschetta'+button
                recipesObj.write(cr,uid,rowId,{'line_ids':[[1,rowLineId,{vaschettaName:ids[0]}]]},context)
            self.write(cr,uid,ids,{'buttonName':str(button)})
     
class omnia_acq_manuali_row(models.Model):
    _name = "acq.manuali.row"
    acq_manuali_rel = fields.Many2one('acq.recipes.row', string='Recipes Row Rel', invisible = 1)
    description=fields.Char('Descrizione', required=True)
    percentuale=fields.Char('Percentuale')
    destinazione=fields.Char('Destinazione')
    introduzione=fields.Char('Introduzione')
    
    def deleteButton(self, cr, uid, ids, context):
        button = context.get('buttonNamee',False)
        if button:
            rowId = context.get('active_id',False)
            recipesRowObj = self.pool.get('acq.recipes.row')
            newVaschetta = context.get('newVaschetta', True)
            if rowId:
                vaschettaName = 'vaschetta'+button
                '''scrive nella ricetta row'''
                recipesRowObj.write(cr,uid,rowId,{vaschettaName:False},context)
                '''elimina vaschetta'''
                self.unlink(cr, uid, ids, context)
                
    def saveOkButton(self, cr, uid, ids, context):
        rowId = context.get('recipeId',False)
        rowLineId = context.get('recipe_row_id',False)
        recipesObj = self.pool.get('acq.recipes')
        newManuale = context.get('newManuale', True)
        if rowId and rowLineId:
            recipesObj.write(cr,uid,rowId,{'line_ids':[[1,rowLineId,{'manuali':ids[0]}]]},context)
    
class omnia_categoria(models.Model):
    _name = "acq.category"
    name = fields.Char('Nome')
    field1 = fields.Char('Campo 1')
    
class omnia_mrp_production(models.Model):
    _inherit = "mrp.production"
    
    receiptRell = fields.Many2one('acq.recipes', string = 'Ricetta')
    
#     def create(self, cr, uid, vals, context):
#         pass

class omnia_mrp_routing_workcenter(models.Model):
    _inherit = "mrp.routing.workcenter"
    
    #recipesRel = fields.One2many('acq.recipes', 'acq_recipes_routing_rel', string = 'Relazione Ricetta', copy=True)
    dur=fields.Integer('dur')
    velocita= fields.Selection([('veloce', 'Veloce'),('lento','Lento')], string = 'Velocita')
    ava=fields.Integer('ava' )
    pau=fields.Integer('pau' )
    ind=fields.Integer('ind' )
    scarico= fields.Selection([('nessuno', 'Nessuno'),('canaletta','Canaletta')], string = 'Scarico') 
    h2o=fields.Integer('h2o')
    temp=fields.Integer('T')
    s=fields.Integer('S%')
    col=fields.Integer('col')
    
    '''campi vaschette'''
    #namee=fields.Char('Nome')
    comp1=fields.Char('Comp1')
    comp2=fields.Char('Comp2')
    comp3=fields.Char('Comp3')
    comp4=fields.Char('Comp4')