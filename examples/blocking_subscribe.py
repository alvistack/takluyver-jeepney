"""
See the aio-subscribe example for proxy usage.

Match rules are pretty byzantine, e.g., ``path`` and ``path_namespace`` are
mutually exclusive. See spec_

.. _spec: https://dbus.freedesktop.org/doc/dbus-specification.html
   #message-bus-routing-match-rules

Add session id to target unicast messages (those only addressed to you)::

  destination=connection.unique_name

Won't work in the example below, because we're just tuning in to broadcasts.
"""

from jeepney import DBusAddress, new_method_call
from jeepney.integrate.blocking import connect_and_authenticate
from jeepney.bus_messages import MatchRule
from collections import namedtuple

addresses = {
    "DBus": DBusAddress("/org/freedesktop/DBus",
                        bus_name="org.freedesktop.DBus",
                        interface="org.freedesktop.DBus"),
    "Notifications": DBusAddress("/org/freedesktop/Notifications",
                                 bus_name="org.freedesktop.Notifications",
                                 interface="org.freedesktop.Notifications")
}
addresses = namedtuple("Addresses", addresses)(**addresses)

connection = connect_and_authenticate(bus="SESSION")

match_rule = MatchRule(
    type="signal",
    sender=addresses.Notifications.bus_name,
    interface=addresses.Notifications.interface,
    member="NotificationClosed",
    path=addresses.Notifications.object_path,
).serialise()

msg = new_method_call(addresses.DBus, "AddMatch", "s", (match_rule,))

reply = connection.send_and_get_reply(msg)
print("Request reply is empty on success:", reply == tuple())

connection.router.subscribe_signal(
    callback=print,
    path=addresses.Notifications.object_path,
    interface=addresses.Notifications.interface,
    member="NotificationClosed"
)

# Using dbus-send or d-feet or another example script, send some notifications
# and either manually close them or call ``.CloseNotification`` after a beat.
try:
    while True:
        connection.recv_messages()
except KeyboardInterrupt:
    pass
