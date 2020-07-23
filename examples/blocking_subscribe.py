"""
Example of subscribing to a D-Bus signal using blocking I/O.
This subscribes to the signal for a desktop notification being closed.

To try it, start this script, then trigger a desktop notification, and close it
somehow to trigger the signal. Use Ctrl-C to stop the script.

This example relies on the ``org.freedesktop.Notifications.NotificationClosed``
signal; some desktops may not support it. See the notification spec for more
details:
https://people.gnome.org/~mccann/docs/notification-spec/notification-spec-latest.html

Match rules are defined in the D-Bus specification:
https://dbus.freedesktop.org/doc/dbus-specification.html#message-bus-routing-match-rules
"""
from collections import deque

from jeepney.bus_messages import MatchRule, message_bus
from jeepney.integrate.blocking import connect_and_authenticate, Proxy
from jeepney.wrappers import DBusAddress

noti = DBusAddress('/org/freedesktop/Notifications',
                   bus_name='org.freedesktop.Notifications',
                   interface='org.freedesktop.Notifications')

connection = connect_and_authenticate(bus="SESSION")

match_rule = MatchRule(
    type="signal",
    interface=noti.interface,
    member="NotificationClosed",
    path=noti.object_path,
)

queue = deque()
connection.add_filter(match_rule, queue)

# Tell the session bus to pass us matching signal messages:
bus_proxy = Proxy(message_bus, connection)
print("Match added?", bus_proxy.AddMatch(match_rule) == ())


# Using dbus-send or d-feet or blocking_notify.py, send a notification and
# manually close it or call ``.CloseNotification`` after a beat.
while len(queue) == 0:
    connection.recv_messages()

reasons = {1: 'expiry', 2: 'dismissal', 3: 'dbus', '4': 'undefined'}

nid, reason_no = queue.popleft().body
reason = reasons.get(reason_no, 'unknown')
print('Notification {} closed by: {}'.format(nid, reason))

connection.close()
