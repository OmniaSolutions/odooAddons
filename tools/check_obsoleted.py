'''
Created on 9 Jun 2016

@author: dsmerghetto
'''
COMMIT = True
from DbWrapper.wrapperOpenERP import BaseDbIntegration
BaseDbIntegration.newStyleCall = True
BaseDbIntegration.create('admin', 'admin', 'tomorrow', 'localhost', '8069', '', 'http')
limit = None
objDicts = BaseDbIntegration.GetDetailsSearch('product.product', [[('id', '>', -1)]], ['engineering_code', 'engineering_revision', 'state'], limit=limit)

result = {}

objects = len(objDicts)
print('compute %r items' % (objects))

for dictObj in objDicts:
    engineering_code = dictObj.get('engineering_code', '')
    engineering_revision = dictObj.get('engineering_revision', 0)
    obj_id = dictObj.get('id', 0)
    state = dictObj.get('state', '')
    
    if engineering_code not in result:
        result[engineering_code] = {}
    if engineering_revision not in result[engineering_code]:
        result[engineering_code][engineering_revision] = dictObj

print('Parse result')

errors = []
count = 0
for eng_code, vals in result.items():
    print('Evaluate %r / %r' % (count, len(result)))
    keys = vals.keys()
    keys.sort()
    last_rev = vals[keys[-1]]
    state = last_rev['state']
    if state in ['obsoleted', 'undermodify']:
        errors.append(last_rev)
        print('[WARNING] Component %r in state %r' % (last_rev['id'], state))
    count += 1
    
print('\nFound %r errors\n' % (len(errors)))

for error_vals in errors:
    if COMMIT:
        res_id = error_vals.get('id', False)
        values = {'state': 'released'}
        kArgs = {}
        res = BaseDbIntegration.UpdateValue('product.product', [res_id], values, kArgs)
        if not res:
            print('Cannot update state for component res_id')
    
    
    
    
    
    