# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2012 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2012 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

import logging
from record_mapping import OUTPUT_RECORD_MAPPING
from record_mapping import INPUT_RECORD_MAPPING
from record_mapping import BONIFICI

FLOWTYPE = 'OUTPUT_RECORD_MAPPING' # default value

#TODO add fields validation as specified in standard
class Field(object):

    def length(self):
        return (self.toposition - self.fromposition) + 1

    def __init__(self, fromposition, toposition, name, content=''):
        self.fromposition = fromposition
        self.toposition = toposition
        self.name = name
        if not content:
            self.content = ''.ljust(self.length())
        else:
            self.content = content

    def __str__(self):
        return self.content


class Record(object):

    #we create EF record structure by default
    def __init__(self, rawrecord='EF', flowtype=FLOWTYPE):
        self.fields = []
        recordLen=len(rawrecord)
        code = rawrecord[1:3]
        flowtype = eval(flowtype)
        if code not in flowtype:
            raise IndexError('Unknown record type %s' % code)
        maxRowLeng = 0
        for field_args in flowtype[code]:
            newfield = Field(*field_args)
            if field_args[2] == 'tipo_record':
                newfield.content = code
            self.appendfield(newfield)
            if field_args[1] > maxRowLeng:
                maxRowLeng = field_args[1]
        self.readrawrecord(rawrecord)

    def __str__(self):
        c = ''
        for field in self.fields:
            c = c + field.content
        return c
    
    def get(self, key, default=None):
        try:
            return self[key]
        except:
            return default

    def __getitem__(self, key):
        """Overloading in order to retrieve content
            by position or field name as specified by CBI docs"""
        if isinstance(key, slice) and not key.step:
            return self.__str__()[key.start - 1:key.stop]
        elif isinstance(key, str):
            for field in self.fields:
                if field.name == key:
                    return field.content.strip()  # strip o non strip?
            if default:
                return default
            raise IndexError('Impossible to find field with key %s' % key)
        else:
            return self.__str__()[key]

    def __setitem__(self, key, item):
        """Overloading in order to write content
            by position or field name as specified by CBI docs"""
        if isinstance(key, slice) and not key.step:
            for field in self.fields:
                if (field.fromposition == key.start
                    and field.toposition == key.stop):
                    field.content = item
                    return
            raise IndexError('Impossible to find field with position %i, %i'
                % (key.start, key.stop))
        elif isinstance(key, str):
            for field in self.fields:
                if field.name == key:
                    field.content = item.ljust(field.length())
                    return
            raise IndexError('Impossible to find field with key %s' % key)
        else:
            raise TypeError(
                'You must use slice or string to access fields list')
    
    def hasKey(self, key):
        return key in [f.name for f in self.fields]
        
    def appendfield(self, field):
        if not isinstance(field, Field):
            raise TypeError('You can only append Field objects')
        if field.name in [f.name for f in self.fields]:
            raise IndexError('Field name %s already present' % field.name)
        self.fields.append(field)

    def appendFields(self, record):
        for field in record.fields:
            try:
                self.appendfield(field)
            except Exception as ex:
                logging.warning("Field Already Set")
                self[field.name] += field.content
            
    def readrawrecord(self, rawrecord):
        for field in self.fields:
            field.content = rawrecord[
                (field.fromposition - 1):field.toposition]


class Disposal(object):

    def __init__(self, recs=[]):
        self.records = recs[:]
        
    def record_type(self):
        out = []
        for record in self.records:
            out.append(record['tipo_record'])
        return out
                
    def __getitem__(self, key):
        """Overloading in order to retrieve content by record code"""
        if isinstance(key, str):
            for record in self.records:
                if record['tipo_record'] == key:
                    return record
            raise IndexError('Impossible to find record %s' % key)
        else:
            raise TypeError('Key must be string')

    def __setitem__(self, key, item):
        """Overloading in order to write content by record code"""
        if not isinstance(item, Record):
            raise TypeError('You can only write Record objects')
        if isinstance(key, str):
            for record in self.records:
                if record['tipo_record'] == key:
                    record = item
            raise IndexError('Impossible to find field with key %s' % key)
        else:
            raise TypeError('Key must be string')


class Flow(object):

    def __init__(self, header=None, footer=None, disposals=[]):
        self.header = header
        self.footer = footer
        self.disposals = disposals

    def readfile(self, fileobj, firstrecordidentifier='14',
        flowtype=FLOWTYPE):
        rows = []
        for line in fileobj:
            line = line.replace('\r', '').replace('\n', '')
            line = line.rstrip()
            if len(line):
                rows.append(line)
        if len(rows) < 3:
            raise TypeError('Insufficient number of rows')
        self.header = Record(rows[0], flowtype=flowtype)
        self.footer = Record(rows[len(rows) - 1], flowtype=flowtype)
        self.disposals = []
        currentdisposal = Disposal()
        for row in rows[1:len(rows) - 1]:
            record = Record(row, flowtype=flowtype)
            if (record['tipo_record'] == firstrecordidentifier
                and currentdisposal.records):
                ''' Appends last disposal and creates new disposal
                with firstrecordidentifier '''
                self.disposals.append(currentdisposal)
                currentdisposal = Disposal()
            currentdisposal.records.append(record)
        if currentdisposal.records:
            ''' Appends last disposal '''
            self.disposals.append(currentdisposal)
        lastrecordfound = False
        for disposal in self.disposals:
            if str(firstrecordidentifier) in set([r['tipo_record'] for r in disposal.records]):
                lastrecordfound = True
        if not lastrecordfound:
            self.disposals = []
            raise IndexError(
                'First record identifier %s for disposals not found'
                % firstrecordidentifier)

    def writefile(self, filepath):
        f = open(filepath, 'w')
        f.write(str(self.header) + '\r\n')
        for disposal in self.disposals:
            for record in disposal.records:
                f.write(str(record) + '\r\n')
        f.write(str(self.footer) + '\r\n')
        f.close()