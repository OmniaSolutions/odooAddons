# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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

'''
Created on Dec 7, 2017

@author: daniel
'''

# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WorkCenters(http.Controller):
    @http.route('/workcenter/', auth='public')
    def index(self, **kw):
        wcObj = request.env['mrp.workcenter']
        woObj = request.env['mrp.workorder']
        wcBrwsList = wcObj.search([], limit=30)
        wcDict = {}
        for wcBrws in wcBrwsList:
            wcId = wcBrws.id
            if wcId not in wcDict.keys():
                wcDict[wcId] = {'work_orders': [],
                                'wc_obj': wcBrws,}
            woBrwsList = woObj.search([('workcenter_id', '=', wcBrws.id)], limit=5, order='id DESC')
            for woBrws in woBrwsList:
                wcDict[wcId]['work_orders'].append(woBrws)
        
        return http.request.render('omnia_production_workcenter.index', {
            'workcenter_dict': wcDict,
        })
