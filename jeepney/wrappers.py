from typing import Union
from warnings import warn

from .low_level import *

__all__ = [
    'DBusObject',
    'new_method_call',
    'new_method_return',
    'new_error',
    'new_signal',
    'MessageGenerator',
    'Properties',
    'DBusErrorResponse',
]

class DBusAddress:
    def __init__(self, object_path, bus_name=None, interface=None):
        self.object_path = object_path
        self.bus_name = bus_name
        self.interface = interface

    def __repr__(self):
        return '{}({!r}, bus_name={!r}, interface={!r})'.format(type(self).__name__,
                    self.object_path, self.bus_name, self.interface)

    def with_interface(self, interface):
        return type(self)(self.object_path, self.bus_name, interface)

class DBusObject(DBusAddress):
    def __init__(self, object_path, bus_name=None, interface=None):
        super().__init__(object_path, bus_name, interface)
        warn('Deprecated alias, use DBusAddress instead', stacklevel=2)

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


class MessageGenerator:
    """Subclass this to define the methods available on a DBus interface.
    
    jeepney.bindgen can automatically create subclasses using introspection.
    """
    def __init__(self, object_path, bus_name):
        self.object_path = object_path
        self.bus_name = bus_name

    def __repr__(self):
        return "{}({!r}, bus_name={!r})".format(type(self).__name__,
                                                self.object_path, self.bus_name)


class ProxyBase:
    """A proxy is an IO-aware wrapper around a MessageGenerator
    
    Calling methods on a proxy object will send a message and wait for the
    reply. This is a base class for proxy implementations in jeepney.integrate.
    """
    def __init__(self, msggen):
        self._msggen = msggen

    def __getattr__(self, item):
        if item.startswith('__'):
            raise AttributeError(item)

        make_msg = getattr(self._msggen, item, None)
        if callable(make_msg):
            return self._method_call(make_msg)

        raise AttributeError(item)

    def _method_call(self, make_msg):
        raise NotImplementedError("Needs to be implemented in subclass")

class Properties:
    """Build messages for accessing object properties

    This uses the standard DBus interface org.freedesktop.DBus.Properties
    """
    def __init__(self, obj: Union[DBusObject, MessageGenerator]):
        self.obj = obj
        self.props_if = obj.with_interface('org.freedesktop.DBus.Properties')

    def get(self, name):
        return new_method_call(self.props_if, 'Get', 'ss',
                   (self.obj.interface, name))

    def get_all(self):
        return new_method_call(self.props_if, 'GetAll', 's',
                               (self.obj.interface,))

    def set(self, name, signature, value):
        return new_method_call(self.props_if, 'Set', 'ssv',
                   (self.obj.interface, name, (signature, value)))

class Introspectable(MessageGenerator):
    interface = 'org.freedesktop.DBus.Introspectable'

    def Introspect(self):
        return new_method_call(self, 'Introspect')

class DBusErrorResponse(Exception):
    def __init__(self, msg):
        self.name = msg.header.fields.get(HeaderFields.error_name)
        self.data = msg.body

    def __str__(self):
        return '[{}] {}'.format(self.name, self.data)
