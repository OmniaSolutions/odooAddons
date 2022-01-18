##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError


class TemporaryPickAttach(models.TransientModel):
    _name = 'temporary.pick.attach'

    picking_ids = fields.Many2many('stock.picking', string="Picking Ids")
    attachment = fields.Binary("Dcoument to attach")
    attachment_name = fields.Char("Document Filename")

    @api.model
    def default_get(self, fields_list):
        ret = super(TemporaryPickAttach, self).default_get(fields_list)
        return ret

    @api.multi
    def action_attach_to_pickings(self):
        attachment = self.env['ir.attachment']
        for wizard in self:
            document = wizard.attachment
            if not document or not wizard.attachment_name:
                raise UserError('You need to provide the document to attach.')
            if not wizard.picking_ids:
                raise UserError('You need to provide at least a picking to attach the documen to.')
            for picking in wizard.picking_ids:
                attachment.create({
                    'name': wizard.attachment_name,
                    'datas': document,
                    'res_model': picking._name,
                    'res_id': picking.id,
                    'res_name': picking.display_name,
                    'datas_fname': wizard.attachment_name,
                    })
        return {
            'name': _('Pickings'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'res_model': wizard.picking_ids._name,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', wizard.picking_ids.ids)],
            'context': {}
        }
