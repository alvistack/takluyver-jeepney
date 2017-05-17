import asyncio
import sys

from jeepney import new_method_call, DBusObject, message_bus
from jeepney.integrate.blocking import connect_and_authenticate

secrets = DBusObject('/org/freedesktop/secrets',
                           bus_name= 'org.freedesktop.secrets',
                           interface='org.freedesktop.Secret.Service')

login_keyring = DBusObject('/org/freedesktop/secrets/collection/login',
                           bus_name= 'org.freedesktop.secrets',
                           interface='org.freedesktop.Secret.Collection')

def get_property(obj, property):
    property_obj = DBusObject(obj.object_path, bus_name=obj.bus_name,
                              interface='org.freedesktop.DBus.Properties')
    return new_method_call(property_obj, 'Get', 'ss',
                           (obj.interface, property))

msg = new_method_call(login_keyring, 'SearchItems', 'a{ss}',
                      ([
                          ('user', 'tk2e15'),
                      ],)
                     )


conn = connect_and_authenticate(bus='SESSION')

resp = conn.send_and_get_reply(get_property(secrets, 'Collections'))
print('Collections:', resp.body[0][1])

resp = conn.send_and_get_reply(msg)
print('Search res:', resp)
