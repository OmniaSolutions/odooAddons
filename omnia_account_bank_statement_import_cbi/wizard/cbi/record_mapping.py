# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2012 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2012 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# Struttura del record di testa - codice fisso "IM"
IM = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 104, 'filler2'),
    (105, 105, 'tipo_flusso'),
    (106, 106, 'qualificatore_flusso'),
    (107, 111, 'soggetto_veicolatore'),
    (112, 113, 'filler3'),
    (114, 114, 'codice_divisa'),
    (115, 115, 'filler4'),
    (116, 120, 'campo_non_disponibile'),
    ]

# Struttura del record di testa - codice fisso "PC"
PC = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 104, 'filler2'),
    (105, 105, 'tipo_flusso'),
    (106, 106, 'qualificatore_flusso'),
    (107, 111, 'soggetto_veicolatore'),
    (112, 112, 'filler3'),
    (113, 113, 'flag_priorita_trattamento_bonifico'),
    (114, 114, 'codice_divisa'),
    (115, 115, 'filler4'),
    (116, 120, 'campo_non_disponibile'),
    ]

# 3.1 Struttura del record di testa– codice fisso "PE"
PE = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 104, 'filler2'),
    (105, 105, 'tipo_flusso'),
    (106, 106, 'qualificatore_flusso'),
    (107, 111, 'soggetto_veicolatore'),
    (112, 115, 'filler3'),
    (116, 120, 'campo_non_disponibile'),
    ]

# Struttura del record di coda - codice fisso "EF"
EF = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 52, 'numero_disposizioni'),
    (53, 67, 'tot_importi_negativi'),
    (68, 82, 'tot_importi_positivi'),
    (83, 89, 'numero_record'),
    (90, 113, 'filler2'),
    (114, 114, 'codice_divisa'),
    (115, 120, 'campo_non_disponibile'),
    ]

# Struttura del record di coda - codice fisso "RH"
RH = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 52, 'numero_disposizioni'),
    (53, 67, 'tot_importi_negativi'),
    (68, 82, 'tot_importi_positivi'),
    (83, 89, 'numero_record'),
    (90, 113, 'filler2'),
    (114, 114, 'codice_divisa'),
    (115, 120, 'campo_non_disponibile'),
    ]

# Struttura del record di coda - codice fisso "EF" - bonifici
EF_BON = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 52, 'numero_disposizioni'),
    (53, 67, 'tot_importi_negativi'),
    (68, 82, 'tot_importi_positivi'),
    (83, 89, 'numero_record'),
    (90, 112, 'filler2'),
    (113, 113, 'flag_priorita_trattamento_bonifico'),
    (114, 114, 'codice_divisa'),
    (115, 120, 'campo_non_disponibile'),
    ]

# Struttura del record di coda - codice fisso "EF" - bonifici esteri
EF_BON_ES = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 52, 'numero_disposizioni'),
    (53, 64, 'filler2'),
    (65, 82, 'totale_importi'),
    (83, 89, 'numero_record'),
    (90, 114, 'filler3'),
    (115, 120, 'campo_non_disponibile'),
    ]

# Struttura del record - codice fisso “10”
X = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 16, 'filler2'),
    (17, 22, 'data_esecuzione_disposizione'),
    (23, 28, 'data_valuta_banca_beneficiario'),
    (29, 33, 'causale'),
    (34, 46, 'importo'),
    (47, 47, 'segno'),
    (48, 52, 'codice_abi_banca_ordinante'),
    (53, 57, 'codice_cab_banca_ordinante'),
    (58, 69, 'conto_ordinante'),
    (70, 74, 'codice_abi_banca_destinataria'),
    (75, 79, 'codice_cab_banca_destinataria'),
    (80, 91, 'conto_destinatario'),
    (92, 96, 'codice_azienda'),
    (97, 97, 'tipo_codice'),
    (98, 113, 'codice_cliente_beneficiario'),
    (114, 114, 'modalita_di_pagamento'),
    (115, 118, 'filler4'),
    (119, 119, 'flag_priorita_trattamento_bonifico'),
    (120, 120, 'codice_divisa'),
    ]

