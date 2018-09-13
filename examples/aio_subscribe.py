# The note at the top of blocking_subscribe.py also applies to this example.

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate, Proxy
from jeepney.bus_messages import message_bus, MatchRule
from aio_notify import Notifications


def print_match(match_info):
    """A demo callback.
    Called with a single tuple on successful matches.
    """
    reasons = (  # <https://developer.gnome.org/notification-spec>
        "Expired",
        "Dismissed by the user",
        "Closed by a call to CloseNotification",
        "Undefined/reserved reasons"
    )
    idee, reason = match_info
    print("<- %d %s" % (idee, reasons[reason]))


async def main():
    __, proto = await connect_and_authenticate("SESSION")
    session_bus = Proxy(message_bus, proto)
    notify_msggen = Notifications()
    notify_service = Proxy(notify_msggen, proto)

    # Create a "signal-selection" match rule used by *Match methods below
    match_rule = MatchRule(
        type="signal",
        sender=notify_msggen.bus_name,
        interface=notify_msggen.interface,
        member="NotificationClosed",
        path=notify_msggen.object_path,
    )

    # Prep and register callback
    proto.router.subscribe_signal(
        callback=print_match,
        path=notify_msggen.object_path,
        interface=notify_msggen.interface,
        member="NotificationClosed"
    )

    idee, *__ = await notify_service.Notify("aio_subscribe", 0, "",
                                            "Foo", "foo", [], {}, -1,)
    print("->", idee, "+")  # ~~> notified
    await asyncio.sleep(1)
    print("->", idee, "-")  # ~~> closing
    await notify_service.CloseNotification(idee)

    print("# Starting subscription")
    await session_bus.AddMatch(match_rule)
    await asyncio.sleep(1)

    idee, *__ = await notify_service.Notify("aio_subscribe", 0, "",
                                            "Bar", "bar", [], {}, -1,)
    print("->", idee, "+")
    await asyncio.sleep(1)
    print("->", idee, "-")
    await notify_service.CloseNotification(idee)

    print("# Cancelling subscription")
    await session_bus.RemoveMatch(match_rule)
    await asyncio.sleep(1)

    idee, *__ = await notify_service.Notify("aio_subscribe", 0, "",
                                            "Baz", "baz", [], {}, -1,)
    print("->", idee, "+")
    await asyncio.sleep(1)
    print("->", idee, "-")
    await notify_service.CloseNotification(idee)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
