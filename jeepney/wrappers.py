from .low_level import *

__all__ = [
    'DBusObject',
    'message_bus',
    'new_method_call',
    'new_method_return',
    'new_error',
    'new_signal',
    'hello_msg',
]

class DBusObject:
    def __init__(self, object_path, bus_name=None, interface=None):
        self.object_path = object_path
        self.bus_name = bus_name
        self.interface = interface

    def __repr__(self):
        return '{}({!r}, bus_name={!r}, interface={!r})'.format(type(self).__name__,
                    self.object_path, self.bus_name, self.interface)

    def with_interface(self, interface):
        return type(self)(self.bus_name, self.object_path, interface)

message_bus = DBusObject('/org/freedesktop/DBus',
                         'org.freedesktop.DBus',
                         'org.freedesktop.DBus')

def new_header(msg_type):
    return Header(Endianness.little, msg_type, flags=0, protocol_version=1,
                  body_length=-1, serial=-1, fields={})

def new_method_call(remote_obj, method, signature=None, body=()):
    header = new_header(MessageType.method_call)
    header.fields[HeaderFields.path] = remote_obj.object_path
    if remote_obj.bus_name is None:
        raise ValueError("remote_obj.bus_name cannot be None for method calls")
    header.fields[HeaderFields.destination] = remote_obj.bus_name
    if remote_obj.interface is not None:
        header.fields[HeaderFields.interface] = remote_obj.interface
    header.fields[HeaderFields.member] = method
    if signature is not None:
        header.fields[HeaderFields.signature] = signature

    return Message(header, body)

def new_method_return(parent_msg, signature=None, body=()):
    header = new_header(MessageType.method_return)
    header.fields[HeaderFields.reply_serial] = parent_msg.header.serial
    if signature is not None:
        header.fields[HeaderFields.signature] = signature
    return Message(header, body)

def new_error(parent_msg, error_name, signature=None, body=()):
    header = new_header(MessageType.error)
    header.fields[HeaderFields.reply_serial] = parent_msg.header.serial
    header.fields[HeaderFields.error_name] = error_name
    if signature is not None:
        header.fields[HeaderFields.signature] = signature
    return Message(header, body)

def new_signal(emitter, signal, signature=None, body=()):
    header = new_header(MessageType.signal)
    header.fields[HeaderFields.path] = emitter.object_path
    if emitter.interface is None:
        raise ValueError("emitter.interface cannot be None for signals")
    header.fields[HeaderFields.interface] = emitter.interface
    header.fields[HeaderFields.member] = signal
    if signature is not None:
        header.fields[HeaderFields.signature] = signature
    return Message(header, body)

# We need to say hello to the message bus before doing anythong else, so provide
# a prebuilt message for this.
hello_msg = new_method_call(message_bus, 'Hello')
