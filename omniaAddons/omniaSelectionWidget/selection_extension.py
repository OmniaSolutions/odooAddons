'''
Created on Jul 1, 2015

@author: daniel
'''

# from osv                            import osv, fields
# from openerp.tools.translate        import _
# from datetime                       import datetime,timedelta, date
# from openerp.tools                  import DEFAULT_SERVER_DATETIME_FORMAT
# import dateutil.relativedelta, calendar, json, base64
from openerp.osv                import osv, fields
import logging
_logger = logging.getLogger(__name__)

class SelExtension(osv.osv):
    _name = 'selection.extension'
    _inherit = []
    _columns = {}
    _defaults = {
                 }
SelExtension()
    
