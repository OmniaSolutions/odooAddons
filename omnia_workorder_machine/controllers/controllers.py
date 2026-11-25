# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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
import logging
import json
import mimetypes
from odoo import _, http
from odoo.http import request, Response, Controller


class WebsiteWorkorderControllerByUser(Controller):

    def renderTemplate(self, templateName, values):
        return request.render(templateName, values)

    def forceRender(self, templateName, vals):
        resp = Response(template=templateName, qcontext=vals)
        tableHtml = resp.render()
        return tableHtml

    @http.route('/mrp_omnia/workorder_by_user')
    def workorderByUser(self, **post):
        logging.info('WorkorderMachine called')
        values = post
        values['hide_user'] = False
        return self.renderTemplate('omnia_workorder_machine.by_user', values)

    @http.route(['/mrp_omnia/render_workorder_by_user/<int:user_id>'], type='json')
    def render_workorder_by_user(self, user_id, **post):
        values = post
        lines = request.env['mrp.workorder'].getWorkordersByUser(user_id, listify=True)
        logging.info("Lines %r" % lines)
        values['wo_lines'] = lines
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table', values)

    @http.route(['/mrp_omnia/render_workorder_by_employee/<int:employee_id>'], type='json')
    def render_workorder_by_employee(self, employee_id, **post):
        values = post
        lines = request.env['mrp.workorder'].getWorkordersByEmployee(employee_id, listify=True)
        logging.info("Lines %r" % lines)
        values['wo_lines'] = lines
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table', values)


    @http.route(['/mrp_omnia/render_workorder_all/<int:manufactory_id>/<int:workcenter_id>'], type='json')
    def render_workorder_all(self,
                             manufactory_id=False,
                             workcenter_id=False,
                             **post):
        domain = []
        if manufactory_id:
            domain.append(['production_id', '=', manufactory_id])
        if workcenter_id:
            domain.append(['workcenter_id', '=',workcenter_id])
        values = post
        lines = request.env['mrp.workorder'].getWorkordersByDomain(domain, listify=True)
        logging.info("Lines %r" % lines)
        values['wo_lines'] = lines
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table_all', values)
    
    @http.route(['/mrp_omnia/workorder_machine/<int:workcenter_id>'])
    def workoder_machine_wc(self, workcenter_id, **post):
        logging.info('WorkorderMachine with workcenter %r called' % (workcenter_id))
        values = post
        return self.renderTemplate('omnia_workorder_machine.template_workorder_machine', values)

    @http.route(['/mrp_omnia/get_user_name/<int:user_id>'], type='json')
    def get_user_name(self, user_id):
        user_id = request.env['res.users'].sudo().browse(user_id)
        if user_id and user_id.exists():
            try:
                return "<b>%s %s</b>" % (user_id.lastname, user_id.firstname)
            except Exception as ex:
                logging.error(ex)
                msg = "<b>%s</b>" % (user_id.name)
                return msg
        else:
            return "<b>No User For id: %r</b>" % user_id

    @http.route(['/mrp_omnia/get_employee_name/<int:employee_id>'], type='json')
    def get_employee_name(self, employee_id):
        employee_id = request.env['hr.employee'].sudo().browse(employee_id)
        if employee_id and employee_id.exists():
            msg = "<b>%s</b>" % (employee_id.name)
            return msg
        else:
            return "<b>No User For id: %r</b>" % employee_id

    @http.route(['/mrp_omnia/workorder_machine/<int:workcenter_id>/<int:workorder_id>'], type='json')
    def workoder_machine_wc_wo(self, workcenter_id, workorder_id, **post):
        logging.info('WorkorderMachine with workcenter %r and workorder %r called' % (workcenter_id, workorder_id))
        values = post
        lines = request.env['mrp.workorder'].getWorkorders(workcenter_id, workorder_id, listify=True)
        values['wo_lines'] = lines
        return self.forceRender('omnia_workorder_machine.template_workorder_machine_table', values)

    @http.route('/mrp_omnia/print_label/<string:internal_ref>', type='http', auth='user')
    def print_sale_details(self, internal_ref, **kw):
        if internal_ref:
            prodList = request.env['product.product'].search([('default_code', '=', internal_ref)])
            if prodList:
                wizard = request.env['product.label.layout'].create({
                    'product_ids': [(6, 0, prodList.ids)],
                })
                xml_id, data = wizard._prepare_report_data()
                rep = request.env.ref(xml_id)
                pdfContent, _fileType = rep._render_qweb_pdf(rep, prodList.product_tmpl_id.ids, data=data)
                headers = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdfContent))]
                return request.make_response(pdfContent, headers=headers)
        return None

    @http.route(['/mrp_omnia/workorder_start'], auth='public', type='json')
    def workorder_start(self, wo_id=None, wo_ids=None, **post):
        logging.info(f"Workorder Start called. wo_id={wo_id}, wo_ids={wo_ids}")
        user_id = int(post.get('user_id', 0))
        employee_id = int(post.get('employee_id', 0))
        Workorder = request.env['mrp.workorder']
        if wo_ids:
            for wid in wo_ids:
                Workorder.startWork(int(wid), user_id, employee_id)
            return {
                "status": "success",
                "message": "Multiple WO started",
            }
        if wo_id:
            Workorder.startWork(int(wo_id), user_id, employee_id)
            return {"status": "success", "message": "Single WO started"}
        return {"status": "error", "message": "No workorder ID provided"}

    @http.route(['/mrp_omnia/workorder_pause'], auth='public', type='json')
    def workorder_pause(self, wo_id=None, wo_ids=None, **post):
        user_id = int(post.get('user_id', 0))
        employee_id = int(post.get('employee_id', 0))
        Workorder = request.env['mrp.workorder']
        if wo_ids:
            for wid in wo_ids:
                Workorder.pauseWork(int(wid), user_id, employee_id)
            return {
                "status": "success",
                "message": "Multiple workorders paused",
            }
        if wo_id:
            Workorder.pauseWork(int(wo_id), user_id, employee_id)
            return {
                "status": "success",
                "message": "Single workorder paused"
            }
        return {"status": "error", "message": "No workorder ID provided"}

    @http.route(['/mrp_omnia/workorder_resume'], auth='public', type='json')
    def workorder_resume(self, wo_id=None, wo_ids=None, **post):
        user_id = int(post.get('user_id', 0))
        employee_id = int(post.get('employee_id', 0))
        Workorder = request.env['mrp.workorder']
        if wo_ids:
            for wid in wo_ids:
                Workorder.resumeWork(int(wid), user_id, employee_id)
            return {
                "status": "success",
                "message": "Multiple workorders resumed",
            }
        if wo_id:
            Workorder.resumeWork(int(wo_id), user_id, employee_id)
            return {
                "status": "success",
                "message": "Single workorder resumed"
            }
        return {"status": "error",
                "message": "No workorder ID provided"}

    @http.route(['/mrp_omnia/workorder_record'], auth='public', type='json')
    def workorder_record(self, wo_id, n_pieces, n_scrap, **post):
        logging.info('Workorder record called wo_id %r' % (wo_id))
        res = False
        if wo_id:
            wo_id = int(wo_id)
            user_id = post.get('user_id', 0)
            employee_id = int(post.get('employee_id', 0))
            operation_note = post.get('operation_note')
            res = request.env['mrp.workorder'].recordWork(wo_id, n_pieces, n_scrap, user_id, employee_id, operation_note)
        return res

    @http.route('/mrp_omnia/get_worksheet/<int:mrp_workorder_id>', type='http')
    def get_worksheet(self, mrp_workorder_id):
        workorder = request.env['mrp.workorder'].sudo().browse(mrp_workorder_id)
        operation = workorder.operation_id
        if not operation:
            return request.not_found()
        point = operation.quality_point_ids.filtered(lambda p: p.worksheet_document)[:1]
        if not point:
            return request.not_found()
        doc = point.worksheet_document
        mimetype = doc.mimetype or 'application/octet-stream'
        filename = doc.filename or workorder.display_name
        ext = mimetypes.guess_extension(mimetype) or ''
        if ext and not filename.lower().endswith(ext.lower()):
            filename += ext
        headers = [
            ('Content-Type', mimetype),
            ('Content-Length', len(doc.content)),
            ('Content-Disposition', 'inline; filename="%s"' % filename),
        ]
        return request.make_response(doc.content, headers=headers)
    
    @http.route('/mrp_omnia/workorder_machine_all', type='http')
    def workoder_machine_wc_all(self, **post):
        values = post
        return self.renderTemplate('omnia_workorder_machine.workorder_machine_all', values)


    @http.route(['/mrp_omnia/name_get_generic/<string:object_name>/<string:name_like>',
                 '/mrp_omnia/name_get_generic/<string:object_name>/<string:name_like>/<string:extra_domain>'], type='json')
    def name_get_generic(self, object_name, name_like, extra_domain=False, **post):
        logging.info('name_get_generic/%s/%s' % (object_name, name_like))
        out = []
        domain = [('name', 'ilike', name_like)]
        if (extra_domain):
            domain.append(json.loads(extra_domain))
        for obj_generic in request.env[object_name.strip()].sudo().search(domain,
                                                                          limit=50):
            out.append((obj_generic.id, obj_generic.name))
        return {'data': out}



