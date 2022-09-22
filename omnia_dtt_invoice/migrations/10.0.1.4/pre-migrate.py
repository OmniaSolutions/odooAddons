# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2019 https://OmniaSolutions.website
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
Created on July 22, 2020

@author: lcazzolati
'''
import logging
_logger = logging.getLogger(__name__)
      
def migrate(cr, version):
    if not version:
        _logger.warning("""
            There is no previous version of the module.
            Skip the migration.
            """)
      
        return
      
    _logger.info("port value from related")
    cr.execute("begin transaction;")
    cr.execute("""ALTER TABLE account_invoice RENAME COLUMN delivery_address TO delivery_address_id;""")
    cr.execute("""ALTER TABLE account_invoice ADD COLUMN delivery_address CHARACTER VARYING;""")
    cr.execute("""SELECT id, delivery_address_id FROM account_invoice WHERE delivery_address_id IS NOT null;""")
    invoice_partners = cr.fetchall()
    for row in invoice_partners:
        cr.execute("""SELECT id, street, city, zip, state_id, country_id FROM res_partner WHERE id = %s;""" % (row[1]))
        invoice_fields = cr.fetchall()
        for field in invoice_fields:
            if field[4]:
                cr.execute("""SELECT name FROM res_country_state WHERE id = %s;""" % (field[4]))
                state = cr.fetchall()
                state = (state[0])[0]
            else:
                state = ''
            if field[5]:
                cr.execute("""SELECT name FROM res_country WHERE id = %s;""" % (field[5]))
                country = cr.fetchall()
                country = (country[0])[0]
            else:
                country = ''
        address = (invoice_fields[0])[1] + ', ' + (invoice_fields[0])[2] + ', ' + (invoice_fields[0])[3] + ' ' + state + ' ' + country
        cr.execute("UPDATE account_invoice SET delivery_address = '%s' WHERE id = %s;" % (address, row[0]))
    cr.execute('commit;')
    _logger.info("Migration terminated.")
 
     