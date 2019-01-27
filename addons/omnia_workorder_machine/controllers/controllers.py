'''
Created on Oct 14, 2018

@author: daniel
'''
import logging
import json
import os
from odoo import http
from odoo import _
from odoo.http import request
from odoo.http import Response
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
import tempfile


class WebsiteWorkorderController(http.Controller):

    def renderTemplate(self, templateName, values):
        return request.render(templateName, values)

    @http.route(['/web/workorder_machine'], auth='public')
    def workoder_machine(self, **post):
        logging.info('WorkorderMachine called')
        values = post
        return self.renderTemplate('omnia_workorder_machine.template_workorder_machine', values)

    @http.route(['/web/workorder_machine/<int:workcenter_id>'], auth='public')
    def workoder_machine_wc(self, workcenter_id, **post):
        logging.info('WorkorderMachine with workcenter %r called' % (workcenter_id))
        values = post
        return self.renderTemplate('omnia_workorder_machine.template_workorder_machine', values)

    @http.route(['/web/workorder_machine/<int:workcenter_id>/<int:workorder_id>'], type='json')
    def workoder_machine_wc_wo(self, workcenter_id, workorder_id, **post):
        logging.info('WorkorderMachine with workcenter %r and workorder %r called' % (workcenter_id, workorder_id))
        values = post
        lines = request.env['mrp.workorder'].getWorkorders(workcenter_id, workorder_id, listify=True)
        values['wo_lines'] = lines
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table', values)

    def forceRender(self, templateName, vals):
        resp = Response(template=templateName, qcontext=vals)
        tableHtml = resp.render()
        return tableHtml

    @http.route('/make_login', auth='none', methods=['POST'], csrf=False)
    def make_login(self, **post):
        logging.info('Make Login')
        database = post.get('database', '')
        user = post.get('user', '')
        pwd = post.get('password', '')
        post['csrf_token'] = ''
        post['user_logged'] = False
        if database and user and pwd:
            try:
                uid = request.session.authenticate(database, user, pwd)
                if uid:
                    csrf_token = request.csrf_token()
                    post['csrf_token'] = csrf_token
                    post['user_logged'] = True
            except Exception as ex:
                logging.error(ex)
        return self.renderTemplate('omnia_workorder_machine.template_workorder_machine', post)

    @http.route(['/web/workorder_start'], auth='public', type='json')
    def workoder_start(self, wo_id, **post):
        logging.info('Workorder Start called wo_id %r' % (wo_id))
        res = False
        if wo_id:
            wo_id = int(wo_id)
            res = request.env['mrp.workorder'].startWork(wo_id)
        return res

    @http.route(['/web/workorder_pause'], auth='public', type='json')
    def workorder_pause(self, wo_id, **post):
        logging.info('Workorder Pause called wo_id %r' % (wo_id))
        res = False
        if wo_id:
            wo_id = int(wo_id)
            res = request.env['mrp.workorder'].pauseWork(wo_id)
        return res

    @http.route(['/web/workorder_resume'], auth='public', type='json')
    def workorder_resume(self, wo_id, **post):
        logging.info('Workorder Resume called wo_id %r' % (wo_id))
        res = False
        if wo_id:
            wo_id = int(wo_id)
            res = request.env['mrp.workorder'].resumeWork(wo_id)
        return res

    @http.route(['/web/workorder_record'], auth='public', type='json')
    def workorder_record(self, wo_id, n_pieces, n_scrap, **post):
        logging.info('Workorder record called wo_id %r' % (wo_id))
        res = False
        if wo_id:
            wo_id = int(wo_id)
            res = request.env['mrp.workorder'].recordWork(wo_id, n_pieces, n_scrap)
        return res

    @http.route('/web/print_label/<string:internal_ref>', type='http', auth='user')
    def print_sale_details(self, internal_ref, **kw):
        if internal_ref:
            prodList = request.env['product.product'].search([('default_code', '=', internal_ref)])
            if prodList:
                rep = request.env['ir.actions.report.xml'].search([('report_name', '=', 'product.report_productlabel')])
                pdfContent, _fileType = rep.render_report(prodList.ids, 'product.report_productlabel', data=None)
                tmpDir = tempfile.gettempdir()
                filePath = os.path.join(tmpDir, 'testtttt.pdf')
                with open(filePath, 'w') as writeFile:
                    writeFile.write(pdfContent)
                return pdfContent
        return None

    @http.route('/web/workorder_by_user')
    def workorderByUser(self, **post):
        logging.info('WorkorderMachine called')
        values = post
        return self.renderTemplate('omnia_workorder_machine.by_user', values)

    @http.route(['/web/render_workorder_by_user/<int:user_id>'], type='json')
    def render_workorder_by_user(self, user_id, **post):
        values = post
        lines = request.env['mrp.workorder'].getWorkordersByUser(user_id, listify=True)
        logging.info("Lines %r" % lines)
        values['wo_lines'] = lines
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table', values)
 
    @http.route(['/web/get_user_name/<int:user_id>'], type='json')
    def get_user_name(self, user_id):
        user_id = request.env['res.users'].sudo().browse(user_id)
        return "<b>%s %s</b>" % (user_id.lastname, user_id.firstname) 
        
    
    
