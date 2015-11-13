'''
Created on Jun 16, 2015

@author: daniel

'''
from datetime import datetime,timedelta, date
timeNow = datetime.utcnow().replace(second=0, microsecond=0)
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



# #              #Manzotti
#             (24, timeNow.replace( day=7, month=7, hour=5, minute=21)),  
#             (24, timeNow.replace( day=7, month=7, hour=10, minute=3)),   
#             (24, timeNow.replace( day=7, month=7, hour=10, minute=58)),   
#             (24, timeNow.replace( day=8, month=7, hour=6, minute=5)),   
# #              #Villagrossi
# #              (35, timeNow.replace( day=7, month=7, hour=7, minute=31)),   
# #              (35, timeNow.replace( day=7, month=7, hour=12, minute=31)),   
# #              (35, timeNow.replace( day=7, month=7, hour=14, minute=1)),  
# #              (35, timeNow.replace( day=8, month=7, hour=8, minute=5)),   
# #              #Ortolani
#             (51, timeNow.replace( day=7, month=7, hour=5, minute=31)),   
#             (51, timeNow.replace( day=7, month=7, hour=11, minute=11)),   
#             (51, timeNow.replace( day=7, month=7, hour=12, minute=1)),  
#             (51, timeNow.replace( day=8, month=7, hour=6, minute=5)),  



#                 #OmniaSolutions
#                 #Test chiusura alle 12
#             (117, timeNow.replace( day=7, month=7, hour=9, minute=0)), 
#             (117, timeNow.replace( day=8, month=7, hour=10, minute=0)), 
#                    
#                 #Test chiusura alle 18
#             (117, timeNow.replace( day=8, month=7, hour=12, minute=0)), 
#             (117, timeNow.replace( day=8, month=7, hour=13, minute=0)), 
#             (117, timeNow.replace( day=9, month=7, hour=10, minute=5)), 
#                    
#                 #Test minuti non recuperati la sera
#             (117, timeNow.replace( day=9, month=7, hour=12, minute=0)), 
#             (117, timeNow.replace( day=9, month=7, hour=13, minute=0)),
#             (117, timeNow.replace( day=9, month=7, hour=17, minute=1)),
#                    
#                 #Test minuti recuperati la sera
#             (117, timeNow.replace( day=10, month=7, hour=8, minute=5)),
#             (117, timeNow.replace( day=10, month=7, hour=12, minute=0)), 
#             (117, timeNow.replace( day=10, month=7, hour=13, minute=0)),
#             (117, timeNow.replace( day=10, month=7, hour=17, minute=6)),
#                    
#                 #Test entro alle 17:00 ed entro alle 17:30        a mezzogiorno e mezzo perdo la mezz'ora
#             (117, timeNow.replace( day=11, month=7, hour=8, minute=0)),
#             (117, timeNow.replace( day=11, month=7, hour=12, minute=29)),
#             (117, timeNow.replace( day=11, month=7, hour=17, minute=0)),
#             (117, timeNow.replace( day=11, month=7, hour=17, minute=30)),
#     
#                 #Test esco 12:30 entro 13:00 e perdo la mezz'ora perche' ho un'ora di pausa pranzo
#             (117, timeNow.replace( day=12, month=7, hour=7, minute=48)),
#             (117, timeNow.replace( day=12, month=7, hour=12, minute=33)),
#             (117, timeNow.replace( day=12, month=7, hour=13, minute=0)),
#             (117, timeNow.replace( day=12, month=7, hour=17, minute=00)),
#               
#                 #Test entro alle 17:30 e non esco
#             (117, timeNow.replace( day=13, month=7, hour=8, minute=0)),
#             (117, timeNow.replace( day=13, month=7, hour=12, minute=0)),
#             (117, timeNow.replace( day=13, month=7, hour=18, minute=30)),
#             (117, timeNow.replace( day=14, month=7, hour=8, minute=05)),
#   
#                 #Test entro alle 16:30 ed esco alle 17:01 non recuperando il ritardo della mattina
#             (117, timeNow.replace( day=14, month=7, hour=12, minute=29)),
#             (117, timeNow.replace( day=14, month=7, hour=16, minute=30)),
#             (117, timeNow.replace( day=14, month=7, hour=17, minute=01)),

              ]