# Struttura del record - codice fisso “14”
XIV = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 22, 'filler2'),
    (23, 28, 'data_pagamento'),
    (29, 33, 'causale'),
    (34, 46, 'importo'),
    (47, 47, 'segno'),
    (48, 52, 'codice_abi_banca'),
    (53, 57, 'cab_banca'),
    (58, 69, 'conto'),
    (70, 91, 'filler3'),
    (92, 96, 'codice_azienda'),
    (97, 97, 'tipo_codice'),
    (98, 113, 'codice_cliente_debitore'),
    (114, 119, 'filler4'),
    (120, 120, 'codice_divisa'),
    ]

# Tipo record 16 (coordinate ordinante)
XVI = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 12, 'codice_paese'),
    (13, 14, 'check_digit'),
    (15, 15, 'cin'),
    (16, 20, 'codice_abi'),
    (21, 25, 'codice_cab'),
    (26, 37, 'numero_conto'),
    (38, 44, 'filler2'),
    (45, 120, 'filler3'),
    ]

# Struttura del record – codice fisso “17” (coordinate beneficiario)
XVII = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 12, 'codice_paese'),
    (13, 14, 'check_digit'),
    (15, 15, 'cin'),
    (16, 20, 'codice_abi'),
    (21, 25, 'codice_cab'),
    (26, 37, 'numero_conto'),
    (38, 44, 'filler2'),
    (45, 120, 'filler3'),
    ]

# Struttura del record - codice fisso “20”
XX = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 34, '1_segmento'),
    (35, 58, '2_segmento'),
    (59, 82, '3_segmento'),
    (83, 106, '4_segmento'),
    (107, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “20” - bonifici
XX_BON = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, 'denominazione_azienda'),
    (41, 70, 'indirizzo'),
    (71, 100, 'localita'),
    (101, 116, 'codifica_fiscale'),
    (117, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “30”
XXX = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, '1_segmento'),
    (41, 70, '2_segmento'),
    (71, 86, 'codice_fiscale_cliente'),
    (87, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “30” - bonifici
XXX_BON = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, '1_segmento'),
    (41, 70, '2_segmento'),
    (71, 100, '3_segmento'),
    (101, 116, 'codice_fiscale_cliente'),
    (117, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “40”
XL = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, 'indirizzo'),
    (41, 45, 'cap'),
    (46, 70, 'comune_e_sigla_provincia'),
    (71, 98, 'completamento_indirizzo'),
    (99, 100, 'codice_paese'),
    (101, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “40” - bonifici
XL_BON = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, 'indirizzo'),
    (41, 45, 'cap'),
    (46, 70, 'comune_e_sigla_provincia'),
    (71, 120, 'banca_sportello_beneficiario'),
    ]

# Struttura del record – codice fisso “50” - bonifici
L_BON = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, '1_segmento'),
    (41, 70, '2_segmento'),
    (71, 100, '3_segmento'),
    (101, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “50”
L = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 50, '1_segmento'),
    (51, 90, '2_segmento'),
    (91, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “51”
LI = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 20, 'numero_disposizione'),
    (21, 74, 'filler2'),
    (75, 86, 'codice_identificativo_univoco'),
    (87, 120, 'filler3'),
    ]

# Struttura del record - codice fisso “59”
LIX = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 65, '1_segmento'),
    (66, 120, '2_segmento'),
    ]
#610000001             0000000000                14U0000483210030000000700EUR010119C000000018732,80IT08
RH_61 = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 49, 'unknow'),
    (49, 74, 'iban'),
    (74, 77, 'currency'),
    (77, 83, 'date'),
    (83, 84, 'cousale'),
    (84, 99, 'amount'),
    (100, 101, 'country_code'),
    (102, 103, 'number_code'),    
    ]
#620000001001280219280219D000000000019,5645                                           ADDEBITO TELEPASS / VIACARD
RH_62 = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (10, 13, 'record_group'),
    (20, 25, 'data'),
    (26, 26, 'credito_debito'),
    (27, 43, 'amount'),
    (87, 113, 'causale'),    
    ]
#630000001001 CRED. TELEPASS S.P.A. ID.MANDATO 7013840000000165770081 RIF. SALDO DOCUM. 003373412 DEL 280 219 SDD 2019 R
RH_63 = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (10, 13, 'record_group'),
    (15, 120, 'descrizione'),    
    ] 
#640000001EUR280219C000000005950,68C000000005950,68
RH_64 = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (11, 13, 'currency'), 
    (14, 19, 'date'), 
    (37, 51, 'amount'), 
    ]

# Struttura del record – codice fisso “60”
LX = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 40, '1_segmento'),
    (41, 70, '2_segmento'),
    (71, 100, '3_segmento'),
    (101, 120, 'filler2'),
    ]