class WebsiteWorkorderControllerSimple(Controller):

    def renderTemplate(self, templateName, values):
        return request.render(templateName, values)

    @http.route('/mrp_omnia/workorder_simple', csrf=False)
    def workcenter_main_form(self, *arg, **kargs):
        return request.render('omnia_workorder_machine.workorder_simple','')

    def get_workcenter_table(self,
                             workcenter_id,
                             status="READY", csrf=False):
        if status =='READY':
            data = {'data':  request.env['mrp.workorder'].getReadyWorkorder(workcenter_id)}
            return self.renderTemplate('omnia_workorder_machine.workorder_simple_table', data)
        elif status == 'INPROGRESS':
            data = {'data':  request.env['mrp.workorder'].getInProgressWorkorder(workcenter_id)}
            return self.renderTemplate('omnia_workorder_machine.workorder_simple_table', data)
        return ''
    
    @http.route('/mrp_omnia/workorder_simple_post', methods=['POST'], csrf=False)
    def workcenter_main_form_post(self, *arg, **kargs):
        workorder_id = kargs.get('workorder_id')
        request.env['mrp.workorder'].confirm_start_workorder(workorder_id)
        return 'OK'
    
    @http.route('/mrp_omnia/active_workorder_simple', csrf=False)
    def get_active_workorder_table(self, *arg, **kargs):
        workcenter_id = self.getWorkcenterFromRequest()
        if workcenter_id:
            return self.get_workcenter_table(workcenter_id, status='INPROGRESS')
        return ""
        
    @http.route('/mrp_omnia/ready_workorder_simple', csrf=False)
    def get_ready_workorder_table(self, *arg, **kargs):
        workcenter_id = self.getWorkcenterFromRequest()
        if workcenter_id:
            return self.get_workcenter_table(workcenter_id, status='READY')
        return ""
    
    @http.route('/mrp_omnia/workcenter_name', csrf=False)
    def get_workcenter_name(self, *args, **kargs):
        workcenter_id = self.getWorkcenterFromRequest()
        if workcenter_id:
            return workcenter_id.name
        return request.httprequest.host

    def getWorkcenterFromRequest(self):
        host = request.httprequest.host
        workcenter_ids = request.env['mrp.workcenter'].search([('web_ip_address', '=', host)])
        for workcenter_id in workcenter_ids:
            return workcenter_id 
        logging.warning("No workcenter found for address : %r" % host)
                        
