##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010-2019 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

    
class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    show_on_task = fields.Boolean(
        string='Show On Task',
    )

    show_on_issue = fields.Boolean(
        string='Show On Issue',
    )
