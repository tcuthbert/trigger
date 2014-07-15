# -*- coding: utf-8 -*-

"""
This code is originally from parser.py. This is the basic grammar and rules
from which the other specific grammars are built. This file is not meant to by used by itself.
Imported into the specific grammar files.

#Constants
    errs
    rules
#Classes
    Modifiers
#Functions
    S
    literals
    update
    dict_sum
"""

__author__ = 'Jathan McCollum, Mike Biancaniello, Michael Harding, Michael Shields'
__editor__ = 'Joseph Malone'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathanism@aol.com'
__copyright__ = 'Copyright 2006-2013, AOL Inc.; 2013 Saleforce.com'

from support import *

# Each production can be any of:
# 1. string
#    if no subtags: -> matched text
#    if single subtag: -> value of that
#    if list: -> list of the value of each tag
# 2. (string, object) -> object
# 3. (string, callable_object) -> object(arg)

class Modifiers(MyDict):
    """
    Container class for modifiers. These are only supported by JunOS format
    and are ignored by all others.
    """
    def __setitem__(self, key, value):
        # Handle argument-less modifiers first.
        if key in ('log', 'sample', 'syslog', 'port-mirror'):
            if value not in (None, True):
                raise exceptions.ActionError('"%s" action takes no argument' % key)
            super(Modifiers, self).__setitem__(key, None)
            return
        # Everything below requires an argument.
        if value is None:
            raise exceptions.ActionError('"%s" action requires an argument' %
                                         key)
        if key == 'count':
            # JunOS 7.3 docs say this cannot contain underscores and that
            # it must be 24 characters or less, but this appears to be false.
            # Doc bug filed 2006-02-09, doc-sw/68420.
            check_name(value, exceptions.BadCounterName, max_len=255)
        elif key == 'forwarding-class':
            check_name(value, exceptions.BadForwardingClassName)
        elif key == 'ipsec-sa':
            check_name(value, exceptions.BadIPSecSAName)
        elif key == 'loss-priority':
            if value not in ('low', 'high'):
                raise exceptions.ActionError('"loss-priority" must be "low" or "high"')
        elif key == 'policer':
            check_name(value, exceptions.BadPolicerName)
        else:
            raise exceptions.ActionError('invalid action: ' + str(key))
        super(Modifiers, self).__setitem__(key, value)

    def output_junos(self):
        """
        Output the modifiers to the only supported format!
        """
        keys = self.keys()
        keys.sort()
        return [k + (self[k] and ' '+str(self[k]) or '') + ';' for k in keys]

subtagged = set()

def S(prod):
    """
    Wrap your grammar token in this to call your helper function with a list
    of each parsed subtag, instead of the raw text. This is useful for
    performing modifiers.

    :param prod: The parser product.
    """
    subtagged.add(prod)
    return prod

def literals(d):
    '''Longest match of all the strings that are keys of 'd'.'''
    keys = [str(key) for key in d]
    keys.sort(lambda x, y: len(y) - len(x))
    return ' / '.join(['"%s"' % key for key in keys])

def update(d, **kwargs):
    # Check for duplicate subterms, which is legal but too confusing to be
    # allowed at AOL.  For example, a Juniper term can have two different
    # 'destination-address' clauses, which means that the first will be
    # ignored.  This led to an outage on 2006-10-11.
    for key in kwargs.iterkeys():
        if key in d:
            raise exceptions.ParseError('duplicate %s' % key)
    d.update(kwargs)
    return d

def dict_sum(dlist):
    dsum = {}
    for d in dlist:
        for k, v in d.iteritems():
            if k in dsum:
                dsum[k] += v
            else:
                dsum[k] = v
    return dsum

## syntax error messages
errs = {
    'comm_start': '"comment missing /* below line %(line)s"',
    'comm_stop':  '"comment missing */ below line %(line)s"',
    'default':    '"expected %(expected)s line %(line)s"',
    'semicolon':  '"missing semicolon on line %(line)s"',
}

rules = {
    'digits':     '[0-9]+',
    '<digits_s>': '[0-9]+',
    '<ts>':       '[ \\t]+',
    '<ws>':       '[ \\t\\n]+',
    '<EOL>':      "('\r'?,'\n')/EOF",
    'alphanums':  '[a-zA-Z0-9]+',
    'word':       '[a-zA-Z0-9_.-]+',
    'anychar':    "[ a-zA-Z0-9.$:()&,/'_-]",
    'hex':        '[0-9a-fA-F]+',
    'ipchars':    '[0-9a-fA-F:.]+',
    'ipv4':       ('digits, (".", digits)*', TIP),
    'ipaddr':     ('ipchars', TIP),
    'cidr':       ('("inactive:", ws+)?, (ipaddr / ipv4), "/", digits, (ws+, "except")?', TIP),
    'macaddr':    'hex, (":", hex)+',
    'protocol':   (literals(Protocol.name2num) + ' / digits', do_protocol_lookup),
    'tcp':        ('"tcp" / "6"', Protocol('tcp')),
    'udp':        ('"udp" / "17"', Protocol('udp')),
    'icmp':       ('"icmp" / "1"', Protocol('icmp')),
    'icmp_type':  (literals(icmp_types) + ' / digits', do_icmp_type_lookup),
    'icmp_code':  (literals(icmp_codes) + ' / digits', do_icmp_code_lookup),
    'port':       (literals(ports) + ' / digits', do_port_lookup),
    'dscp':       (literals(dscp_names) + ' / digits', do_dscp_lookup),
    'root':       'ws?, junos_raw_acl / junos_replace_family_acl / junos_replace_acl / junos_replace_policers / ios_acl, ws?',
}
