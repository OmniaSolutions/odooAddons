##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 02/mar/2015 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
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
Created on 02/mar/2015

@author: mboscolo
'''
from datetime import datetime

from openerp import models, fields, api, _
from openerp.exceptions import Warning

class DichiarazioneIntento(models.Model):

    _name = 'dichiarazione.intento'  # Model identifer used for table name
    _inherit = ['mail.thread']
    name        = fields.Char("Numero")
    date_start  = fields.Date(string="Start Date",
                                                readonly=True,
                                                states={'draft': [('readonly', False)]})
    date_end    = fields.Date(string="End Date",
                                                readonly=True,
                                                states={'draft': [('readonly', False)]})
    state       = fields.Selection([('draft','Draft'),
                                    ('confirmed','Active'),
                                    ('expired','Expired')], 
                                                      string='Status', index=True, readonly=True, default='draft',
                                                      track_visibility='onchange', copy=False,
                                        help=" * The 'Draft' status is used when the document is in draft not confirmes.\n"
                                             " * The 'Confermed' when the document is ready and not expired\n"
                                             " * The 'Expired' is set automaticaly when the end date arrived\n"
                                                 )
    
    @api.v8
    def checkValidity(self):
        """
            check the validity of the document and set to expired in case of document expired
        """
        if self.date_end<datetime.now():
            self.state='expired'
    
    
DichiarazioneIntento()    