# Struttura del record - codice fisso “70”
LXX = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 93, 'filler2'),
    (94, 94, 'tipo_bollettino'),
    (95, 95, 'filler3'),
    (96, 100, 'campo_a_disposizione'),
    (101, 120, 'chiavi_di_controllo'),
    ]
# Struttura del record - codice fisso “70” - bonifici
LXX_BON = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 25, 'filler2'),
    (26, 30, 'campo_non_disponibile'),
    (31, 31, 'tipo_flusso'),
    (32, 32, 'qualificatore_flusso'),
    (33, 37, 'soggetto_veicolatore'),
    (38, 42, 'codice_mp'),
    (43, 69, 'filler3'),
    (70, 70, 'flag_richiesta'),
    (71, 100, 'codice_univoco'),
    (101, 110, 'filler4'),
    (111, 111, 'cin_coordinate_bancaria'),
    (112, 112, 'filler5'),
    (113, 120, 'chiavi_di_controllo'),
    ]

# Struttura del record di testa - codice fisso “IB”
IB = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 8, 'mittente'),
    (9, 13, 'ricevente'),
    (14, 19, 'data_creazione'),
    (20, 39, 'nome_supporto'),
    (40, 45, 'campo_a_disposizione'),
    (46, 104, 'filler2'),
    (105, 105, 'tipo_flusso'),
    (106, 106, 'qualificatore_flusso'),
    (107, 111, 'soggetto_veicolatore'),
    (112, 113, 'filler3'),
    (114, 114, 'codice_divisa'),
    (115, 115, 'filler4'),
    (116, 120, 'campo_non_disponibile'),
    ]

# Struttura del record del flusso di ritorno - codice fisso “14”
XIV_IN = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 22, 'filler2'),
    (23, 28, 'data_pagamento'),
    (29, 33, 'causale'),
    (34, 46, 'importo'),
    (47, 47, 'segno'),
    (48, 52, 'codice_abi_esattrice'),
    (53, 57, 'cab_esattrice'),
    (58, 69, 'filler3'),
    (70, 74, 'codice_abi_assuntrice'),
    (75, 79, 'cab_assuntrice'),
    (80, 91, 'conto'),
    (92, 96, 'codice_azienda'),
    (97, 97, 'tipo_codice'),
    (98, 113, 'codice_cliente_debitore'),
    (114, 119, 'filler4'),
    (120, 120, 'codice_divisa'),
    ]

# Struttura del record del flusso di ritorno - codice fisso “51”
LI_IN = [
    (1, 1, 'filler1'),
    (2, 3, 'tipo_record'),
    (4, 10, 'numero_progressivo'),
    (11, 20, 'numero_disposizione'),
    (21, 74, 'filler2'),
    (75, 86, 'codice_identificativo_univoco'),
    (87, 120, 'filler3'),
    ]

OUTPUT_RECORD_MAPPING = {
    'IM': IM,
    'EF': EF,
    'RH': RH,
    'PC': PC,
    '10': X,
    '14': XIV,
    '16': XVI,
    '17': XVII,
    '20': XX,
    '30': XXX,
    '40': XL,
    '50': L,
    '51': LI,
    '59': LIX,
    '61': RH_61, #mabo
    '62': RH_62, #mabo
    '63': RH_63, #mabo
    '64': RH_64, #mabo
    '70': LXX,
    'IB': IB,
    }

INPUT_RECORD_MAPPING = {
    'IM': IM,
    'EF': EF,
    '14': XIV_IN,
    '20': XX,
    '30': XXX,
    '40': XL,
    '50': L,
    '51': LI_IN,
    '59': LIX,
    '70': LXX,
    'IB': IB,
    }

MAV = {
    'IM': IM,
    'EF': EF,
    '14': XIV_IN,
    '20': XX,
    '30': XXX,
    '40': XL,
    '50': L,
    '51': LI_IN,
    '59': LIX,
    '70': LXX,
    'IB': IB,
    }

BONIFICI = {
    'PC': PC, # testa
    '10': X,
    '16': XVI,
    '17': XVII,
    '20': XX_BON,
    '30': XXX_BON,
    '40': XL_BON,
    '50': L_BON,
    '60': LX,
    '70': LXX_BON,
    'EF': EF_BON, # coda
    }

BONIFICI_ESTERI = {
    'PE': PE, #testa
    # ...
    'EF': EF_BON_ES, #coda
    }