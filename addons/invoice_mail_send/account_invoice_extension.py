# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
#    All Right Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on Jan 12, 2016

@author: Daniel Smerghetto
'''

from osv import osv, fields
import logging

class omnia_account_invoice_mail(osv.osv):
    
    _name = "account.invoice"
    _inherit = ['account.invoice']
    
    def generate_mails(self, cr, uid, ids, alsoCompanyAddress=False, context={}):
        for invoiceBrows in self.browse(cr, uid, ids):
            if invoiceBrows.state != 'open':
                continue
            email_to = []
            customerBrws = invoiceBrows.partner_id
            for childBrws in customerBrws.child_ids:
                if childBrws.type == 'invoice' and childBrws.email:
                    email_to.append(childBrws.email)
            if alsoCompanyAddress:
                customerEmail = customerBrws.email
                email_to.append(customerEmail)
#             user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#             mail_values = {
#                  'email_from': user.partner_id.email,
#                  'email_to': email_to,
#                  'subject': 'Invitation to follow %s' % invoiceBrows.name_get()[0][1],
#                  'body_html': '''  ''',
#                  'auto_delete': True,
#                  'type': 'email',
#             }
#             mail_obj = self.pool.get('mail.mail')
#             mail_id = mail_obj.create(cr, uid, mail_values, context=context)
#             mail_obj.send(cr, uid, [mail_id], recipient_ids=[customerBrws.id], context=context)
            
            
            
            try:
                ir_model_data = self.pool.get('ir.model.data')
                template_id = ir_model_data.get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')[1]
                #templateBrws = ir_model_data.browse(cr, uid, template_id)
            except ValueError:
                template_id = False
            context.update({
                'default_email_to': email_to,
                })
            self.pool.get('email.template').send_mail(cr, uid, template_id, invoiceBrows.id, force_send=True, context=context)

omnia_account_invoice_mail()


class plm_temporary_mail(osv.osv_memory):
    _name = "temporary.mail"
# Specialized Actions callable interactively

    def action_generate_mails(self, cr, uid, ids, context=None):
        """
            Call generate mails
        """
        if 'active_ids' not in context:
            return False
        objPoolProduct = self.pool.get('account.invoice')
        objPoolProduct.generate_mails(cr, uid, context.get('active_ids',[]))
        return False


plm_temporary_mail()