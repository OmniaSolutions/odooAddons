# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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
from odoo import models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    
    def _prepare_timeline_vals(self, duration, date_start, date_end=False):
        ret = super(MrpWorkorder, self)._prepare_timeline_vals(duration, date_start, date_end)
        employee_mrp_id = self.env.context.get('employee_mrp_id')
        if employee_mrp_id:
            ret['employee_mrp_id'] = employee_mrp_id
        return ret
