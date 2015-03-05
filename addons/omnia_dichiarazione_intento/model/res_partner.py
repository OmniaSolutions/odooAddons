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
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class res_partner(models.Model):
    _inherit = 'res.partner'
    dichiarazione_intento=fields.Many2many('dichiarazione.intento',
                                           'dichiarazione_intento_res_partner_rel',
                                           'partner_id',
                                           'dichiarazione_intento_id')
res_partner()   