"""Messages for talking to the DBus daemon itself
"""
from .wrappers import DBusObject, new_method_call

message_bus = DBusObject('/org/freedesktop/DBus',
                         'org.freedesktop.DBus',
                         'org.freedesktop.DBus')

def hello():
    return new_method_call(message_bus, 'Hello')

class DBusNameFlags:
    allow_replacement = 1
    replace_existing = 2
    do_not_queue = 4

def request_name(name, flags=0):
    return new_method_call(message_bus, 'RequestName', 'su',
                           (name, flags))

def release_name(name):
    return new_method_call(message_bus, 'ReleaseName', 's', (name,))

def list_queued_owners(name):
    return new_method_call(message_bus, 'ListQueuedOwners', 's', (name,))

def list_names():
    return new_method_call(message_bus, 'ListNames')

def list_activatable_names():
    return new_method_call(message_bus, 'ListActivatableNames')

def name_has_owner(name):
    return new_method_call(message_bus, 'NameHasOwner', 's', (name,))

def start_service_by_name(name):
    return new_method_call(message_bus, 'StartServiceByName', 'su', (name, 0))

def update_activation_environment(env: dict):
    return new_method_call(message_bus, 'UpdateActivationEnvironment', 'a{ss}',
                           (env,))

def get_name_owner(name):
    return new_method_call(message_bus, 'GetNameOwner', 's', (name,))

def get_connection_unix_user(name):
    return new_method_call(message_bus, 'GetConnectionUnixUser', 's', (name,))

def get_connection_unix_process_id(name):
    return new_method_call(message_bus, 'GetConnectionUnixProcessID', 's', (name,))

def get_connection_credentials(name):
    return new_method_call(message_bus, 'GetConnectionCredentials', 's', (name,))

def get_adt_audit_session_data(name):
    return new_method_call(message_bus, 'GetAdtAuditSessionData', 's', (name,))

def get_connection_selinux_security_context(name):
    return new_method_call(message_bus, 'GetConnectionSELinuxSecurityContext',
                           's', (name,))

class MatchRule:
    """Construct a match rule to subscribe to DBus messages.
    
    e.g.::
    
        mr = MatchRule(interface='org.freedesktop.DBus', member='NameOwnerChanged',
                       type='signal')
        msg = add_match(mr)
        # Send this message to subscribe to the signal
    """
    def __init__(self, *, type=None, sender=None, interface=None, member=None,
                 path=None, path_namespace=None, destination=None,
                 eavesdrop=False):
        self.conditions = c ={}
        if type:
            c['type'] = type
        if sender:
            c['sender'] = sender
        if interface:
            c['interface'] = interface
        if member:
            c['member'] = member
        if path:
            c['path'] = path
        if path_namespace:
            c['path_namespace'] = path_namespace
        if destination:
            c['destination'] = destination
        if eavesdrop:
            c['eavesdrop'] = 'true'

    def add_arg_condition(self, argno, value, kind='string'):
        """Add a condition for a particular argument
        
        argno: int, 0-63
        kind: 'string', 'path', 'namespace'
        """
        if kind not in {'string', 'path', 'namespace'}:
            raise ValueError("kind={!r}".format(kind))
        if kind == 'namespace' and argno != 0:
            raise ValueError("argno must be 0 for kind='namespace'")
        if kind == 'string':
            kind = ''
        name = 'arg{}{}'.format(argno, kind)
        self.conditions[name] = value

    def serialise(self):
        parts = []
        for k, v in sorted(self.conditions.items()):
            parts.append('{}={}'.format(k, v.replace("'", r"\'")))
        return ','.join(parts)

def add_match(rule):
    if isinstance(rule, MatchRule):
        rule = rule.serialise()
    return new_method_call(message_bus, 'AddMatch', 's', (rule,))

def remove_match(rule):
    if isinstance(rule, MatchRule):
        rule = rule.serialise()
    return new_method_call(message_bus, 'RemoveMatch', 's', (rule,))

def get_id():
    return new_method_call(message_bus, 'GetId')

def become_monitor(rules):
    return new_method_call(message_bus, 'BecomeMonitor', 'asu', (rules, 0))
