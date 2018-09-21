'''
Created on Sep 17, 2018

@author: daniel
'''
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _
from datetime import datetime
from odoo.exceptions import UserError
import tempfile
import os
import csv
import base64
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class WarehouseJournal(models.TransientModel):
    _name = 'warehouse.journal'

    @api.model
    def _default_date_format(self):
        langBrws = self.env['res.lang'].search([('code', '=', self.env.user.lang)])
        if langBrws:
            return langBrws.date_format
        return DEFAULT_SERVER_DATE_FORMAT

    data_file = fields.Binary(string=_('Out File'))
    data_file_name = fields.Char(string=_('Out File Name'), default="WarehouseJournal.csv")
    last_row_counter = fields.Integer(string=_('Last Row Number'), default=0)
    date_from = fields.Date(string=_('Date From'))
    date_to = fields.Date(string=_('Date To'))
    quote_char = fields.Char(_('File Quote Char'), default="|")
    delimiter = fields.Char(_('File Delimiter'), default=";")
    datetimeFormat = fields.Char(_('Datetime format'), default=_default_date_format, help="Default Odoo datetime format %r" % (DEFAULT_SERVER_DATETIME_FORMAT))

    def convertOdooDT(self, strDatetime, dtFormat):
        if not strDatetime:
            return ''
        odooDT = datetime.strptime(strDatetime, DEFAULT_SERVER_DATETIME_FORMAT)
        return datetime.strftime(odooDT, dtFormat)

    def convertOdooDate(self, strDatetime, dtFormat):
        if not strDatetime:
            return ''
        return self.convertOdooDT(strDatetime + ' 00:00:00', dtFormat)

    @api.model
    def getExportRow(self, counter, moveLine):
        operationType = moveLine.picking_id.picking_type_id.code
        addQty = 0
        minusQty = 0
        resQty = moveLine.qty_done
        if operationType == 'incoming':
            addQty = resQty
        elif operationType == 'outgoing':
            minusQty = resQty
        else:
            return []
        return self.getRowVals(counter, moveLine, addQty, minusQty)
            
    @api.model
    def getRowVals(self, counter, moveLine, addQty, minusQty):
        return [
            str(counter),   #N.RIGA
            self.convertOdooDT(moveLine.date, self.datetimeFormat) or '',  # DATA REG
            moveLine.picking_id.ddt_number or '',   # N.DOC
            self.convertOdooDate(moveLine.picking_id.ddt_date, self.datetimeFormat) or '',    # DATA DOC
            moveLine.picking_id.note_ddt or '', # DESCRIZ. DEL MOVIMENTO
            moveLine.product_id.default_code or '',   # ARTICOLO
            moveLine.product_id.name or '',   # DESCRIZIONE
            moveLine.product_uom_id.name or '',   # UM
            str(addQty), # CARICO
            str(minusQty),   # SCARICO
            moveLine.location_id.name,
            moveLine.location_dest_id.name
            ]

    @api.model
    def getExportHeaders(self):
        return ['N.RIGA', 'DATA REG.', 'N.DOC.', 'DATA DOC.', 'DESCRIZ. DEL MOV.',
                  'ARTICOLO', 'DESCRIZIONE', 'UM', 'CARICO', 'SCARICO', 'LOCATION FROM', 'LOCATION TO']
        
    @api.multi
    def generate_report(self):
        if self.date_from > self.date_to or self.date_to < self.date_from:
            raise UserError(_('Date range is inconsistent.'))
        stockMoveLineObj = self.env['stock.move.line']
        counter = self.last_row_counter + 1
        
        moveLines = stockMoveLineObj.search([
            ('date', '>=', str(self.date_from)),
            ('date', '<=', str(self.date_to)),
            ('state', '=', 'done')
            ], order='date ASC')
        filePath = os.path.join(tempfile.gettempdir(), 'tmp_journal.csv')
        if os.path.exists(filePath):
            os.unlink(filePath)
        header = self.getExportHeaders()
        with open(filePath, 'w') as outFileObj:
            spamwriter = csv.writer(outFileObj, delimiter=self.delimiter,
                        quotechar=self.quote_char, quoting=csv.QUOTE_ALL)
            spamwriter.writerow(header)
            for moveLine in moveLines:
                listRow = self.getExportRow(counter, moveLine)
                if not listRow:
                    continue
                spamwriter.writerow(listRow)
                counter = counter + 1
        with open(filePath, 'rb') as outFileObjr:
            self.data_file = base64.b64encode(outFileObjr.read())
        return {'view_type': 'form',
                'res_model': self._name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',    
                'res_id': self.id,
                }

