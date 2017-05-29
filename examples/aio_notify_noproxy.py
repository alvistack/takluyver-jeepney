import asyncio

from jeepney import DBusAddress, new_method_call
from jeepney.integrate.asyncio import connect_and_authenticate

notifications = DBusAddress('/org/freedesktop/Notifications',
                            bus_name='org.freedesktop.Notifications',
                            interface='org.freedesktop.Notifications')

async def send_notification():
    (transport, protocol) = await connect_and_authenticate(bus='SESSION')

    msg = new_method_call(notifications, 'Notify', 'susssasa{sv}i',
                            ('jeepney_test',  # App name
                             0,     # Not replacing any previous notification
                             '',    # Icon
                             'Hello, world!',  # Summary
                             'This is an example notification from Jeepney',
                             [], {},  # Actions, hints
                             -1,      # expire_timeout (-1 = default)
                            ))
    # Send the message and await the reply
    reply = await protocol.send_message(msg)
    print('Notification ID:', reply[0])

loop = asyncio.get_event_loop()
loop.run_until_complete(send_notification())
