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
import os
import logging
import datetime
import base64
import shutil
import tempfile
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from omnia_docfly_utils import generatePDVFile
from omnia_docfly_utils import generatePDV
from omnia_docfly_utils import FTPTLS

class FatturaPAExportConservation(models.Model):
    _name = 'fatturapa.exportconservation'

    date_from = fields.Date(_('Invoice Date From'))
    date_to = fields.Date(_('Invoice Date To'))
    pdv_name = fields.Char(_('Nome PDV'),
                            help='Nome Contenitore conservazione sostitutiva base')
    fatturapa_out_ids = fields.Many2many('account.invoice',
                                         'cons_out_id',
                                         'invoice_out_id',
                                         string='Fatture Client esportate')
    fatturapa_in_ids = fields.Many2many('account.invoice',
                                        'cons_in_id',
                                        'invoice_in_id',
                                        string='Fatture Fornitori esportate')
    
    @api.onchange('date_from','date_to')
    def _onChangeDates(self):
        for cons in self:
            cons.pdv_name = "PDV_%s_%s" % (cons.date_from, cons.date_to)
    
    @api.multi
    def getInvoices(self):
        for item in self:
            out_ivoice_ids = self.env['account.invoice'].search([('date_invoice', '>=', item.date_from ),
                                                               ('date_invoice', '<=', item.date_to ),
                                                               ('type', 'in', ('out_invoice', 'out_refund'))]).ids
                
            in_ivoice_ids = self.env['account.invoice'].search([('date_invoice', '>=', item.date_from ),
                                                                ('date_invoice', '<=', item.date_to ),
                                                                ('type', 'in', ( 'in_invoice', 'in_refund'))]).ids

            item.fatturapa_out_ids = [(6, 0, out_ivoice_ids)] 
            item.fatturapa_in_ids = [(6, 0, in_ivoice_ids)] 
    
    
    @api.multi
    def put_to_docfly(self):
        config_pool = self.env['ir.config_parameter']
        ftp_session = FTPTLS() 
        ftp_session.connect(host=config_pool.sudo().get_param('DOCFLY_FTP_URL'),
                            port=990,
                            timeout=5)
        ftp_session.login(user=config_pool.sudo().get_param('DOCFLY_FTP_USER'),
                          passwd=config_pool.sudo().get_param('DOCFLY_FTP_PWS'))
        ftp_session.prot_p()
        ftp_session.codice_fiscale=config_pool.sudo().get_param('DOCFLY_CODICE_FISCALE')
        
        def mark_and_push(pdv_name,
                          temporary_folder, 
                          invoices):
            files = ''
            for invoice in item.fatturapa_in_ids:
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
                    raise UserError("Unable to get the e-invoice from invoice %s" % invoice.number)
            pdv_path = generatePDV(temporary_folder, pdv_name, files)
            ftp_session.push_to_aruba(pdv_name,
                                      pdv_path)

        for item in self:
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
