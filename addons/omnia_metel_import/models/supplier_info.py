# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010-2018 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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

'''
Created on Jul 30, 2018

@author: daniel
'''

import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.addons import decimal_precision as dp
import os
import tempfile
import base64

# TODO: mettere tutte queste variabili nelle variabili di sistema in modo che il cliente possa sistemarsele da solo
LEAD_TIME = 5
MAIN_DISCOUNT = 0.6
STATO_PRODOTTO = 0
LEAD_TIME = 7
MOLTIPLICATORE_PREZZO = 1
EAN13 = '0000000000000'

UOM_DESC = {'PCE': 'Pezzi',
            'BRD': 'Cartoni',
            'BLI': 'Blister',
            'LM': 'Metri lineari',
            'PL': 'Pallet',
            'LE': 'Litri',
            'KGM': 'Chilogrammi'
}

UOM = {'PCE': 'nr',
       'BRD': '',  # 'Scatola',
       'BLI': '',
       'LM': '',  # 'mt',
       'PL': '',
       'LE': '',  # 'Litro/i',
       'KGM': '',  # 'Kg'
}

metel_listino = dict(identificazione=(0, 20),
                     azienda=(20, 3),
                     partita_iva=(23, 11),
                     listino=(34, 6),
                     data_decorrenza_pubblico=(40, 8),
                     data_variazione=(48, 8),
                     descrizione=(56, 30),
                     filler1=(86, 39),
                     verifica=(125, 3),
                     data_decorrenza_grossista=(128, 8),
                     isopartita=(136, 16),
                     filler2=(152, 25)
)

metel_prodotto = dict(marchio_produttore=(0, 3),  # (ad esempio VIW per VIMAR)
                      codice_prodotto=(3, 16),
                      ean13=(19, 13),
                      descrizione=(32, 43),
                      qta_in_cartone=(75, 5),
                      qta_multipla_ordine=(80, 5),
                      qta_minima_ordine=(85, 5),
                      qta_massima_ordine=(90, 6),
                      lead_time=(96, 1),  # quanto tempo passa dall'ordine alla consegna
                      prezzo_al_grossista=(97, 11),
                      prezzo_al_pubblico=(108, 11),
                      moltiplicatore_prezzo=(119, 6),  # quantità di prodotto a cui si riferisce il prezzo
                      codice_valuta=(125, 3),
                      unita_misura=(128, 3),
                      prodotto_composto=(131, 1),  # non rilevante
                      stato_prodotto=(132, 1),  # 3=prodotto gestito, 9=annullato
                      data_ultima_variazione_var=(133, 8),  # ultimo aggiornamento dei dati del prodotto
                      famiglia_di_sconto=(141, 18),  # non rilevante
                      famiglia_statistica=(159, 18),  # il codice della famiglia a cui si appartiene il prodotto
)

standard_0 = {'codice_prodotto': 'CODICE',
              'descrizione': 'DESCRIZIONE',
              'qta_minima_ordine': 'PZ CONFEZIONE',
              'prezzo_al_pubblico': 'PREZZO LORDO',
              'prezzo_al_grossista': 'PREZZO LORDO',
              'famiglia_di_sconto': 'LISTINO',
              'sconto': 'SCONTO%',
}

standard_1 = {'ref': 'ref',
              'codice_prodotto': 'codice_prodotto',
              'attivo': 'attivo',
              'descrizione': 'descrizione',
              'name': 'descrizione',
              'stato_prodotto': 'stato_prodotto',
              'qta_minima_ordine': 'qta_minima_ordine',
              'prezzo_al_pubblico': 'prezzo_al_pubblico',
              'prezzo_al_grossista': 'prezzo_al_grossista',
              'moltiplicatore_prezzo': 'moltiplicatore_prezzo',
              'famiglia_di_sconto': 'famiglia_di_sconto',
              'sconto': 'sconto',
              'ean13': 'ean13'
}


