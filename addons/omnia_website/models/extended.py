# -*- encoding: utf-8 -*-
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

from openerp import tools
from openerp.osv import osv, fields


class product_template(osv.Model):
    _inherit = "product.template"

    _columns = {
        'client_name': fields.char("Client Name", help="Name for activation code evaluation."),
    }

    _defaults = {
        'client_name': lambda *a: False,
    }

class activated_line(osv.osv):
    _name = 'sale.order.line.activated'
    _columns = {
               'sequence': fields.integer('Sequence'),
               'service_id': fields.char('Service ID code'),
               'line_id': fields.integer('Order line ID'),
               'node_id': fields.char('Node ID code'),
               'activation_code': fields.char('Activation Code'),
                }

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
 
    _columns = {
        'activated': fields.one2many('sale.order.line.activated', 'line_id', 'Activation Codes'),
    }
 
    _defaults = {
        'activated' : False,
    }

    def unlink(self,cr, uid, ids, context=None):
 
        activated_obj=self.pool.get('sale.order.line.activated')
        code_ids = activated_obj.search(cr, uid, [("line_id", "in", ids),], context=context)
        activated_obj.unlink(cr, uid, code_ids, context)

        return super(sale_order_line, self).unlink(cr, uid, ids, context)


