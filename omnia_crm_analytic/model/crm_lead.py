'''
Created on 3 Apr 2017

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class crm_lead(models.Model):
    '''
    extent the base class adding some new feature
    '''
    _inherit = ['crm.lead']

    project_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        help="The analytic account related to a Crem Lead.",
        copy=False)
