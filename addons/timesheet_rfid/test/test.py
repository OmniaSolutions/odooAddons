'''
Created on Jun 16, 2015

@author: daniel
'''
from datetime import datetime,timedelta, date
timeNow = datetime.now().replace(tzinfo=None,second=0, microsecond=0)
HOURS_LIST = []
HOURS_LIST = [
#               timeNow.replace( day=8, month=6, hour=7, minute=59),      #08:00
#               timeNow.replace( day=8, month=6, hour=12, minute=3),      #12:00
#               timeNow.replace( day=8, month=6, hour=12, minute=59),     #13:00
#               
#               timeNow.replace( day=10, month=6, hour=8, minute=1),      #08:00
#               timeNow.replace( day=10, month=6, hour=12, minute=30),    #12:30
#               timeNow.replace( day=10, month=6, hour=13, minute=31),    #13:30
#               timeNow.replace( day=10, month=6, hour=19, minute=12),    #19:00
#               
#               timeNow.replace( day=11, month=6, hour=6, minute=54),     #07:00
#               timeNow.replace( day=11, month=6, hour=13, minute=00),    #13:00
#               timeNow.replace( day=11, month=6, hour=18, minute=23),    #18:30



             #Manzotti
             (24, timeNow.replace( day=7, month=7, hour=7, minute=21)),  
             (24, timeNow.replace( day=7, month=7, hour=12, minute=3)),   
             (24, timeNow.replace( day=7, month=7, hour=12, minute=58)),   
             (24, timeNow.replace( day=8, month=7, hour=8, minute=5)),   
             #Villagrossi
             (35, timeNow.replace( day=7, month=7, hour=7, minute=31)),   
             (35, timeNow.replace( day=7, month=7, hour=12, minute=31)),   
             (35, timeNow.replace( day=7, month=7, hour=14, minute=1)),  
             (35, timeNow.replace( day=8, month=7, hour=8, minute=5)),   
             #Ortolani
             (51, timeNow.replace( day=7, month=7, hour=7, minute=31)),   
             (51, timeNow.replace( day=7, month=7, hour=13, minute=11)),   
             (51, timeNow.replace( day=7, month=7, hour=14, minute=1)),  
             (51, timeNow.replace( day=8, month=7, hour=8, minute=5)),  
              ]