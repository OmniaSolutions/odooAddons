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
from odoo import _, api, models, fields
from odoo.exceptions import UserError


class TimesheetDocument(models.Model):
    _name = 'timesheet.document'
    _inherit = ['mail.thread']
    _description = 'Timesheet Document'

    name = fields.Char(
        string="Timesheet Name",
        readonly=True,
        copy=False,
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
        ],
        string='Status',
        default='draft',
        index=True,
        readonly=True,
        tracking=True,
        copy=False,
        help=(
            "* Draft: when the Timesheet Document is created\n"
            "* Confirmed: when Timesheet document is ready to be delivered"
        ),
    )

    timesheet_customer_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        tracking=True,
    )

    timesheet_reference_id = fields.Many2one(
        'res.partner',
        string='Reference',
        required=True,
        tracking=True,
    )

    timesheet_date = fields.Date(
        string="Timesheet Date",
        default=fields.Date.context_today,
        tracking=True,
    )

    timesheet_timesheet_line = fields.Many2many(
        'account.analytic.line',
        string='Timesheet Lines',
    )

    timesheet_total = fields.Float(
        string='Total Time',
        compute='_compute_total',
        store=True,
    )

    timesheet_note = fields.Text(
        string="Note",
    )

    def action_confirm(self):
        """
            write the confirmed status
        """
        if len(self.timesheet_timesheet_line) > 0:
            for line in self.timesheet_timesheet_line:
                if line.timesheet_document_ref is not False:
                    if line.timesheet_document_ref != self.name:
                        raise UserError(
                            _('You cannot confirm a timesheet that have line already refereed line id: %r Ref: %r' % (
                                line.id, line.timesheet_document_ref)))
            self.state = 'confirmed'
            if not self.name:
                self.name = self.env['ir.sequence'].next_by_code('timesheet.document')
            for line in self.timesheet_timesheet_line:
                line.timesheet_document_ref = self.name
        else:
            raise UserError(_('You cannot confirm a timesheet that have no line'))

    def action_draft(self):
        """
            write draft status
        """
        self.state = 'draft'

    @api.depends('timesheet_timesheet_line.unit_amount')
    def _compute_total(self):
        """
            compute the total amount of time spent
        """
        total = 0
        for l in self.timesheet_timesheet_line:
            total = total + l.unit_amount
        self.timesheet_total = total

    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        try:
            template = self.env.ref(
                'timesheet_document.email_template_timesheet_document',
                raise_if_not_found=False
            )
        except ValueError:
            template = False
        try:
            compose_form = self.env.ref(
                'mail.email_compose_message_wizard_form',
                raise_if_not_found=False
            )
        except ValueError:
            compose_form = False
        ctx = dict()
        ctx = {
            'default_model': 'timesheet.document',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Timesheet'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')] if compose_form else [],
            'target': 'new',
            'context': ctx,
        }