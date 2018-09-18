'''
Created on 26 Apr 2018

@author: dsmerghetto
'''
import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError


class StockRecicleProduct(models.Model):
    _name = "stock.recycle_product"

    @api.model
    def _compute_default_from_location(self):
        scrappedLoc = False
        try:
            scrappedLoc = self.env.ref('stock.stock_location_scrapped')
        except Exception as ex:
            logging.error("stock.stock_location_scrapped not found !! %r " % ex)
        return scrappedLoc

    @api.model
    def _compute_default_to_location(self):
        stockLoc = False
        try:
            company = self.env.user.company_id
            partner = company.partner_id
            stockLoc = partner.property_stock_customer
        except Exception as ex:
            logging.warning("Unable to _compute_default_to_location %r " % ex)
        return stockLoc

    @api.model
    def create(self, vals):
        if not vals.get('name', False):
            vals['name'] = self.env['ir.sequence'].next_by_code("RECICLE_NUMBERING")
        return super(StockRecicleProduct, self).create(vals)

    @api.multi
    def unlink(self):
        for move in self.env['stock.move'].search([('recycle_id', 'in', self.ids)]):
            move._action_cancel()
            move.sudo().unlink()
        return super(StockRecicleProduct, self).unlink()

    #  For multi-company create company from and company to?
    #  And recycle location has to change?
    name = fields.Char(_('name'), readonly=True)
    description = fields.Text(_('Notes'))
    from_product_id = fields.Many2one('product.product', _('From Product'), required=True)
    to_product_id = fields.Many2one('product.product', _('To Product'), required=True)
    from_qty = fields.Float(_('From Quantity'), required=True)
    to_qty = fields.Float(_('To Quantity'), required=True)
    from_location = fields.Many2one('stock.location', _('From Location'), required=True, default=_compute_default_from_location)
    to_location = fields.Many2one('stock.location', _('To Location'), required=True, default=_compute_default_to_location)
    from_product_uom = fields.Many2one('product.uom', _('From Unit of measure'), related='from_product_id.uom_id')
    to_product_uom = fields.Many2one('product.uom', _('To Unit of measure'), related='to_product_id.uom_id')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed')],
                             default='draft')

    @api.multi
    def action_confirm(self):
        for recycle_product_id in self:
            recycle_product_id.state = 'confirmed'
            recycle_product_id.button_recycle()

    @api.multi
    def action_reset(self):
        for recycle_product_id in self:
            recycle_product_id.state = 'draft'
            recycle_product_id.button_reset()

    @api.one
    def button_recycle(self):
        recycleLoc = self.env.ref('omnia_mrp_recycle.location_to_recycle')
        moveObj = self.env['stock.move']
        self.createMove(moveObj, self.from_product_id, self.from_qty, self.from_location, recycleLoc)
        self.createMove(moveObj, self.to_product_id, self.to_qty, recycleLoc, self.to_location)
        return {
            'name': _("Recycle Moves"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def button_open_moves(self):
        moves = self.env['stock.move'].search([('recycle_id', 'in', self.ids)])
        return {
            'name': _("Moves"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', moves.ids)],
        }

    @api.one
    def createMove(self, moveObj, prodBrws, prodQty, location_from, location_dest):
        dateNow = datetime.datetime.now()
        moveBrowe = moveObj.create({
            'name': prodBrws.name,
            'date': dateNow,
            'date_expected': dateNow,
            'product_id': prodBrws.id,
            'product_uom': prodBrws.uom_id.id,
            'product_uom_qty': prodQty,
            'location_id': location_from.id,
            'location_dest_id': location_dest.id,
            'company_id': self.env.user.company_id.id,
            'production_id': False,
            'origin': prodBrws.name,
            'group_id': False,
            'propagate': False,
            'recycle_id': self.id
        })
        moveBrowe._action_confirm()
        moveBrowe.quantity_done = prodQty
        moveBrowe._action_done()
        return moveBrowe
