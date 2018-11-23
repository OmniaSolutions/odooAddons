'''
Created on Oct 14, 2018

@author: daniel
'''
import logging
import json
from odoo import http
from odoo import _
from odoo.http import request
from odoo.http import Response
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


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
        lines = request.env['mrp.workorder'].getWorkorders(workcenter_id, workorder_id)
        values['wo_lines'] = self.listify(lines)
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table', values)
        
    def forceRender(self, templateName, vals):
        resp = Response(template=templateName, qcontext=vals)
        tableHtml = resp.render()
        return tableHtml

    def listify(self, woList):
        lines = []
        for dictRes in woList:
            lines.append(
                [
                    dictRes.get('wo_id', ''),
                    dictRes.get('product_name', ''),
                    dictRes.get('product_default_code', ''),
                    dictRes.get('wo_name', ''),
                    dictRes.get('production_name', ''),
                    dictRes.get('wo_description', ''),
                    dictRes.get('wo_state', ''),
                    dictRes.get('qty', 0),
                    dictRes.get('date_planned', ''),
                    str(dictRes.get('is_user_working', False)),
                    ]
                )
        return lines
        
    @http.route('/make_login', auth='none', methods=['POST'], csrf=False)
    def make_login(self, **post):
        logging.info('Make Login')
        database = post.get('database', '')
        user = post.get('user', '')
        pwd = post.get('password', '')
        post['csrf_token'] = ''
        post['user_logged'] = False
        if database and user and pwd:
            uid = request.session.authenticate(database, user, pwd)
            if uid:
                csrf_token = request.csrf_token()
                post['csrf_token'] = csrf_token
                post['user_logged'] = True
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

    @http.route(['/web/workorder_stop'], auth='public', type='json')
    def workorder_stop(self, wo_id, n_pieces, **post):
        logging.info('Workorder Stop called wo_id %r' % (wo_id))
        res = False
        if wo_id:
            wo_id = int(wo_id)
            res = request.env['mrp.workorder'].stopWork(wo_id, n_pieces)
        return res

    @http.route('/setcookie', methods = ['POST', 'GET'])
    def setcookie(self, **post):
        logging.info('Set Cookie')

