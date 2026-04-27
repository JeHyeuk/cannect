from cannect import DataBaseCAN
from pandas import set_option

set_option('display.expand_frame_repr', False)

db = DataBaseCAN.Reader()
# print(db)

sort = db[db['ECU'] != 'EMS']

for n, (m, obj) in enumerate(sort.messages.items(), start=1):
    channel = obj['ICE Channel']
    if not channel:
        channel =  obj['HEV Channel']
    if channel == "P":
        channel = "CAN1"
    else:
        channel = "CAN3"
    print(channel, 'Rx', m, obj['ID'])