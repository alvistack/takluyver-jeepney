"""
This example simulates two clients interacting with the message bus, more or
less independently.

Client 1
    Any app on the bus (here, called *service*). It asks the bus for sole
    custody of its preferred name, a `well-known bus name`_ that it wants
    others to recognize.

Client 2
    An interested party (here, called *watcher*). It asks the bus to emit a
    signal (send it an update) whenever *service*'s well-known bus name changes
    hands.  It uses Jeepney's ``router.subscribe_signal`` to fire a callback
    every time this occurs.

.. _well-known bus name: https://dbus.freedesktop.org/doc
   /dbus-specification.html#message-protocol-names
"""

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate, Proxy
from jeepney.bus_messages import message_bus, MatchRule

well_known_bus_name = "io.readthedocs.jeepney.aio_subscribe_example"


def print_match(match_info):
    """A demo callback triggered on successful matches."""
    print("[watcher] match hit:", match_info)


async def main():
    __, service_proto = await connect_and_authenticate("SESSION")
    __, watcher_proto = await connect_and_authenticate("SESSION")
    # Interface objects used by each app to interact with the message bus
    service = Proxy(message_bus, service_proto)
    watcher = Proxy(message_bus, watcher_proto)

    # Create a "signal-selection" match rule
    match_rule = MatchRule(
        type="signal",
        sender=message_bus.bus_name,
        interface=message_bus.interface,
        member="NameOwnerChanged",
        path=message_bus.object_path,
    )

    # Condition: arg number 0 must match the bus name (try changing either)
    match_rule.add_arg_condition(0, well_known_bus_name)

    # Register a callback
    watcher_proto.router.subscribe_signal(
        callback=print_match,
        path=message_bus.object_path,
        interface=message_bus.interface,
        member="NameOwnerChanged"
    )

    # Tell the session bus to pass us matching signal messages.
    print("[watcher] adding match rule")
    await watcher.AddMatch(match_rule)
    await asyncio.sleep(1)

    print("[service] calling 'RequestName'")
    resp = await service.RequestName(well_known_bus_name, 4)

    print("[service] reply:", (None, "primary owner", "in queue",
                               "exists", "already owned")[resp[0]])

    await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
