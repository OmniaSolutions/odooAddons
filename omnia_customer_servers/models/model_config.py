##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2020 OmniaSolutions (<https://omniasolutions.website>). All Rights Reserved
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
# Leonardo Cazziolati
# leonardo.cazziolati@omniasolutions.eu
# 28-02-2020

from odoo import models, fields

class ServerConfig(models.Model):
    _name = 'server.config'
    _description = "Server configurations"
    
    partner_id = fields.Many2one("res.partner","Customer")
    odoo_version = fields.Char(string='Odoo Version')
    ip_server = fields.Char(string='IP Server')
    user_login_odoo = fields.Char(string='User Login')
    password_login_odoo = fields.Char(string='Password Login')
    open_vpn = fields.Binary(string='Open VPN')
    open_vpn_login = fields.Char(string='Open VPN Login')
    open_vpn_password = fields.Char(string='Open VPN Password')
    ip_ssh = fields.Char(string='IP SSH')
    user_ssh = fields.Char(string='User SSH')
    password_ssh = fields.Char(string='Password SSH')
    user_root_ssh = fields.Char(string='User Root SSH')
    password_root_ssh = fields.Char(string='Password Root SSH')
    ssh_key = fields.Char(string='SSH Key')
    comando_ssh = fields.Char(string='Command SSH')
    path_file_config = fields.Char(string='Config File Path')
    path_file_log = fields.Char(string='Log File Path')
    path_addons = fields.Text(string='Addons Path')
    client_port = fields.Char(string='Client Port')
    client_protocol = fields.Char(string='Client Protocol')
    db_name = fields.Char(string='DB Name')
    notes = fields.Text(string='Additional Notes')
    # used_cad = fields.one2many(string='CAD utilizzato')
