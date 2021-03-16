# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 15 Mar 2021

@author: mboscolo
'''
from openerp.tools.translate import _
from osv import osv, fields
import os
import logging
import datetime
import base64
import shutil
import tempfile
from datetime import timedelta
from omnia_docfly_utils import generatePDVFile
from omnia_docfly_utils import generatePDV
from omnia_docfly_utils import FTPTLS
from openerp import SUPERUSER_ID


class FatturaPAExportConservation(osv.osv):
    _name = 'fatturapa.exportconservation'
    
    _columns = {
        'date_from':fields.date(_('Invoice Date From')),
        'date_to': fields.date(_('Invoice Date To')),
        'pdv_name': fields.char(_('Nome PDV'),
                                help='Nome Contenitore conservazione sostitutiva base'),
        'fatturapa_out_ids': fields.many2many('account.invoice',
                                             'cons_out_id',
                                             'invoice_out_id',
                                             string='Fatture Clienti esportate'),
        'fatturapa_in_ids': fields.many2many('account.invoice',
                                            'cons_in_id',
                                            'invoice_in_id',
                                            string='Fatture Fornitori esportate'),
    }
    
    def onChangeDates(self, cr, uid, ids, date_from, date_to, context=None):
        result = {'value': {
                'pdv_name': "PDV_%s_%s" % (date_from or '', date_to or ''),
                }
            }
        return result
    
    def getInvoices(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context):
            out_ivoice_ids = self.pool['account.invoice'].search(cr, uid, [('date_invoice', '>=', item.date_from ),
                                                               ('date_invoice', '<=', item.date_to ),
                                                               ('type', 'in', ('out_invoice', 'out_refund'))])
                
            in_ivoice_ids = self.pool['account.invoice'].search(cr, uid, [('date_invoice', '>=', item.date_from ),
                                                                ('date_invoice', '<=', item.date_to ),
                                                                ('type', 'in', ( 'in_invoice', 'in_refund'))])
            item.write({
                'fatturapa_out_ids': [(6, 0, out_ivoice_ids)],
                'fatturapa_in_ids': [(6, 0, in_ivoice_ids)],
                })
    
    def put_to_docfly(self, cr, uid, ids, context=None):
        config_pool = self.pool['ir.config_parameter']
        ftp_session = FTPTLS() 
        ftp_session.connect(host=config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_FTP_URL'),
                            port=990,
                            timeout=5)
        try:
            ftp_session.login(user=config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_FTP_USER'),
                              passwd=config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_FTP_PWS'))
        except Exception as ex:
            return {'name': ('Setup FTP login credentials'),
                    'context': context,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'fatturapa.exportconservationparams',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
            }
        ftp_session.prot_p()
        ftp_session.codice_fiscale = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_CODICE_FISCALE')
        
        def mark_and_push(pdv_name,
                          temporary_folder, 
                          invoices):
            files = ''
            for invoice in invoices:
                if invoice.fatturapa_attachment_in_id:
                    in_xml_invoice = invoice.fatturapa_attachment_in_id
                    file_path = os.path.join(temporary_folder,
                                             in_xml_invoice.name)
                    with open(file_path, 'w') as fobj:
                        fobj.write(base64.b64decode(in_xml_invoice.datas))
                    files+=generatePDVFile(pdv_name, file_path)
                    ftp_session.push_to_aruba(pdv_name,
                                              file_path)
                else:
                    raise osv.except_osv(_('Configuration Error!'),
                        _("Unable to get the e-invoice from invoice %s" % invoice.number))
            pdv_path = generatePDV(temporary_folder, pdv_name, files)
            ftp_session.push_to_aruba(pdv_name,
                                      pdv_path)

        for item in self.browse(cr, uid, ids, context):
            temporary_folder = tempfile.mkdtemp()
            in_invoice_pdv =  "%s_in" % item.pdv_name
            mark_and_push(in_invoice_pdv,
                          temporary_folder,
                          item.fatturapa_in_ids)
            
            out_invoice_pdv =  "%s_out" % item.pdv_name
            mark_and_push(out_invoice_pdv,
                          temporary_folder,
                          item.fatturapa_out_ids)
            shutil.rmtree(temporary_folder)
        ftp_session.quit()
