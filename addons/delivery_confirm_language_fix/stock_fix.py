# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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

from openerp.osv import osv
import logging


class StockPickingOut(osv.osv):
    _inherit = "stock.picking"
    _name = "stock.picking"

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms picking.
        @return: True
        """
        logging.info('Start fixing language by Omnia')
        if not context:
            context = {}
        userLang = self.pool.get('res.users').browse(cr, uid, uid).lang
        context['lang'] = userLang
        return super(StockPickingOut, self).action_confirm(cr, uid, ids, context=context)

StockPickingOut()