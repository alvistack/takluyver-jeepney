from collections import deque

from jeepney import DBusAddress, new_method_call
from jeepney.bus_messages import message_bus, MatchRule
from jeepney.integrate.blocking import open_dbus_connection, Proxy

portal = DBusAddress(
    object_path='/org/freedesktop/portal/desktop',
    bus_name='org.freedesktop.portal.Desktop',
)
filechooser = portal.with_interface('org.freedesktop.portal.FileChooser')

conn = open_dbus_connection()

token = 'file_choice_1'
sender_name = conn.unique_name[1:].replace('.', '_')
handle = f"/org/freedesktop/portal/desktop/request/{sender_name}/{token}"

response_rule = MatchRule(
    type='signal', interface='org.freedesktop.portal.Request', path=handle
)
chan = deque(maxlen=1)
conn.add_filter(response_rule, chan)
Proxy(message_bus, conn).AddMatch(response_rule)

# https://flatpak.github.io/xdg-desktop-portal/portal-docs.html#gdbus-method-org-freedesktop-portal-FileChooser.OpenFile
req = new_method_call(filechooser, 'OpenFile', 'ssa{sv}', (
    # Parent window, title, options
    '', 'Pick a file', {'handle_token': ('s', token)}
))
conn.send_and_get_reply(req)

while len(chan) == 0:
    conn.recv_messages()

response, results = chan.popleft().body
if response == 0:
    # print(results)
    print("Chose file:", results['uris'][1][0])

conn.close()
