'''
Created on Oct 5, 2017

@author: daniel
'''
from OdooQtUi.RPC.rpc import connectionObj
import agenzia_entrate
import os
import sys
from datetime import datetime
import time
from OdooQtUi.utils_odoo_conn import utils
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
    
    def __init__(self, date_from, date_to, journals, progressBar, label_progress, savingPath=''):
        #self.invoiceType = invoiceType  # in_invoice, out_invoice, 'out_refund', 'in_refund'
        #Dati Fatture Emesse (DTE), Dati Fatture Ricevute (DTR) 
        self.date_from = date_from
        self.date_to = date_to
        self.journals = journals
        self.progressBar = progressBar
        self.label_progress = label_progress
        self.savingPath = savingPath
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
        self.label_progress.setText('Reading invoices from database')
        self.progressBar.setValue(0)
        invIds = self.getAllInvoices()
        numberInvoices = len(invIds)
        for invId in invIds:
            index = invIds.index(invId)
            self.progressBar.setValue(self.percentage(index, numberInvoices))
            self.odooReadInvoices.append(self.getInvoiceVals(invId))
        self.generateInvoices()
        self.progressBar.setValue(0)

    def percentage(self, currentVal, maxVal):
        return int(100 * currentVal / maxVal)

    def generateInvoices(self):

        def dichiarante(fiscalCode):
            '''
            CODICE DI CARICA
            1 Rappresentante legale, negoziale o di fatto, socio amministratore
            2 Rappresentante di minore, inabilitato o interdetto, amministratore di sostegno, ovvero curatore dell’eredità giacente,
            amministratore di eredità devoluta sotto condizione sospensiva o in favore di nascituro non ancora concepito
            3 Curatore fallimentare
            4 Commissario liquidatore (liquidazione coatta amministrativa ovvero amministrazione straordinaria)
            5 Custode giudiziario (custodia giudiziaria), ovvero amministratore giudiziario in qualità di rappresentante dei
            beni sequestrati ovvero commissario giudiziale (amministrazione controllata)
            6 Rappresentante fiscale di soggetto non residente
            7 Erede
            8 Liquidatore (liquidazione volontaria)
            9 Soggetto tenuto a presentare la dichiarazione ai fini IVA per conto del soggetto estinto a seguito di operazioni
            straordinarie o altre trasformazioni sostanziali soggettive (cessionario d’azienda, società beneficiaria, incorporante,
            conferitaria, ecc.); ovvero, ai fini delle imposte sui redditi e/o dell’IRAP, rappresentante della società beneficiaria
            (scissione) o della società risultante dalla fusione o incorporazione
            10 Rappresentante fiscale di soggetto non residente con le limitazioni di cui all’art. 44, comma 3, del d.l. n. 331/1993
            11 Soggetto esercente l’attività tutoria del minore o interdetto in relazione alla funzione istituzionale rivestita
            12 Liquidatore (liquidazione volontaria di ditta individuale - periodo ante messa in liquidazione)
            13 Amministratore di condominio
            14 Soggetto che sottoscrive la dichiarazione per conto di una p
            '''
            Carica = None
            agenzia_entrate.DichiaranteType(CodiceFiscale=fiscalCode, Carica)

        def fatturaHeader(progressivo, fiscalCode):
            '''
            Questo blocco va valorizzato solo se il soggetto obbligato alla comunicazione dei dati fattura non coincide con il soggetto passivo IVA al quale i dati si riferiscono. NON deve essere valorizzato se per il soggetto trasmittente è vera una delle seguenti affermazioni:
            - coincide  con il soggetto IVA al quale i dati si riferiscono;
            - è legato da vincolo di incarico con il soggetto IVA al quale i dati si riferiscono;
            - è un intermediario.
            In tutti gli altri casi questo blocco DEVE essere valorizzato.
            '''
            IdSistema = None    # Da non valorizzare mai perchè riservato al sistema
            Dichiarante = dichiarante(fiscalCode)
            return agenzia_entrate.DatiFatturaHeaderType(ProgressivoInvio=unicode(progressivo), IdSistema=IdSistema, Dichiarante=Dichiarante)
        
        def fatturaSede(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione):
            return agenzia_entrate.IndirizzoNoCAPType(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)

        def fatturaStabileOrganizzazione():
            '''
                Blocco da valorizzare nei casi di cedente / prestatore non residente, con stabile organizzazione in Italia
            '''
            return None
            Indirizzo = None
            NumeroCivico = None
            CAP = None
            Comune = None
            Provincia = None
            Nazione = None
            agenzia_entrate.IndirizzoType(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
        
        def fatturaRappresentanteFiscale():
            '''
                Blocco da valorizzare nei casi in cui il cedente / prestatore si avvalga di un rappresentante fiscale in Italia.
            '''
            return None
            IdFiscaleIVA = None
            Denominazione = None
            Nome = None
            Cognome = None
            agenzia_entrate.RappresentanteFiscaleType(IdFiscaleIVA, Denominazione, Nome, Cognome)
            
        def fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione):
            # TODO:    Capire cosa fare
            Sede = fatturaSede(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            StabileOrganizzazione = fatturaStabileOrganizzazione()    # Sembra non servire
            RappresentanteFiscale = fatturaRappresentanteFiscale()    # Sembra non servire
            return agenzia_entrate.AltriDatiIdentificativiNoCAPType(Denominazione, Nome, Cognome, Sede, StabileOrganizzazione, RappresentanteFiscale)
            agenzia_entrate.AltriDatiIdentificativiNoSedeType(Denominazione, Nome, Cognome, Sede, StabileOrganizzazione, RappresentanteFiscale)
        
        def fatturaIdFiscaleIva(idPaese, idCodice):
            #IdPaese = ''    # esempio IT
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
            idPaese = 'IT'  # Può essere solo IT
            country = vals.get('country_id', None)
            if country:
                idCountry, _countryName = country
                res = connectionObj.read('res.country', ['name', 'code'], [idCountry])
                for elemDict in res:
                    return elemDict.get('code', None), idPaese
            return None, idPaese

        def fatturaDatiGenerali():
            TipoDocumento = '' #Esempio TD01 per le fatture
            Data = datetime.strptime(fatturaVals.get('date_invoice'), SERVER_DATE_FORMAT)   # Data fattura in formato italiano
            Numero = fatturaVals.get('number', None) or None # Numero fattura
            return agenzia_entrate.DatiGeneraliType(TipoDocumento, Data.date(), Numero)
        
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
            # TODO: Ciclo for per andare a mettere dati di fatture dello stesso cliente
            DatiGenerali = fatturaDatiGenerali()
            DatiRiepilogo = fatturaDatiRiepilogo()
            return [agenzia_entrate.DatiFatturaBodyDTEType(DatiGenerali, DatiRiepilogo)]

        def fatturaBodyDTR():
            # TODO: Ciclo for per andare a mettere dati di fatture dello stesso fornitore
            DatiGenerali = fatturaDatiGenerali()
            DatiRiepilogo = fatturaDatiRiepilogo()
            return [agenzia_entrate.DatiFatturaBodyDTRType(DatiGenerali, DatiRiepilogo)]
            
        def fatturaDTE():
            # Fattura emessa
            '''
                Non devono essere riportati in questo blocco i dati delle così dette autofatture, cioè fatture emesse dall'acquirente nei casi in cui non le abbia 
                ricevute oppure, pur avendole ricevute, abbia rilevato in esse delle irregolarità. Tali dati devono essere riportati come dati delle fatture ricevute.
            '''
            CedentePrestatoreDTE = fatturaCedentePrestatore(partnerVals)
            CessionarioCommittenteDTE = fatturaConcessionarioCommittente(companyVals)
            Rettifica = None    # Pare non serva
            return agenzia_entrate.DTEType(CedentePrestatoreDTE=CedentePrestatoreDTE, CessionarioCommittenteDTE=CessionarioCommittenteDTE, Rettifica=Rettifica)

        def fatturaDTR():
            # Fattura ricevuta
            CessionarioCommittenteDTR = fatturaConcessionarioCommittenteDTR(partnerVals)
            CedentePrestatoreDTR = fatturaCedentePrestatoreDTR(companyVals)
            Rettifica = None
            return agenzia_entrate.DTRType(CessionarioCommittenteDTR=CessionarioCommittenteDTR, CedentePrestatoreDTR=CedentePrestatoreDTR, Rettifica=Rettifica)

        def fatturaCedentePrestatore(vals):
            # Chi la manda (fornitore)
            codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione = getCommonVals(vals)
            IdentificativiFiscali = fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice)
            AltriDatiIdentificativi = fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            return agenzia_entrate.CedentePrestatoreDTEType(IdentificativiFiscali, AltriDatiIdentificativi)
            
        def fatturaConcessionarioCommittente(vals):
            # Chi la riceve la fattura, quindi ha chiesto un lavoro
            '''
                Blocco contenente le informazioni relative al cessionario/committente (cliente) e ai dati fattura a lui riferiti.
                Può essere replicato per trasmettere dati di fatture relative a clienti diversi
            '''
            # TODO: Inserire un ciclo che va a creare n concessionari committenti, uno per ogni fattura emessa
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
            # TODO: Ciclo for
            codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione = getCommonVals(vals)
            IdentificativiFiscali = fatturaIdentificativiFiscali(codiceFiscale, idPaese, idCodice)
            AltriDatiIdentificativi = fatturaAltriDatiIdentificativi(Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione)
            DatiFatturaBodyDTR = fatturaBodyDTR()
            return [agenzia_entrate.CedentePrestatoreDTRType(IdentificativiFiscali, AltriDatiIdentificativi, DatiFatturaBodyDTR)]

        def encodeStringByDict(vals, val):
            res = vals.get(val, '')
            return encodeString(res)
        
        def encodeString(res):
            if not res:
                res = None
            else:
                res = res.encode('ascii', 'ignore')
            return res
            
        def getCommonVals(vals):
            codiceFiscale = vals.get('fiscalcode', None) or None
            is_company = vals.get('is_company', None)
            Denominazione = None
            Nome = None
            Cognome = None
            if is_company:
                Denominazione = encodeStringByDict(vals, 'name')
            else:
                nameList = vals.get('name', '').split(' ')
                Nome = nameList[0].encode('ascii', 'ignore')
                Nome = encodeString(Nome)
                Cognome = ' '.join(nameList[1:])
                Cognome = encodeString(Cognome)
            Indirizzo = encodeStringByDict(vals, 'street')  # Se si mette il civico qua allora non si deve mettere il "NumeroCivico"
            NumeroCivico = encodeStringByDict(vals, 'street2') or None
            CAP = vals.get('zip', None) or None
            Comune = encodeStringByDict(vals, 'city')
            Provincia = getProvince(vals) or None
            Nazione, idPaese = getCountry(vals)
            idCodice = vals.get('vat', None) or None # Partita iva
            return codiceFiscale, idPaese, idCodice, Denominazione, Nome, Cognome, Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione
            
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
        numberInvoices = len(self.odooReadInvoices)
        self.label_progress.setText('Reading infos and generating XML files')
        for fatturaVals in self.odooReadInvoices:
            index = self.odooReadInvoices.index(fatturaVals)
            self.progressBar.setValue(self.percentage(index, numberInvoices))
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
        self.progressBar.setValue(0)
        self.label_progress.setText('')
    
    def createXML(self, progressivo, _fatturaTypeObj):
        newFileName = unicode(progressivo) + '.xml'
        currentDir = os.getcwd()
        if self.savingPath:
            currentDir = self.savingPath
        outDir = os.path.join(currentDir, 'OUT_XML_SPESOMETRO')
        if not os.path.exists(outDir):
            os.makedirs(outDir)
        newFilePath = os.path.join(outDir, newFileName)
        with open(newFilePath, 'w') as outFile:
            _fatturaTypeObj.export(outFile, 0)
        if os.path.exists(newFilePath):
            print 'File %r generated' % (newFileName)
