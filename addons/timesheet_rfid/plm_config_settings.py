'''
Created on Jun 18, 2015

@author: daniel
'''
from osv import osv, fields
from openerp.tools.translate import _

class plm_config_settings(osv.osv):
    _name = 'plm.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
       'plm_service_id': fields.char('Register PLM module, insert your Service ID.',size=128,  help="Insert the Service ID and register your PLM module. Ask it to OmniaSolutions."),
       'activated_id': fields.char('Activated PLM client',size=128,  help="Listed activated Client."),
       'active_editor':fields.char('Client Editor Name',size=128,  help="Used Editor Name"),
       'active_node':fields.char('OS machine name',size=128,  help="Editor Machine name"),
       'active_os':fields.char('OS name',size=128,  help="Editor OS name"),
       'active_os_rel':fields.char('OS release',size=128,  help="Editor OS release"),
       'active_os_ver':fields.char('OS version',size=128,  help="Editor OS version"),
       'active_os_arch':fields.char('OS architecture',size=128,  help="Editor OS architecture"),
       'node_id':fields.char('Registered PLM client',size=128,  help="Listed registered Client."),
    }
 
    def GetServiceIds(self, cr, uid, oids, default=None, context=None):
        """
            Get all Service Ids registered.
        """
        ids=[]
        partIds=self.search(cr,uid,[('activated_id','=',False)],context=context)
        for part in self.browse(cr, uid, partIds):
            ids.append(part.plm_service_id)
        return list(set(ids))
 
    def RegisterActiveId(self, cr, uid, vals, default=None, context=None):
        """
            Get all Service Ids registered.  [serviceID, activation, activeEditor, (system, node, release, version, machine, processor) ]
        """
        defaults={}
        serviceID, activation, activeEditor, platformData, nodeId=vals
        if activation:
            defaults['plm_service_id']=serviceID
            defaults['activated_id']=activation
            defaults['active_editor']=activeEditor
            defaults['active_os']=platformData[0]
            defaults['active_node']=platformData[1]
            defaults['active_os_rel']=platformData[2]
            defaults['active_os_ver']=platformData[3]
            defaults['active_os_arch']=platformData[4]
            defaults['node_id']=nodeId
    
            partIds=self.search(cr,uid,[('plm_service_id','=',serviceID),('activated_id','=',activation)],context=context)
    
            if partIds:
                for partId  in partIds:
                    self.write(cr, uid, [partId], defaults, context=context)
                    return False
            
            self.create(cr, uid, defaults, context=context)
        return False
   
    def GetActiveServiceId(self, cr, uid, vals, default=None, context=None):
        """
            Get all Service Ids registered.  [serviceID, activation, activeEditor, (system, node, release, version, machine, processor) ]
        """
        results=[]
        nodeId, activation, activeEditor, platformData =vals

        partIds=self.search(cr,uid,[('node_id','=',nodeId),('activated_id','=',activation)],context=context)

        for partId  in self.browse(cr, uid, partIds):
            results.append(partId.plm_service_id)
            
        return results

plm_config_settings()