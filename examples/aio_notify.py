import asyncio

from jeepney import new_method_call, DBusObject, message_bus
from jeepney.integrate.asyncio import connect_and_authenticate

notifications = DBusObject('/org/freedesktop/Notifications',
                           bus_name= 'org.freedesktop.Notifications',
                           interface='org.freedesktop.Notifications')

hello_msg = new_method_call(message_bus, 'Hello')


msg = new_method_call(notifications, 'Notify', 'susssasa{sv}i', (
                       'jeepney_test',  # App name
                       0,      # Not replacing any previous notification
                       '',    # Icon
                       'Hello, world!',  # Summary
                       'This is an example notification from Jeepney', # Body
                       [],    # Actions
                       {},    # Hints
                       -1,    # expire_timeout (-1 = default)
                     ))


async def send_notification():
    (t, p) = await connect_and_authenticate(bus='SESSION')

    resp = await p.send_message(msg)
    print('Notification ID:', resp.body[0])


loop = asyncio.get_event_loop()
loop.run_until_complete(send_notification())
