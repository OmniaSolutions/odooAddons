import logging
from odoo import models
from odoo import fields
from odoo import api
from odoo import tools
from odoo import _
from lxml import etree
from lxml import builder

FIELD_TO_ADD = ['id',
                'create_date',
                'write_date',
                'create_uid',
                'write_uid']

class Base(models.AbstractModel):
    _inherit = 'base'
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        ret = super(Base, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self.env.user.asGroup('base.group_no_one'):
            try:
                if view_type == 'tree':
                    arch = ret.get('arch', '')
                    try:
                        root = etree.fromstring(arch)
                    except Exception as e:
                        logging.warning('lxml was unable to parse xml: %s' % e)
                        return 
                    tree = etree.ElementTree(root)
                    rootElem = tree.getroot()
                    if rootElem.tag == 'tree':
                        fields_get = self.fields_get()
                        for child in rootElem.getchildren():
                            field_name = child.attrib.get('name', '')
                            if field_name in fields_to_add:
                                fields_to_add.remove(field_name)
                        elem_maker = builder.ElementMaker()
                        for field_name in FIELD_TO_ADD:
                            if field_name in self._fields.keys():
                                elem = elem_maker.field(name=field_name)
                                rootElem.append(elem)
                                fields[field_name] = fields_get.get(field_name, {})
                        xml_string = etree.tostring(rootElem)
                        ret['arch'] = xml_string
            except Exception as ex:
                logging.warning('Cannot add omnia develop fields due to error %r' % (ex))
        return ret