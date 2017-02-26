import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate

async def hello():
    (t, p) = await connect_and_authenticate(bus='SESSION')
    print('My ID is:', p.unique_name)
    
loop = asyncio.get_event_loop()
loop.run_until_complete(hello())
