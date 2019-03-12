# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import dateutil.parser
import StringIO
import logging

from odoo import api, fields, models, _ 
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from cbi.wrapper import Flow

class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.bank.statement.import"

    def _get_hide_journal_field(self):
        return self.env.context and 'journal_id' in self.env.context or False

    journal_id = fields.Many2one('account.journal', string='Journal',
        help="Accounting journal related to the bank statement you're importing.")
    hide_journal_field = fields.Boolean(string='Hide the journal field in the view', default=_get_hide_journal_field)
    
    record_identifier = fields.Integer(string="CBI Record identifier",
                                   default=62)

    @api.onchange('data_file')
    def _onchange_data_file(self):
        file_content = self.data_file and base64.b64decode(self.data_file) or ""

    def _find_additional_data(self, *args):
        """ As .CBI format does not allow us to detect the journal, we need to let the user choose it.
            We set it in context in the same way it's done when calling the import action from a journal.
        """
        if self.journal_id:
            self.env.context = dict(self.env.context, journal_id=self.journal_id.id)
        return super(AccountBankStatementImport, self)._find_additional_data(*args)
    
    def _parse_file(self, data_file):
        BankStatementLine = self.env['account.bank.statement.line']
        vals_bank_statement = {}
        flow = Flow()
        flow.readfile(data_file.split("\n"),
                      firstrecordidentifier=self.record_identifier)
        
        def mergeColumnRecord(records, record_index):
            records_dict = {}
            for record in records:
                if not record.hasKey(record_index):
                    continue
                record_index_value = record[record_index]
                if record_index_value in records_dict.keys():
                    records_dict[record_index_value].appendFields(record)
                else:
                    records_dict[record_index_value] = record
            return records_dict.values()
            
        for disposal in flow.disposals:
            transactions = []
            total_amount = 0.0
            unique_ids = []
            index = 1
            for record in mergeColumnRecord(disposal.records, record_index='record_group'):
                vals_line = {}
                unique_val = record.get('data', '') + record['credito_debito'] + record['amount'] + record['causale'].strip() + record.get('descrizione', '')
                if unique_val in unique_ids:
                    raise UserError("Duplicate value in file %r" % unique_val)
                unique_ids.append(unique_val)
                if BankStatementLine.sudo().search_count([('unique_import_id', '=', unique_val)])>0:
                    logging.warning("Row Already in the database %r" % unique_val)
                    continue
                amount = float(record['amount'].replace(',', '.'))
                if record['credito_debito'] == 'D':
                    amount = -amount
                total_amount += amount
                if str(self.record_identifier) in record['tipo_record']:
                    vals_line['sequence'] = index
                    vals_line['date'] = datetime.datetime.strptime(record['data'], "%d%m%y").strftime(DEFAULT_SERVER_DATE_FORMAT)
                    vals_line['amount'] = amount
                    vals_line['ref'] = record['causale']
                    vals_line['unique_import_id'] = unique_val
                    vals_line['name'] = record.get('descrizione', '')
                    index +=1
                transactions.append(vals_line)
                
            vals_bank_statement.update({
                'name': self.filename,
                'balance_end_real': total_amount,
                'transactions': transactions
            })
        return None, None, [vals_bank_statement]
