# -*- coding: utf-8 -*-
##############################################################################
# this module is derived from the article 
#Copyright (c) https://www.odoo.com/forum/help-1/question/how-to-remove-manage-databases-2615
# All Right Reserved
#
#
# Author : Boscolo Matteo (Omniasolutions)
# Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
# All Right Reserved
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name': 'Remove Manage db',
    'description': """
This module remove the manage db from the login screen
======================================================


""",
    'version': '0.1',
    'depends': ['web'],
    'author': 'OmniaSolutions',
    'category': 'security', 
    'url': 'http://http://www.omniasolutions.eu/',
    'data': [ ],
    'qweb' : [
              "static/src/xml/loginOverload.xml",
              ],
              
    
    'installable'   : True,
    'auto_install'  : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
