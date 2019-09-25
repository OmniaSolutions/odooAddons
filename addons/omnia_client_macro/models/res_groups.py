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
Created on Apr 19, 2017

@author: daniel
'''

import logging
import tempfile
import os
import base64
from openerp.osv import fields,osv
from openerp import api


class ResGroups(osv.osv):
    _name = 'res.groups'
    _inherit = 'res.groups'

    _columns = {
        'macro_ids': fields.many2many('client.macro', 'group_macro_rel', 
                         'macro_id', 'group_id', string='Macros')
    }

    @api.multi
    def getMacros(self):
        for groupBrws in self:
            logging.info('Request Macros file for user %r and group %r-%r and id %r' % (groupBrws.env.uid, groupBrws.category_id.name, groupBrws.name, groupBrws.id))
            if groupBrws.macro_ids:
                return groupBrws.macro_ids.getMacrosInfos()
        return []

    @api.multi
    def getMacroUserInfos(self):
        for groupBrws in self:
            logging.info('Request Macros info for user %r and group %r-%r and id %r' % (groupBrws.env.uid, groupBrws.category_id.name, groupBrws.name, groupBrws.id))
            if groupBrws.macro_ids:
                return groupBrws.macro_ids.getMacroUserInfos()
        return []

ResGroups()
