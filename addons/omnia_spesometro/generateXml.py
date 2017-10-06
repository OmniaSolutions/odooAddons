'''
Created on Oct 5, 2017

@author: daniel
'''
from OdooQtUi.RPC.rpc import connectionObj
import agenzia_entrate
import os
from datetime import datetime
SERVER_DATE_FORMAT = '%Y-%m-%d'

INVOICE_LINE_FIELDS = [
    'id',
    'account_id',
    'invoice_id',
    'price_subtotal',
    'partner_id',
    'reverse_charge',
    'invoice_line_tax_id',
    'journal_id'
    ]

PARTNER_FIELDS =[
    'id',
    'name',
    'street',
    'city',
    'vat',
    'fiscalcode',
    'country_id',
    'state_id',
    'province',
    'zip',
    'is_company',
    ]

INVOICE_FIELDS = [
    'id',
    'number',
    'fiscal_position',
    'date_invoice',
    'registration_date',
    'journal_id',
    'period_id',
    'partner_id',
    'type',
    'amount_total',
    'amount_tax',
    ]


class GenerateXml(object):
    
    def __init__(self, date_from, date_to, journals):
        #self.invoiceType = invoiceType  # in_invoice, out_invoice, 'out_refund', 'in_refund'
        #Dati Fatture Emesse (DTE), Dati Fatture Ricevute (DTR) 
        self.date_from = date_from
        self.date_to = date_to
        self.journals = journals
        self.odooReadInvoices = []
        self.generatedInvoices = []
        super(GenerateXml, self).__init__()
        
    def getInvoiceType(self, invoiceVals):
        typeInvoice = invoiceVals.get('type', '')
        if typeInvoice == 'in_invoice':
            return 'DTR'
        elif typeInvoice == 'in_refund':
            return 'DTR'
        elif typeInvoice == 'out_invoice':
            return 'DTE'
        elif typeInvoice == 'out_refund':
            return 'DTE'

    def getInvoiceVals(self, invId):
        for resdict in connectionObj.read('account.invoice',
                                  INVOICE_FIELDS,
                                  [invId]):
            return resdict
        return {}

    def getPartnerVals(self, partnerId):
        for resdict in connectionObj.read('res.partner',
                                  PARTNER_FIELDS,
                                  [partnerId]):
            return resdict
        return {}
        
    def readInvoiceLines(self, lineIds):
        return connectionObj.read('account.invoice.line',
                                  INVOICE_LINE_FIELDS,
                                  lineIds)
        
    def getAllInvoiceLines(self, invoiceIds):
        return connectionObj.search('account.invoice.line',
                             [('invoice_id','in',invoiceIds)])
        
    def getAllInvoices(self):
        return connectionObj.search('account.invoice',
                             [('date_invoice','>=',self.date_from),('date_invoice','<=',self.date_to)])

    def startReading(self):
        invIds = self.getAllInvoices()
        for invId in invIds:
            self.odooReadInvoices.append(self.getInvoiceVals(invId))
        self.generateInvoices()

    def generateInvoices(self):

        def fatturaHeader(progressivo, fiscalCode):
            return agenzia_entrate.DatiFatturaHeaderType(ProgressivoInvio=unicode(progressivo), IdSistema=unicode(fiscalCode))
        
        def fatturaSede(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione):
            return agenzia_entrate.IndirizzoNoCAPType(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)

        def fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione):
            # TODO:    Capire cosa fare
            Sede = fatturaSede(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            StabileOrganizzazione = None    # Sembra non servire
            RappresentanteFiscale = None    # Sembra non servire
            return agenzia_entrate.AltriDatiIdentificativiNoCAPType(Denominazione, Nome, Cognome, Sede, StabileOrganizzazione, RappresentanteFiscale)
            agenzia_entrate.AltriDatiIdentificativiNoSedeType(Denominazione, Nome, Cognome, Sede, StabileOrganizzazione, RappresentanteFiscale)
        
        def fatturaIdFiscaleIva(idPaese, idCodice):
            #IdPaese = ''    # esempio IT
            #IdCodice = ''    # boh
            return agenzia_entrate.IdFiscaleITIvaType(idPaese, idCodice)
            
        def fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice):
            IdFiscaleIVA = fatturaIdFiscaleIva(idPaese, idCodice)
            return agenzia_entrate.IdentificativiFiscaliType(IdFiscaleIVA, CodiceFiscale=codiceFiscale)
        
        def getProvince(vals):
            prov = vals.get('province', None)
            if prov:
                idProv, _provName = prov
                res = connectionObj.read('res.province', ['name', 'code'], [idProv])
                for elemDict in res:
                    return elemDict.get('code', None)
            return None
        
        def getCountry(vals):
            country = vals.get('country_id', None)
            if country:
                idCountry, _countryName = country
                res = connectionObj.read('res.country', ['name', 'code'], [idCountry])
                for elemDict in res:
                    return elemDict.get('code', None), elemDict.get('code', None)
            return None

        def fatturaDatiGenerali():
            TipoDocumento = '' #Esempio TD01 per le fatture
            Data = datetime.strptime(fatturaVals.get('date_invoice'), SERVER_DATE_FORMAT)   # Data fattura in formato italiano
            Numero = fatturaVals.get('number', None) # Numero fattura
            return agenzia_entrate.DatiGeneraliType(TipoDocumento, Data, Numero)
        
        def fatturaDatiIVA():
            Imposta = fatturaVals.get('amount_tax', 0.0) # Iva calcolata in euro
            Aliquota = 0 # TODO: Iva ad esempio 22
            res = agenzia_entrate.DatiIVAType(unicode(Imposta), unicode(Aliquota))
            res.Aliquota = Aliquota
            res.Imposta = Imposta
            return res
            
        def fatturaDatiRiepilogo():
            ImponibileImporto = fatturaVals.get('amount_total', 0.0)   # Importo fattura
            DatiIVA = fatturaDatiIVA()
            Natura = None # ???
            Detraibile = None # ???
            Deducibile = None # ???
            EsigibilitaIVA = None # ???
            res = agenzia_entrate.DatiRiepilogoType(ImponibileImporto=None, DatiIVA=DatiIVA, Natura=Natura, Detraibile=Detraibile, Deducibile=Deducibile, EsigibilitaIVA=EsigibilitaIVA)
            res.ImponibileImporto = ImponibileImporto
            return [res]

        def fatturaBody():
            DatiGenerali = fatturaDatiGenerali()
            DatiRiepilogo = fatturaDatiRiepilogo()
            return [agenzia_entrate.DatiFatturaBodyDTEType(DatiGenerali, DatiRiepilogo)]

        def fatturaBodyDTR():
            DatiGenerali = fatturaDatiGenerali()
            DatiRiepilogo = fatturaDatiRiepilogo()
            return agenzia_entrate.DatiFatturaBodyDTRType(DatiGenerali, DatiRiepilogo)
            
        def fatturaDTE():
            CedentePrestatoreDTE = fatturaCedentePrestatore(partnerVals)
            CessionarioCommittenteDTE = fatturaConcessionarioCommittente(companyVals)
            Rettifica = None    # Pare non serva
            return agenzia_entrate.DTEType(CedentePrestatoreDTE=CedentePrestatoreDTE, CessionarioCommittenteDTE=CessionarioCommittenteDTE, Rettifica=Rettifica)

        def fatturaCedentePrestatore(vals):
            # Chi la manda
            codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione = getCommonVals(vals)
            IdentificativiFiscali = fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice)
            AltriDatiIdentificativi = fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            return agenzia_entrate.CedentePrestatoreDTEType(IdentificativiFiscali, AltriDatiIdentificativi)
            
        def fatturaConcessionarioCommittente(vals):
            # Chi la riceve la fattura, quindi ha chiesto un lavoro
            codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione = getCommonVals(vals)
            IdentificativiFiscali = fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice)
            AltriDatiIdentificativi = fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            DatiFatturaBodyDTE = fatturaBody()
            return [agenzia_entrate.CessionarioCommittenteDTEType(IdentificativiFiscali, AltriDatiIdentificativi, DatiFatturaBodyDTE)]

        def fatturaConcessionarioCommittenteDTR(vals):
            codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione = getCommonVals(vals)
            IdentificativiFiscali = fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice)
            AltriDatiIdentificativi = fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            return agenzia_entrate.CessionarioCommittenteDTRType(IdentificativiFiscali, AltriDatiIdentificativi)
        
        def fatturaCedentePrestatoreDTR(vals):
            codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione = getCommonVals(vals)
            IdentificativiFiscali = fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice)
            AltriDatiIdentificativi = fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            DatiFatturaBodyDTR = [fatturaBodyDTR()]
            return agenzia_entrate.CedentePrestatoreDTRType(IdentificativiFiscali, AltriDatiIdentificativi, DatiFatturaBodyDTR)
            
        def getCommonVals(vals):
            codiceFiscale = vals.get('fiscalcode', None) or None
            is_company = vals.get('is_company', None)
            Denominazione = None
            Nome = None
            Cognome = None
            if is_company:
                Denominazione = vals.get('name', '')
            else:
                nameList = vals.get('name', '').split(' ')
                Nome = nameList[0]
                Cognome = nameList[1:]
            Indirizzo = vals.get('street', None)
            NumeroCivico = vals.get('street2', None)
            CAP = vals.get('zip', None)
            Comune = vals.get('city', None)
            Provincia = getProvince(vals)
            Nazione, idPaese = getCountry(vals)
            idCodice = '' # Boh
            return codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione
            
        def fatturaDTR():
            CessionarioCommittenteDTR = fatturaConcessionarioCommittenteDTR(partnerVals)
            CedentePrestatoreDTR = fatturaCedentePrestatoreDTR(companyVals)
            Rettifica = None
            return agenzia_entrate.DTRType(CessionarioCommittenteDTR=CessionarioCommittenteDTR, CedentePrestatoreDTR=[CedentePrestatoreDTR], Rettifica=Rettifica)

        def fatturaSignature():
            # Ci va?
            return None

        companyIds = connectionObj.search('res.company', [])
        companyValsList = connectionObj.read('res.company', ['partner_id'], companyIds)
        companyVals = {}
        for companyValsl in companyValsList:
            partnerId, _partnerName = companyValsl.get('partner_id', [None, None])
            companyVals = self.getPartnerVals(partnerId)
            break
        progressivo = 1
        for fatturaVals in self.odooReadInvoices:
            prt = fatturaVals.get('partner_id', False)
            partnerVals = {}
            if prt:
                prtId, _prtName = prt
                partnerVals = self.getPartnerVals(prtId)
            fiscalCode = partnerVals.get('fiscalcode', '')
            DTE = None
            DTR = None
            ANN = None
            versione = None # Pare non serva
            if self.getInvoiceType(fatturaVals) == 'DTE':
                DTE = fatturaDTE()
            elif self.getInvoiceType(fatturaVals) == 'DTR':
                DTR = fatturaDTR()
            Signature = fatturaSignature()
            header = fatturaHeader(progressivo, fiscalCode)
            _fatturaTypeObj = agenzia_entrate.DatiFatturaType(versione=versione, DatiFatturaHeader=header, DTE=DTE, DTR=DTR, ANN=ANN, Signature=Signature)
            self.createXML(progressivo, _fatturaTypeObj)
            progressivo = progressivo + 1
            # Fare il parse del risultato e collezionare gli xml generati
    
    def createXML(self, progressivo, _fatturaTypeObj):
        newFileName = unicode(progressivo) + '.xml'
        currentDir = os.getcwd()
        generatorFilePath = os.path.join(currentDir, 'agenzia_entrate.py')
        outDir = os.path.join(currentDir, 'OUT')
        if not os.path.exists(outDir):
            os.makedirs(outDir)
        newFilePath = os.path.join(outDir, newFileName)
        with open(newFilePath, 'w') as outFile:
            _fatturaTypeObj.export(outFile, 0)
#         if not os.path.exists(newFilePath):
#             with open(newFilePath, 'wb') as aaa:
#                 pass
#         cmd = 'python %s -s %s' % (generatorFilePath, newFilePath)
#         res = os.popen(cmd)
        if os.path.exists(newFilePath):
            print 'File %r generated' % (newFileName)
        
