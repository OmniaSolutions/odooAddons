##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 22/feb/2015 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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
Created on 22/feb/2015

@author: mboscolo
'''
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class TimesheetDocument(models.Model):

    _name = 'timesheet.document'  # Model identifier used for table name
    _inherit = ['mail.thread']

    def get_now(self):
        return datetime.now()
    #
    # fields
    #
    name = fields.Char("Timesheet Name",
                       readonly=True,
                       states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confermed')],
                             string='Status',
                             index=True,
                             readonly=True,
                             default='draft',
                             track_visibility='onchange',
                             copy=False,
                             help=""" * The 'Draft' status is used when the Timesheet Document is created.\n
                             * The 'Confermed' when Timesheet document is ready to be delivered to the customer\n""")
    timesheet_customer_id = fields.Many2one('res.partner',
                                            string='Partner',
                                            required=True,
                                            readonly=True,
                                            states={'draft': [('readonly', False)]})
    timesheet_reference_id = fields.Many2one('res.partner',
                                             string='Reference',
                                             required=True,
                                             readonly=True,
                                             states={'draft': [('readonly', False)]})
    timesheet_date = fields.Date(string="Timesheet Date",
                                 readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=get_now)
    timesheet_timesheet_line = fields.Many2many('account.analytic.line',
                                                readonly=True,
                                                states={'draft': [('readonly', False)]})

    timesheet_total = fields.Float(compute='compute_total',
                                   readonly=True,
                                   states={'draft': [('readonly', False)]})
    timesheet_note = fields.Text(string="Note",
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})

    @api.one
    def action_confirm(self):
        """
            write the confirmed status
        """
        if len(self.timesheet_timesheet_line) > 0:
            for line in self.timesheet_timesheet_line:
                if line.timesheet_document_ref is not False:
                    if line.timesheet_document_ref != self.name:
                        raise Warning(_('You cannot confirm a timesheet that have line already refereed line id: %r Ref: %r' % (line.id, line.timesheet_document_ref)))
            self.state = 'confirmed'
            if not self.name:
                self.name = self.env['ir.sequence'].next_by_code('timesheet.document')
            for line in self.timesheet_timesheet_line:
                line.timesheet_document_ref = self.name
        else:
            raise Warning(_('You cannot confirm a timesheet that have no line'))

    @api.one
    def action_draft(self):
        """
            write draft status
        """
        self.state = 'draft'

    @api.one
    def compute_total(self):
        """
            compute the total amount of time spent
        """
        total = 0
        for l in self.timesheet_timesheet_line:
            total = total + l.unit_amount
        self.timesheet_total = total

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('timesheet_document', 'email_template_timesheet_document')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'timesheet.document',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
