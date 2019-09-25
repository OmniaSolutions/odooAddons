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

from openerp import models, fields, api
import logging
import base64
import tempfile
import os


class ClientMacro(models.Model):
    _name = 'client.macro'

    name = fields.Char('Attachment Name', required=True)
    integration = fields.Selection( [ 
            ('solidworks','Solidworks'), 
            ('solidedge','SolidEdge'),
            ('thinkdesign','ThinkDesign'),
            ('autocad','Autocad'),
            ('inventor','Inventor'),
            ('freecad','Freecad'),
            ],
                'Integration', required=True)
    db_datas = fields.Binary('Database Data')
    module_name = fields.Char('Module Name', default='Module1', required=True)
    procedure_name = fields.Char('Procedure Name', default='main', required=True)
    
    @api.multi
    def getSingleMacroInfos(self):
        for macroBrws in self:
            logging.info('Getting Macro Infos %r -- %r' % (macroBrws.name, macroBrws.integration))
            return (macroBrws.name, macroBrws.integration, macroBrws.db_datas, macroBrws.module_name, macroBrws.procedure_name)
    
    @api.multi
    def getMacrosInfos(self):
        out = []
        for macroBrws in self:
            out.append(macroBrws.getSingleMacroInfos())
        return out
