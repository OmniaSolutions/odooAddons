# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (https://www.omniasolutions.website)
#    Copyright (c) 2018 Omniasolutions (https://www.omniasolutions.website)
#    Copyright (c) 2021 Omniasolutions (https://www.omniasolutions.website
#    All Right Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    omnia_mrp_orig_move = fields.Many2one("stock.move",
                                          copy=False,
                                          string="Original Move")
    project_id = fields.Many2one('project.project', string="Project")
