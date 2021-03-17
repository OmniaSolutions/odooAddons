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
import zipfile
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
        'fatturapa_error_ids': fields.many2many('account.invoice',
                                            'cons_err_id',
                                            'invoice_err_id',
                                            string='Fatture senza XML'),
    }
    
    def onChangeDates(self, cr, uid, ids, date_from, date_to, context=None):
        result = {'value': {
                'pdv_name': "PDA_%s_%s" % (date_from or '', date_to or ''),
                }
            }
        return result
    
    def getInvoices(self, cr, uid, ids, context=None):
        config_pool = self.pool['ir.config_parameter']
        limit_txt = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_SEARCH_LIMIT_TEST_ONLY_DEFAULT_NONE')
        limit = None
        try:
            limit = eval(limit_txt)
        except Exception as ex:
            logging.warning('Cannot eval DOCFLY_SEARCH_LIMIT_TEST_ONLY_DEFAULT_NONE due to error %r' % (ex))
        for item in self.browse(cr, uid, ids, context):
            out_ivoice_ids = self.pool['account.invoice'].search(cr, uid, [
                ('date_invoice', '>=', item.date_from ),
                ('date_invoice', '<=', item.date_to ),
                ('type', 'in', ('out_invoice', 'out_refund')),
                ('fatturapa_attachment_out_id', 'not in', (False,)),
                ], limit=limit)
            in_ivoice_ids = self.pool['account.invoice'].search(cr, uid, [
                ('date_invoice', '>=', item.date_from ),
                ('date_invoice', '<=', item.date_to ),
                ('type', 'in', ( 'in_invoice', 'in_refund')),
                ('fatturapa_attachment_in_id', 'not in', (False,)),
                ], limit=limit)
            err_ivoice_ids = self.pool['account.invoice'].search(cr, uid, [
                ('date_invoice', '>=', item.date_from ),
                ('date_invoice', '<=', item.date_to ),
                ('type', 'in', ( 'in_invoice', 'in_refund', 'out_invoice', 'out_refund')),
                ('fatturapa_attachment_out_id', 'in', (False,)),
                ('fatturapa_attachment_in_id', 'in', (False,)),
                ])
            item.write({
                'fatturapa_out_ids': [(6, 0, out_ivoice_ids)],
                'fatturapa_in_ids': [(6, 0, in_ivoice_ids)],
                'fatturapa_error_ids': [(6, 0, err_ivoice_ids)],
                })

    def generate_local_file(self,
                          temporary_folder, 
                          in_xml_invoice,
                          inv_number):
        
        if in_xml_invoice:
            file_path = os.path.join(temporary_folder,
                                     in_xml_invoice.name)
            with open(file_path, 'w') as fobj:
                fobj.write(base64.b64decode(in_xml_invoice.datas))
            return file_path
        else:
            raise osv.except_osv(_('Configuration Error!'),
                _("Unable to get the e-invoice from invoice %s" % inv_number))
        return ''

    def upload_mode_standard(self, cr, uid, ids, ftp_session, context=None):
        config_pool = self.pool['ir.config_parameter']
        for item in self.browse(cr, uid, ids, context):
            temporary_folder = tempfile.mkdtemp()
            in_invoice_pdv =  "%s_in" % item.pdv_name
            pdv_files_in = ''
            for inv_in in item.fatturapa_in_ids:
                file_path = self.generate_local_file(temporary_folder,
                                                     inv_in.fatturapa_attachment_in_id,
                                                     inv_in.number)
                pdv_f = generatePDVFile(in_invoice_pdv, file_path)
                pdv_files_in += pdv_f
                ftp_session.push_to_aruba(in_invoice_pdv, file_path)
            purchase_key = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_PURCHASE_KEY')
            pdv_path_in = generatePDV(temporary_folder, in_invoice_pdv, pdv_files_in, purchase_key)
            ftp_session.push_to_aruba(in_invoice_pdv,
                                      pdv_path_in)
            
            pdv_files_out = ''
            out_invoice_pdv =  "%s_out" % item.pdv_name
            for inv_out in item.fatturapa_out_ids:
                file_path = self.generate_local_file(temporary_folder,
                                                     inv_out.fatturapa_attachment_out_id,
                                                     inv_out.number)
                pdv_f_out = generatePDVFile(out_invoice_pdv, file_path)
                pdv_files_out += pdv_f_out
                ftp_session.push_to_aruba(out_invoice_pdv, file_path)
            sale_key = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_SALE_KEY')
            pdv_path_out = generatePDV(temporary_folder, out_invoice_pdv, pdv_files_out, sale_key)
            ftp_session.push_to_aruba(out_invoice_pdv,
                                      pdv_path_out)
            shutil.rmtree(temporary_folder)        

    def upload_mode_zip(self, cr, uid, ids, ftp_session, context=None):
        config_pool = self.pool['ir.config_parameter']
        for item in self.browse(cr, uid, ids, context):
            # Purchase invoices
            purchase_key = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_PURCHASE_KEY')
            in_invoice_pdv =  "%s_in" % item.pdv_name
            temporary_folder = tempfile.mkdtemp()
            for inv_in in item.fatturapa_in_ids:
                file_path = self.generate_local_file(temporary_folder,
                                                     inv_in.fatturapa_attachment_in_id,
                                                     inv_in.number)
            zip_path = os.path.join(tempfile.gettempdir(), in_invoice_pdv)
            zipf = shutil.make_archive(zip_path, 'zip', temporary_folder)
            ftp_session.push_to_aruba(in_invoice_pdv, zipf)
            pdv_f = generatePDVFile(in_invoice_pdv, zipf, 'application/zip')
            pdv_path_in = generatePDV(temporary_folder, in_invoice_pdv, pdv_f, purchase_key)
            ftp_session.push_to_aruba(in_invoice_pdv, pdv_path_in)
            shutil.rmtree(temporary_folder)
            
            # Sale invoices
            sale_key = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_SALE_KEY')
            out_invoice_pdv =  "%s_out" % item.pdv_name
            temporary_folder = tempfile.mkdtemp()
            for inv_out in item.fatturapa_out_ids:
                file_path = self.generate_local_file(temporary_folder,
                                                     inv_out.fatturapa_attachment_out_id,
                                                     inv_out.number)
            zip_path = os.path.join(tempfile.gettempdir(), out_invoice_pdv)
            zipf = shutil.make_archive(zip_path, 'zip', temporary_folder)
            ftp_session.push_to_aruba(out_invoice_pdv, zipf)
            pdv_f = generatePDVFile(out_invoice_pdv, zipf, 'application/zip')
            pdv_path_out = generatePDV(temporary_folder, out_invoice_pdv, pdv_f, sale_key)
            ftp_session.push_to_aruba(out_invoice_pdv, pdv_path_out)
            shutil.rmtree(temporary_folder)
            

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
        DOCFLY_GENERATION_MODE = config_pool.get_param(cr, SUPERUSER_ID, 'DOCFLY_GENERATION_MODE')
        if not DOCFLY_GENERATION_MODE:
            DOCFLY_GENERATION_MODE = 'STANDARD'
        DOCFLY_GENERATION_MODE = DOCFLY_GENERATION_MODE.upper()
        if DOCFLY_GENERATION_MODE == 'STANDARD':
            self.upload_mode_standard(cr, uid, ids, ftp_session, context)
        if DOCFLY_GENERATION_MODE == 'ZIP':
            self.upload_mode_zip(cr, uid, ids, ftp_session, context)
        ftp_session.quit()
        return True