class ProductSupplierinfoWizard(models.TransientModel):
    _name = 'tmp.supplier_info_wizard'

    fileData = fields.Binary(string='Metel file')
    supplier_infos = fields.One2many('tmp.supplier_info', inverse_name='wizard_id', string='Supplier Infos')
    error_message = fields.Char(string='Error')

    data_decorrenza_pubblico = fields.Date(_('Public Effective Date'))
    data_decorrenza_grossista = fields.Date(_('Wholesaler Effective Date'))
    data_variazione = fields.Date(_('Variation Date'))
    verifica = fields.Char(_('Check Code'))
    partita_iva = fields.Char(_('VAT'))
    listino = fields.Char(_('Pricelist'))
    identificazione = fields.Char(_('Identification'))
    azienda = fields.Char(_('Company'))
    descrizione = fields.Char(_('Description'))
    isopartita = fields.Char(_('ISO VAT'))
    filler1 = fields.Char(_('Filler 1'))
    filler2 = fields.Char(_('Filler 2'))
    

    @api.model
    def checkImportMetel(self):
        self.supplier_infos = []
        self.error_message = ''
        tempDir = tempfile.gettempdir()
        tmpFile = os.path.join(tempDir, 'metel.txt')
        if os.path.exists(tmpFile):
            os.unlink(tmpFile)
        with open(tmpFile, 'wb') as fileObj:
            fileObj.write(base64.b64decode(self.fileData))
        tmpFileReader = open(tmpFile, 'rb')
        if not self.fileData:
            self.error_message = 'Cannot compute empty file'
            return self.returnWizard()
        if not self.checkIntegrity(tmpFileReader):
            return self.returnWizard()
        self.runImport(tmpFile)
        return self.returnWizard()
        
    @api.multi
    def returnWizard(self):
        return {'name': _('Import Metel'),
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'tmp.supplier_info_wizard',
                'src_model': "product.supplierinfo",
                #'target': 'new',
                'res_id': self.ids[0],
                'type': 'ir.actions.act_window',
                'domain': "[]"}

    def decodeBytes(self, val):
        try:
            return val.decode("utf-8", errors='ignore')
        except Exception as ex:
            logging.error(ex)
            return ''
        
    @api.model
    def checkIntegrity(self, tmpFileReader):
        header = tmpFileReader.readline()
        if len(header) != 179:
            self.error_message = 'La lunghezza dei records è di {0} non 179+cr+lf caratteri come previsto da METEL'.format(len(header))
            return False
        listino_metel = self.getLineData(header, metel_listino)
        if 'LISTINO METEL' != listino_metel.get('identificazione', ''):
            self.error_message = 'Il file {0} non contiene un listino METEL'.format('METEL.TXT')
            return False
        if listino_metel.get('verifica', '') != '020':
            self.error_message = 'Il listino non è nel formato 020'
            return False
        if listino_metel.get('isopartita', '') != '':
            self.error_message = 'Il campo ISOPARTITA è compilato e lo script non ne prevede la gestione'
            return False
    
        for prodotto in tmpFileReader.readlines():
            prodotto_metel = self.getLineData(prodotto, metel_prodotto)
            if prodotto_metel['codice_valuta'] != 'EUR':
                self.error_message = 'il campo VALUTA è diverso da EUR e lo script non ne prevede la gestione,'
                return False
            if prodotto_metel['stato_prodotto'] in [8, 1]:
                self.error_message = 'il campo stato é {0} e ' \
                      'lo script non ne prevede la gestione,'.format(prodotto_metel['stato_prodotto'])
                return False
            if prodotto_metel['unita_misura'] not in UOM_DESC.keys():
                self.error_message = 'il campo UNITA DI MISURA non è tra quelli METEL,'
                return False
            else:
                if UOM[prodotto_metel['unita_misura']] == '':
                    self.error_message = 'il campo UNITA DI MISURA è {0} ' \
                          'e lo script non ne prevede la gestione'.format(prodotto_metel['unita_misura'])
                    return False
        return True
        
    def getLineData(self, lineToCompute, mapping):
        fields = {}
        for fieldName, charsRange in mapping.items():
            try:
                start, lenght = charsRange
                end = start + lenght
        
                if 'prezzo' in fieldName:
                    if 'moltiplicatore' not in fieldName:
                        integer = self.decodeBytes(lineToCompute[start:end - 2])
                        decimals = self.decodeBytes(lineToCompute[end - 2:end])
                        fields[fieldName] = float('{0}.{1}'.format(integer, decimals))
                    else:
                        fields[fieldName] = int(lineToCompute[start:end])
                else:
                    if 'data' in fieldName:
                        year = int(self.decodeBytes(lineToCompute[start:end - 4]))
                        month = int(self.decodeBytes(lineToCompute[start + 4:end - 2]))
                        day = int(self.decodeBytes(lineToCompute[start + 6:end]))
                        fields[fieldName] = datetime.date(year, month, day)
                    else:
                        if 'lead' in fieldName:
                            lead = self.decodeBytes(lineToCompute[start:end])
                            if lead.isalpha():
                                fields[fieldName] = (ord(lead) - 63) * 5
                            else:
                                fields[fieldName] = int(lead)
                        else:
                            fields[fieldName] = self.decodeBytes(lineToCompute[start:end].strip())
            except Exception as ex:
                logging.error(ex)
                fields[fieldName] = ''
    
        return fields

    @api.multi
    def commonSearchObj(self, refObj, relFilter):
        obj = self.env[refObj]
        res = obj.search(relFilter)
        for elem in res:
            return elem.id
        return False
        
    @api.model
    def runImport(self, tmpFile):
        tmpFileReader = open(tmpFile, 'rb')
        counter = 0
        for lineReader in tmpFileReader.readlines():
            if counter == 0:
                line = self.getLineData(lineReader, metel_listino)
                self.filler1 = line.get('filler1', '')
                self.data_decorrenza_pubblico = line.get('data_decorrenza_pubblico', False)
                self.verifica = line.get('verifica', '')
                self.filler2 = line.get('filler2', '')
                self.partita_iva = line.get('partita_iva', '')
                self.listino = line.get('listino', '')
                self.data_decorrenza_grossista = line.get('data_decorrenza_grossista', False)
                self.identificazione = line.get('identificazione', '')
                self.azienda = line.get('azienda', '')
                self.data_variazione = line.get('data_variazione', False)
                self.descrizione = line.get('descrizione', '')
                self.isopartita = line.get('isopartita', '')
                counter = 1
                continue
            line = self.getLineData(lineReader, metel_prodotto)
            
            prezzo_al_grossista = line.get('prezzo_al_grossista', False)
            ean13 = line.get('ean13', False)
            famiglia_statistica = line.get('famiglia_statistica', False)
            stato_prodotto = line.get('stato_prodotto', False)
            codice_prodotto = line.get('codice_prodotto', False)
            lead_time = line.get('lead_time', False)
            prezzo_al_pubblico = line.get('prezzo_al_pubblico', False)
            marchio_produttore = line.get('marchio_produttore', False)
            data_ultima_variazione_var = line.get('data_ultima_variazione_var', False)
            qta_multipla_ordine = line.get('qta_multipla_ordine', False)
            famiglia_di_sconto = line.get('famiglia_di_sconto', False)
            qta_minima_ordine = line.get('qta_minima_ordine', False)
            prodotto_composto = line.get('prodotto_composto', False)
            moltiplicatore_prezzo = line.get('moltiplicatore_prezzo', False)
            qta_massima_ordine = line.get('qta_massima_ordine', False)
            descrizione = line.get('descrizione', False)
            qta_in_cartone = line.get('qta_in_cartone', False)
            
            codice_valuta = self.commonSearchObj('res.currency', [('name', 'ilike', line.get('codice_valuta', ''))])
            unita_misura = self.commonSearchObj('product.uom', [('name', 'ilike', UOM.get(line.get('unita_misura', '')))])
            
            vals = {
                # Float
                'prezzo_al_grossista': float(prezzo_al_grossista),
                'prezzo_al_pubblico': float(prezzo_al_pubblico),
                'qta_multipla_ordine': float(qta_multipla_ordine),
                'moltiplicatore_prezzo': float(moltiplicatore_prezzo),
                'qta_massima_ordine': float(qta_massima_ordine),
                'qta_minima_ordine': float(qta_minima_ordine),
                'qta_in_cartone': float(qta_in_cartone),
                'lead_time': float(lead_time),
                # Date
                'data_ultima_variazione_var': data_ultima_variazione_var,
                # Char
                'ean13': ean13,
                'famiglia_statistica': famiglia_statistica,
                'stato_prodotto': stato_prodotto,
                'codice_prodotto': codice_prodotto,
                'marchio_produttore': marchio_produttore,
                'famiglia_di_sconto': famiglia_di_sconto,
                'prodotto_composto': prodotto_composto,
                'descrizione': descrizione,
                # many2one
                'unita_misura': unita_misura,
                'codice_valuta': codice_valuta,
                
                'wizard_id': self.ids[0],
                }
            self.env['tmp.supplier_info'].create(vals)

    @api.multi
    def action_test_import(self):
        return self.checkImportMetel()

    @api.multi
    def getPartner(self, vat):
        res = self.env['res.partner'].search([('vat', '=', vat)])
        if not res:
            res = self.env['res.partner'].search([('vat', '=', 'IT' + vat)])
        for elem in res:
            return elem
        return False

    @api.multi
    def getProducts(self, lineBrws):
        productProductEnv = self.env['product.product']
        products = productProductEnv.search([('barcode', '=', lineBrws.ean13)])
        if not products:
            supplInfo = self.env['product.supplierinfo'].search([('product_code', '=', lineBrws.codice_prodotto)])
            if len(supplInfo) > 1:
                raise UserWarning(_('Product with default code %r has been coded more than once' % (lineBrws.codice_prodotto)))
            if supplInfo == 1:
                products = [supplInfo.product_id]
        return products

    @api.multi
    def checkSupplierInfoExists(self, lineBrws, partnerBrws, productBrws):
        supplInfoObj = self.env['product.supplierinfo']
        return supplInfoObj.search([
            ('product_id', '=', productBrws.id),
            ('name', '=', partnerBrws.id),
            ('price', '=', lineBrws.prezzo_al_pubblico),
            ('date_start', '<', lineBrws.data_ultima_variazione_var),
            ('date_end', '>', self.data_decorrenza_pubblico),
            ])
        
    @api.multi
    def action_import(self):
        partner = self.getPartner(self.partita_iva)
        if not partner:
            raise UserWarning(_('Unable to find related partner using VAT %r' % (self.partita_iva)))
        
        supplierInfoObj = self.env['product.supplierinfo']
        
        for lineBrws in self.supplier_infos:
            products = self.getProducts(lineBrws)
