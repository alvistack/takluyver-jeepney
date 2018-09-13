
# Note: "subscribe" in the filename refers to the router.subscribe_signal API
# method and not the process of adding match rules to the message bus.

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate, Proxy
from jeepney.bus_messages import message_bus, MatchRule


def print_match(match_info):
    """A demo callback triggered on successful matches."""
    print("[watcher] match hit:", match_info)


async def main():
    __, service_proto = await connect_and_authenticate("SESSION")
    __, watcher_proto = await connect_and_authenticate("SESSION")
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

    # Arg number 0 must match the string below (try changing either)
    match_rule.add_arg_condition(0, "org.jeepney.aio_subscribe")

    # Register a callback
    watcher_proto.router.subscribe_signal(
        callback=print_match,
        path=message_bus.object_path,
        interface=message_bus.interface,
        member="NameOwnerChanged"
    )

    print("[watcher] adding match rule")
    await watcher.AddMatch(match_rule)
    await asyncio.sleep(1)

    print("[service] calling 'RequestName'")
    resp = await service.RequestName("org.jeepney.aio_subscribe", 4)

    print("[service] reply:", (None, "primary owner", "in queue",
                               "exists", "already owned")[resp[0]])


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
