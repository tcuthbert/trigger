import sys
from trigger.cmds import Commando, ReactorlessCommando
from trigger.netdevices import NetDevices, NetDevice
from twisted.internet import reactor
from twisted.python import log



class Device(object):
    snmp_gather_cmds = ['show snmp community']

    def __init__(self, name):
        self.name = name
        self.acls = []
        self.commands = []
        self.version = None
        self.results = {}
        self.commando = None
        self.lastAccess = None

    def is_old_community_present(self):
        return

    def parse_snmp_output(self):
        return

    def provision_snmp_community(self):
        return
    

class GetSNMPInfo(ReactorlessCommando):
    """
    Collect SNMP information from Device device.
    """

    commands = Device.snmp_gather_cmds

def extract_snmp_community(result):
    """
    Processes the SNMP output on each Device object that is returned by
    GetSNMPInfo.

    1. Extract current SNMP communities from device.
    2. Prepare implementation to remove legacy communities.
    3. Prepare implementation to deploy new community.
    4. Return list of devices to remmediate.
    """
    rv = []

    for device, result in result.items():
        pass


def stop_reactor(data):
    """Stop the event loop"""
    print 'Stopping reactor'
    if reactor.running:
        reactor.stop()


def main():
    log.startLogging(sys.stdout, setStdout=False)
    nds = NetDevices().all()
    global device_list
    global snmp_hosts
    device_list = map(lambda x: x.nodeName, nds)
    jobs = GetSNMPInfo(device_list).run()
    jobs.addBoth(stop_reactor)
    reactor.run()
    # run.addBoth(stop_reactor)

    # log.msg(run.result)


if __name__ == "__main__":
    main()
