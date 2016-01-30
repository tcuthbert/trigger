import sys
import json
from trigger.cmds import Commando, ReactorlessCommando
from trigger.netdevices import NetDevices, NetDevice
from twisted.internet import reactor
from twisted.python import log



class Device(object):
    snmp_gather_cmds = ['show snmp community']
    snmp_deploy_cmd = [
            'config t',
            'snmp-server {host} {community} {mode}',
            'end'
            ]

    def __init__(self, name):
        self.name = name
        self.communities = []
        self.commands = []
        self.version = None
        self.results = {}
        self.commando = None

    def is_old_community_present(self):
        return

    def provision_snmp_community(self):
        return
    

class GetSNMPInfo(ReactorlessCommando):
    """
    Collect SNMP information from Device device.
    """

    commands = Device.snmp_gather_cmds


class WriteSNMPCommunities(ReactorlessCommando):
    """
    Collect SNMP information from Device device.
    """

    commands = Device.snmp_deploy_cmd

def process_hosts(result):
    """
    Processes the SNMP output on each Device object that is returned by
    GetSNMPInfo.

    1. Extract current SNMP communities from device.
    2. Prepare implementation to remove legacy communities if required.
    3. Prepare implementation for new communities if required.
    4. Return list of devices to remmediate.
    """
    import re

    regexp = re.compile('Community Index: (.*?)\r\n')

    for hostname, cli_output in result.items():
        dev = snmp_hosts.get(hostname)
        if cli_output.values() is None:
            dev.build_deployment()
        else:
            communities = regexp.findall(cli_output.values()[0])
            dev.communities = communities
            log.msg("Extracting snmp communities {0} from {1}".format(communities, hostname))

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
    snmp_hosts = {}
    global config
    config = json.loads(open('{0}/config.json'.format(sys.argv[1]), 'rb').read())

    device_list = map(lambda x: x.nodeName, nds)

    for device in device_list:
        if device not in snmp_hosts:
            snmp_hosts[device] = Device(device)

    jobs = GetSNMPInfo(snmp_hosts.keys()).run()
    jobs.addCallback(process_hosts)
    # jobs.addCallback(reduce_snmp_hosts)
    jobs.addBoth(stop_reactor)
    reactor.run()
    # run.addBoth(stop_reactor)

    # log.msg(run.result)


if __name__ == "__main__":
    main()
