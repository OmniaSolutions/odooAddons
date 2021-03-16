# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 15 Mar 2021

@author: dsmerghetto
'''
from openerp.tools.translate import _
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID


class ExportConservationParams(osv.TransientModel):
    _name = 'fatturapa.exportconservationparams'

    _columns = {
        'login_user': fields.char('Login'),
        'login_pass': fields.char('Password'),
        }

    def setup_credentials(self, cr, uid, ids, context={}):
        config_pool = self.pool['ir.config_parameter']
        for wizard in self.browse(cr, uid, ids, context):
            config_pool.set_param(cr, SUPERUSER_ID, 'DOCFLY_FTP_USER', wizard.login_user)
            config_pool.set_param(cr, SUPERUSER_ID, 'DOCFLY_FTP_PWS', wizard.login_pass)
        