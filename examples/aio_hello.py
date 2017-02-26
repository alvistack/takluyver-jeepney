import asyncio

from jeepney import new_method_call, message_bus
from jeepney.integrate.asyncio import connect_and_authenticate

msg = new_method_call(message_bus, 'Hello')

async def hello():
    (t, p) = await connect_and_authenticate(bus='SESSION')
    resp = await p.send_message(msg)
    #print(resp)
    print('My ID is:', resp.body[0])
    
loop = asyncio.get_event_loop()
loop.run_until_complete(hello())
