'''
Created on Oct 14, 2018

@author: daniel
'''
import logging
import json
import os
import base64
from odoo import _
from odoo import http
from odoo.http import request
from odoo.http import Response
from odoo.http import Controller
from odoo.addons.omnia_workorder_machine.controllers.controllers import WebsiteWorkorderControllerByUser
import tempfile


class WebsiteWorkorderControllerByEmployee(WebsiteWorkorderControllerByUser):

    @http.route('/mrp_omnia/workorder_by_employee')
    def workorderByEmployee(self, **post):
        logging.info('WorkorderMachine called')
        values = post
        values['hide_user'] = True
        return self.renderTemplate('omnia_workorder_machine.by_user', values)
