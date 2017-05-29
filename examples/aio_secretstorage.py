"""Example accessing the SecretStorage DBus interface with asyncio APIs

https://freedesktop.org/wiki/Specifications/secret-storage-spec/secrets-api-0.1.html#ref-dbus-api
"""
import asyncio

from jeepney import new_method_call, DBusAddress, Properties
from jeepney.integrate.asyncio import connect_and_authenticate

secrets = DBusAddress('/org/freedesktop/secrets',
                      bus_name= 'org.freedesktop.secrets',
                      interface='org.freedesktop.Secret.Service')

login_keyring = DBusAddress('/org/freedesktop/secrets/collection/login',
                            bus_name= 'org.freedesktop.secrets',
                            interface='org.freedesktop.Secret.Collection')

msg = new_method_call(login_keyring, 'SearchItems', 'a{ss}', ({
                          'user': 'tk2e15',
                        },)
                     )

async def send_notification():
    (t, p) = await connect_and_authenticate(bus='SESSION')

    resp = await p.send_message(Properties(secrets).get('Collections'))
    print('Collections:', resp[0][1])

    resp = await p.send_message(msg)
    print('Search res:', resp)


loop = asyncio.get_event_loop()
loop.run_until_complete(send_notification())

