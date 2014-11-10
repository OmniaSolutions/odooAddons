import werkzeug

from openerp.addons.website_sale.controllers.main import website_sale

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

class omnia_wesite_sale(website_sale):

    @http.route(['/shop/register'], type='http', auth="public", website=True)
    def register(self, **post):

        cr, uid, context = request.cr, request.uid, request.context

        order = request.website.sale_get_order(force_create=1, context=context)

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        self.register_orderlines(order)

        return request.website.render("omnia_website.register", {})
    
    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        cr, uid, context = request.cr, request.uid, request.context

        order = request.website.sale_get_order(force_create=1, context=context)

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        
        redirection = self.check_register_orderlines(order)
        if redirection:
            return redirection
       

        values = self.checkout_values()

        return request.website.render("website_sale.checkout", values)
      
    def check_register_orderlines(self, order):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        # must have a draft sale order with lines at this point, otherwise reset
        if order:
            active_obj= pool.get('sale.order.line.activated')
            for orderLine in order.order_line:
                
                if not orderLine.activated:
                    continue

                for activated in orderLine.activated:
                    if not activated.service_id or not activated.node_id:
                        return request.redirect('/shop/register')
            

    def register_orderlines(self, order):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        # must have a draft sale order with lines at this point, otherwise reset
        if order:
            active_obj= pool.get('sale.order.line.activated')
            for orderLine in order.order_line:

                if orderLine.product_id and orderLine.product_id.product_tmpl_id:
                    if not orderLine.product_id.product_tmpl_id.client_name:
                        continue

                seq=0
                maxseq=max(range(int(orderLine.product_uom_qty)))+1             

                code_ids = active_obj.search(cr, SUPERUSER_ID, [("line_id", "=", orderLine.id),], context=context)
                codes = active_obj.browse(cr, SUPERUSER_ID, code_ids, context)
                for code in codes:
                    seq+=1
                    if code.sequence>maxseq:
                        active_obj.unlink(cr, SUPERUSER_ID, code.id, context)

                for _ in range(maxseq-seq):
                    seq+=1
                    values={'sequence':seq,'line_id':orderLine.id}
                    active_obj.create(cr, uid, values, context)
                    
    @http.route(['/shop/cart/writeToDB'], type='json', auth="public", methods=['POST'], website=True)
    def writeToDBB(self, line_id=None, value=None, fieldType = None, display=True):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        active_obj = pool.get('sale.order.line.activated')
        ordrLnAct = active_obj.browse(cr,uid,line_id,context)
        if fieldType == 'serviceID':
            active_obj.write(cr,uid,line_id,{'service_id':str(value)},context)
        elif fieldType == 'nodeID':
            active_obj.write(cr,uid,line_id,{'node_id':str(value)},context)