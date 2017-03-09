##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 10/lug/2013 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
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
Created on 10/lug/2013
@author: mboscolo
'''
from odoo.report import report_sxw
import os
from odoo import _


class omnia_ddt_parser(report_sxw.rml_parse):

    def get_logo_path_by_name(self, name):
        """Return logo path by name"""
        header_obj = self.pool.get('ir.header_img')
        header_img_id = header_obj.search(self.cursor,
                                          self.uid,
                                          [('name', '=', name)]
                                          )
        if not header_img_id:
            return u''
        if isinstance(header_img_id, list):
            header_img_id = header_img_id[0]

        head = header_obj.browse(self.cursor, self.uid, header_img_id)
        return str("data:image/%s;base64,%s") % (head.type, str(head.img))

    def getSelectionValue(self, model, fieldName, field_val):
        """
            Get a value before the selection values in selection fields
        """
        return dict(self.pool.get(model).fields_get(self.cr, self.uid)[fieldName]['selection']).get(field_val, '')

    def convertToSiNo(self, value):
        """
            convert the boolean value to siNo
        """
        if str(value).upper() == 'TRUE':
            return "Si"
        elif str(value).upper() == 'FALSE':
            return "No"
        return value

    def ifTrueEmpty(self, value):
        """
            return a "---" string if field is empty
        """
        if str(value) == "False":
            return "---"
        if isinstance(value, (unicode, str)):
            return value.replace("\n", "<p/>")
        return "---"

    def getPaymentTerm(self, invoice):
        """
            get the payment terms
        """
        payment_term_id = invoice.payment_term.id
        date_invoice = invoice.date_invoice
        amount_total = invoice.amount_total
        pterm_list = self.pool.get('account.payment.term').compute(self.cr, self.uid, payment_term_id, value=1, date_ref=date_invoice)
        outValue = []
        for date, percentage in pterm_list:
            outValue.append((date, "%.2f" % (amount_total * percentage)))
        return outValue

    def getIvaValue(self, invoice):
        outValue = 22
        for invoiceLine in invoice.invoice_line:
            if invoiceLine.invoice_line_tax_id:
                outValue = invoiceLine.invoice_line_tax_id[0].amount * 100
                break
        return "%i" % outValue

    def __init__(self, cr, uid, name, context):
        super(omnia_ddt_parser, self).__init__(cr, uid, name, context=context)
        self.cursor = cr
        self.uid = uid
        self.localcontext.update({
            'getSelectionValue': self.getSelectionValue,
            'convertToSiNo': self.convertToSiNo,
            'ifTrueEmpty': self.ifTrueEmpty,
            'get_logo_path_by_name': self.get_logo_path_by_name,
            'getPaymentTerm': self.getPaymentTerm,
            'getIvaValue': self.getIvaValue,
        })
