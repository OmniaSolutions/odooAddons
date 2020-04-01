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
from odoo import _

class ServerConfig(models.Model):
    _name = 'server.config'
    _description = "Server configurations"
    
    partner_id = fields.Many2one("res.partner","Customer")
    odoo_version = fields.Char(string=_('Odoo Version'))
    ip_server = fields.Char(string=_('IP Server'))
    user_login_odoo = fields.Char(string=_('User Login'))
    password_login_odoo = fields.Char(string=_('Password Login'))
    db_name = fields.Char(string=_('DB Name'))
    
    open_vpn = fields.Binary(string=_('Open VPN'))
    open_vpn_fname = fields.Char(string=_('Open VPN Filename'))
    open_vpn_login = fields.Char(string=_('Open VPN Login'))
    open_vpn_password = fields.Char(string=_('Open VPN Password'))
    
    ip_ssh = fields.Char(string=_('IP SSH'))
    user_ssh = fields.Char(string=_('User SSH'))
    password_ssh = fields.Char(string=_('Password SSH'))
    user_root_ssh = fields.Char(string=_('User Root SSH'))
    password_root_ssh = fields.Char(string=_('Password Root SSH'))
    ssh_key = fields.Char(string=_('SSH Key'))
    comando_ssh = fields.Char(string=_('Command SSH'))
    
    client_port = fields.Char(string=_('Client Port'))
    client_protocol = fields.Char(string=_('Client Protocol'))
    path_internal_network = fields.Char(string=_('Internal Network Path'))
    used_cad = fields.Many2many("cad.programs",string=_("Used CAD"))
    
    path_file_config = fields.Char(string=_('Config File Path'))
    path_file_log = fields.Char(string=_('Log File Path'))
    path_share = fields.Char(string=_('Share Path'))
    path_backup = fields.Char(string=_('Backup Path'))
    path_filestore = fields.Char(string=_('Filestore Path'))
    path_demon = fields.Char(string=_('Demon Path'))
    path_addons = fields.Text(string=_('Addons Path'))

    migration_code = fields.Char(string=_('Migration Code'))
    notes = fields.Text(string=_('Additional Notes'))
