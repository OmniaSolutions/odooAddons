##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2020 OmniaSolutions (<https://omniasolutions.website>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Leonardo Cazziolati
# leonardo.cazziolati@omniasolutions.eu
# 04-12-2020

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import datetime
import xlwt
import tempfile
import os
import base64
import stat


class StockLifoReportWizard(models.TransientModel):

    _name = 'stock.lifo.report.wizard'
    _description = "Lifo Report wizard"
   
    def _get_default_filename(self):
        return 'stampa_dettagliata_lifo_%s.xls' % (datetime.datetime.now().year)

    product_category_ids = fields.Many2many(comodel_name='product.category', string=_("Categories"))
    product_id = fields.Many2one("product.product", _("Product"))
    year = fields.Char(_('Year'), default=datetime.datetime.now().year)
    parting = fields.Integer(string="Description max characters", default=36)
    include_zero = fields.Boolean(string='Include Zero')
    xls_filename = fields.Char(string='Filename', default=_get_default_filename)
    xls_data = fields.Binary(string='Download File')
    err_msg = fields.Html(_('Error res'))
    
    
    @api.onchange('xls_filename')
    def changeFilename(self):
        if self.xls_filename:
            if not self.xls_filename.endswith('.xls'):
                self.xls_filename += '.xls'
  
    @api.model
    def getAvailableProducts(self, category_ids, product_id):
        product_ids = self.env['product.product']
        if category_ids and not product_id:
            product_ids = product_ids.search([
                ('categ_id', 'in', category_ids.ids),
                ('type', '=', 'product')
                ])
        elif product_id:
            product_ids = product_id
        else:
            product_ids = self.env['product.product'].search([
                ('type', '=', 'product')
                ])
        return product_ids

    @api.multi
    def action_generate_report(self):
        title = xlwt.easyxf('font: bold on, height 320; borders: left thin, right thin, top thin, bottom thin; align: horiz center, vertical center')
        header = xlwt.easyxf('font: bold on, height 150; borders: left thin, right thin, top thin, bottom thin; align: horiz center')
        cell = xlwt.easyxf('font: height 150; borders: left thin, right thin, top thin, bottom thin')
        decimal = xlwt.easyxf('font: height 150; borders: left thin, right thin, top thin, bottom thin', num_format_str='0.000')
        decimal_bold = xlwt.easyxf('font: bold on, height 150; borders: left thin, right thin, top thin, bottom thin', num_format_str='0.000')
        bold = xlwt.easyxf('font: bold on, height 150')
        bold_borders = xlwt.easyxf('font: bold on, height 150; borders: left thin, right thin, top thin, bottom thin')
        
        for wizard in self:
            wizard.err_msg = ''
            err_msg = ''
            category_ids = wizard.product_category_ids
            product_id = wizard.product_id
            product_ids = self.getAvailableProducts(category_ids, product_id)
            product_ids_len = len(product_ids.ids)
            all_lifos = self.env['stock.lifo'].search([('year', '<=', wizard.year), ('product_id', 'in', product_ids.ids)])
            
            mapping_lines = {}
            for index, lifo in enumerate(all_lifos):
                if index % 500 == 0:
                    logging.info('Lines %s / %s' % (index, len(all_lifos)))
                product = lifo.product_id.id
                mapping_lines.setdefault(product, self.env['stock.lifo'])
                mapping_lines[product] += lifo

            mapping_products = {}
            for index, product_dict in enumerate(self.env['product.product'].browse(mapping_lines.keys()).read(['description', 'default_code'])):
                if index % 500 == 0:
                    logging.info('Products %s / %s' % (index, len(all_lifos)))
                mapping_products.setdefault(product_dict['id'], {})
                mapping_products[product_dict['id']] = product_dict
       
            logging.info('LIFO products to evaluate %r' % (product_ids_len))
            
            out_fname = wizard.xls_filename
            if not out_fname:
                out_fname = 'stampa_dettagliata_lifo_%s.xls' % (wizard.year)
            wizard.xls_filename = out_fname
            full_path = os.path.join(tempfile.gettempdir(), out_fname)
            if os.path.exists(full_path):
                os.chmod(full_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.unlink(full_path)
            
            wb = xlwt.Workbook() # create empty workbook object
            newsheet = wb.add_sheet('Sheet1') # sheet name can not be longer than 32 characters
            newsheet.write_merge(0,1,0,7,'Stampa Dettagliata LIFO', style=title)
            newsheet.write(2,0,'Articolo', style=header)
            newsheet.write(2,1,'Descrizione', style=header)
            newsheet.write(2,2,'Anno', style=header)
            newsheet.write(2,3,'Rim. Finale', style=header)
            newsheet.write(2,4,'Rim. Calcolata', style=header)
            newsheet.write(2,5,'Costo Medio', style=header)
            newsheet.write(2,6,'Importo', style=header)
            newsheet.write(2,7,'Subtotale', style=header)
            i=3
            total = 0
            previous_cell = None
            for index, product_id in enumerate(product_ids):
                if index % 300 == 0:
                    logging.info('[action_generate_report] %s / %s' % (index, product_ids_len))
                product_total = 0
                lines = mapping_lines.get(product_id.id, self.env['stock.lifo'])
                lines.sorted('year')
                if not lines:
                    continue
                if lines[-1].year != wizard.year:
                    msg = '[WARNING] product ID %r no lifo for selected year, skipped.'  % (product_id.id)
                    logging.info(msg)
                    err_msg += '<p>' + msg + '</p>'
                    continue
                for line in lines:
                    product_total += line.total_amount
                if product_total != 0 or (product_total == 0 and wizard.include_zero):
                    prod_dict = mapping_products.get(product_id.id, {})
                    product_description = prod_dict.get('description', '') or ''
                    default_code = prod_dict.get('default_code', '') or ''
                    desc_len = len(product_description)
                    if desc_len > wizard.parting:
                        product_description = product_description[:-(desc_len-wizard.parting)]
                    newsheet.write(i,0,default_code, style=cell)
                    newsheet.write(i,1,product_description, style=cell)
                    for j in range(1,len(lines),1):
                        newsheet.write(i+j,0,'', style=cell)
                        newsheet.write(i+j,1,'', style=cell)
                    last_year = 0
                    for line in lines:
                        last_year = line.year
                        newsheet.write(i,2,line.year, style=cell)
                        newsheet.write(i,3,line.remaining_year_qty, style=cell)
                        newsheet.write(i,4,line.computed_qty, style=cell)
                        newsheet.write(i,5,line.avg_price, style=decimal)
                        newsheet.write(i,6,line.total_amount, style=decimal)
                        i += 1
                    avg = 0
                    if product_total and line.remaining_year_qty:
                        avg = product_total/line.remaining_year_qty   
                    newsheet.write(i,1,'Valorizzazione Articolo')#, style=xlwt.easyxf('font: bold on, height 150; align: horiz right'))
                    newsheet.write(i,2,last_year, style=bold_borders)
                    newsheet.write(i,3,'', style=bold_borders)
                    newsheet.write(i,4,line.remaining_year_qty, style=bold_borders)
                    newsheet.write(i,5,avg, style=decimal_bold)
                    newsheet.write(i,6,product_total, style=decimal_bold)
                    curr_subtotal_cell = xlwt.Utils.rowcol_to_cell(i,7)
                    total_cell = xlwt.Utils.rowcol_to_cell(i,6)
                    if previous_cell:
                        newsheet.write(i,7, xlwt.Formula('SUM(%s;%s)' % (previous_cell, total_cell)), style=decimal_bold)
                    else:
                        newsheet.write(i,7, product_total, style=decimal_bold)
                    previous_cell = curr_subtotal_cell
                    total += product_total
                    i += 1
            newsheet.write(i,5,'Totale Magazzino',style=bold)
            
            if previous_cell:
                newsheet.write(i,6, xlwt.Formula('SUM(%s; 0)' % (previous_cell)))
            wb.save(full_path)
            os.chmod(full_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            with open(full_path, 'rb') as f:
                fileContent = f.read()
                if fileContent:
                    wizard.xls_data = base64.encodestring(fileContent)
            wizard.err_msg = err_msg
            return {'name': _('Stampa Report Lifo'),
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': 'stock.lifo.report.wizard',
                    'target': 'new',
                    'res_id': self.ids[0],
                    'type': 'ir.actions.act_window',
                    'domain': "[]"}
    
                
        
