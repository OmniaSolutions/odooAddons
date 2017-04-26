# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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

import logging
from openerp import models
from openerp import osv
from openerp import fields
from openerp import api
from openerp import _
import tempfile
import os
import csv
import base64

HEADERS = ['Part Number', 'Name', 'Description', 'Total Quantity', 'Quantity On Hand', 'Forecast Quantity', 'Vendor', 'Product_id/id', 'Internal Category Name',
           'Revision', 'Engineering Material', 'Engineering Surface', 'Price']

class MrpBomExtensionWizard(osv.osv.osv_memory):
    _name = 'mrp.bom_csv_wizard'
    
    download_datas = fields.Binary('Exported CSV file', attachment=True)
    datas_fname = fields.Char("New File name", required=True)
    showHeaders = fields.Boolean('Show Headers', default=True)

    def getOutInfos(self, prodBrws, qty=1, material='', surface=''):
        def evaluateVal(val):
            if not val:
                return ''
            return val.name

        resDict = prodBrws._product_available(prodBrws.id, False)
        onHand = resDict.get('qty_available', 0)
        forecast = resDict.get('virtual_available', 0)
        return [
            prodBrws.engineering_code,
            prodBrws.name,
            prodBrws.description or '',
            unicode(qty),
            unicode(onHand),  # on hand
            unicode(forecast),  # forecast
            self.getVendorInfos(prodBrws),
            unicode(prodBrws.id),
            evaluateVal(prodBrws.categ_id),
            unicode(prodBrws.engineering_revision),
            material or '',
            surface or '',
            unicode(prodBrws.list_price)
            ]

    def getVendorInfos(self, tmplBrws):
        out = ''
        for sellerBrws in tmplBrws.seller_ids:
            out = out + sellerBrws.name.name + '\n'
        return out

    @api.multi
    def createCsvFile(self):
        bomObj = self.env[self.env.context.get('active_model', '')]
        
        def getRelatedBom(lineBrws):
            bomLineType = lineBrws.type
            prodTmplBrws = lineBrws.product_id.product_tmpl_id
            foundBomBrwsList = bomObj.search([('type', '=', bomLineType),
                                              ('product_tmpl_id', '=', prodTmplBrws.id)])
            for bomBrws in foundBomBrwsList:
                return bomBrws
            return False
        
        def getBomRecursion(bomBrws2, lineQtyParent=1):
            toReturn = []
            currentLevelOutDict = {} # {prodprodid1: values}
            toDelete = []
            for bomLineBrws in bomBrws2.bom_line_ids:
                prodBrws = bomLineBrws.product_id
                prodId = prodBrws.id
                lineQty = bomLineBrws.product_qty
                bomLineType = bomLineBrws.type
                if prodId in currentLevelOutDict.keys() and bomLineType != 'phantom':
                    newQty = float(currentLevelOutDict[prodId][3]) + lineQty
                    currentLevelOutDict[prodId][3] = newQty
                    continue
                if bomBrws2.type == 'phantom':
                    lineQty = lineQtyParent * lineQty
                if bomLineType == 'phantom':
                    toDelete.append(prodId)
                currentLevelOutDict[prodId] = self.getOutInfos(prodBrws.product_tmpl_id, lineQty, prodBrws.tmp_material.name, prodBrws.tmp_surface.name)
                relBomBrws = getRelatedBom(bomLineBrws)
                if relBomBrws:
                    returnList = getBomRecursion(relBomBrws, lineQty)
                    toReturn.extend(returnList)
            for prodId in toDelete:
                if prodId in currentLevelOutDict:
                    del currentLevelOutDict[prodId]
            toReturn.extend(currentLevelOutDict.values())
            return toReturn
        
        out = []
        bomIds = self.env.context.get('active_ids', [])
        for bomBrws in bomObj.browse(bomIds):
            if self.showHeaders:
                out.append(HEADERS)
            out.extend([self.getOutInfos(bomBrws.product_tmpl_id)])
            out.extend(getBomRecursion(bomBrws))
            out.append([])
        
        csvFilePath = os.path.join(tempfile.gettempdir(), self.datas_fname)
        with open(csvFilePath, 'w') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL) # delimiter=' ', quotechar='|', 
            for row in out:
                writer.writerow(row)
        
        if not os.path.exists(csvFilePath):
            raise Exception(_('Unable to create CSV file'))
        
        content = ''
        with open(csvFilePath, 'r') as csvfileread:
            content = csvfileread.read()
        self.download_datas = base64.b64encode(content)
        return {'name': ('Export CSV Bom'),
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mrp.bom_csv_wizard',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                }

    @api.onchange('datas_fname')
    def change_datasfname(self):
        if self.datas_fname and not self.datas_fname.endswith('.csv'):
            self.datas_fname = self.datas_fname + '.csv'
    
MrpBomExtensionWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