#             if not products:
#                 raise UserWarning(_('Unable to find product with ID %r' % (lineBrws.id)))
            for product in products:
                if not self.checkSupplierInfoExists(lineBrws, partner, product):
                    vals = {
                        'name': partner.id,
                        'product_name': lineBrws.descrizione, # Vendor product name
                        'product_code': lineBrws.codice_prodotto, # Vendor product Code
                        'discount': 0, # Discount (%)
                        'delay': int(lineBrws.lead_time), # Delivery Lead Time
                        'min_qty': lineBrws.qta_minima_ordine, # Minimal Quantity
                        'price': lineBrws.prezzo_al_pubblico,
                        'date_start': lineBrws.data_ultima_variazione_var,
                        'date_end': self.data_decorrenza_pubblico,
                        'product_tmplt_id': product.product_tmpl_id.id,
                        'currency_id': lineBrws.codice_valuta.id,
                        'product_id': product.id,
                        }
                    supplierInfoObj.create(vals)
        


class TmpSupplierPricelist(models.TransientModel):
    _name = 'tmp.supplier_info'
    
    prezzo_al_grossista = fields.Float(_('Wholesaler Price'))
    ean13 = fields.Char(_('EAN13'))
    famiglia_statistica = fields.Char(_('Statistic Family'))
    stato_prodotto = fields.Char(_('Field State'))
    codice_prodotto = fields.Char(_('Product Code'))
    lead_time = fields.Float(_('Lead Time'))
    prezzo_al_pubblico = fields.Float(_('Public Price'))
    marchio_produttore = fields.Char(_('Manufacturer Brand'))
    codice_valuta = fields.Many2one('res.currency', _('Currency'))
    data_ultima_variazione_var = fields.Date(_('Date Last Change'))
    qta_multipla_ordine = fields.Float(_('Multiple Quantity Order'))
    famiglia_di_sconto = fields.Char(_('Discount Family'))
    qta_minima_ordine = fields.Float(_('Minimum Quantity Order'))
    prodotto_composto = fields.Char(_('Composed Product'))
    moltiplicatore_prezzo = fields.Float(_('Price Multiplier'))
    qta_massima_ordine = fields.Float(_('Maximum Quantity Order'))
    descrizione = fields.Char(_('Description'))
    qta_in_cartone = fields.Float(_('Quantity in Cardboard'))
    unita_misura = fields.Many2one('product.uom', _('Unit of measure'))
    
    wizard_id = fields.Many2one('tmp.supplier_info_wizard', string='ID')
    
    