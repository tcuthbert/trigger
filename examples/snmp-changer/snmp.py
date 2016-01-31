import sys
import json
from trigger.cmds import Commando, ReactorlessCommando
from trigger.netdevices import NetDevices, NetDevice
from twisted.internet import reactor
from twisted.python import log



class Device(object):
    snmp_gather_cmds = ['show snmp community']
    snmp_deploy_cmd = 'snmp-server {host} community {community} {mode}'
    snmp_deployment = ['config t', 'end', 'wr mem']

    def __init__(self, name):
        self.name = name
        self.remove_communities = []
        self.commands = []
        self.version = None
        self.results = {}
        self.commando = None

    def __repr__(self):
        return unicode(self.name)

    def __unicode__(self):
        return unicode(self.name)

    def filter_stale_communities(self):
        self.remove_communities = [c for c in self.remove_communities if c in config["oldCommunityStrings"]]

    def build_deployment(self):
        """
        Build deployment config.
        """
        if self.remove_communities:
            for community in self.remove_communities:
                line = "no snmp-server community {community}".format(community=community)
                self.snmp_deployment.insert(1, line)

        log.msg("Following communities will be removed on {0}: {1}".format(self.name, self.remove_communities))

        for community in config["newCommunityStrings"]:
            host, community, mode = community[u'host'], community['community'], community['mode']
            line = self.snmp_deploy_cmd.format(
                    host=host,
                    community=community,
                    mode=mode)
            # Trim any excess whitespace
            line = ' '.join(line.split())
            self.snmp_deployment.insert(1, line)

        log.msg("New SNMP Deployment: {0}".format(self.snmp_deployment))
    

class GetSNMPInfo(ReactorlessCommando):
    """
    Collect SNMP information from Device device.
    """

    commands = Device.snmp_gather_cmds


class WriteSNMPCommunities(ReactorlessCommando):
    """
    Write SNMP information to Device.
    """
    def to_cisco(self, dev, commands=None, extra=None):
        return snmp_hosts[dev.nodeName].snmp_deployment

    def from_cisco(self, results, device, commands=None):
        commands = commands or self.commands

        log.msg('Received %r from %s' % (results, device))
        self.store_results(device, self.map_results(commands, results))

    def errback(self, failure, device):
        print "Error in WriteSNMPCommunities for device {}\n{}".format(
            device,
            failure.getTraceback()
        )


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
    rv = []

    for hostname, cli_output in result.items():
        dev = snmp_hosts.get(hostname)
        if cli_output.values()[0] is None:
            pass
        else:
            communities = regexp.findall(cli_output.values()[0])
            dev.remove_communities = communities
            dev.filter_stale_communities()
        dev.build_deployment()
        rv.append(dev)

    return rv or None


def start_deployment(devices):
    return WriteSNMPCommunities(devices).run()


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
    jobs.addCallback(start_deployment)
    jobs.addBoth(stop_reactor)
    reactor.run()
    for k, v in snmp_hosts.items():
        log.msg("The following was deployed to {0} // \n{1}".format(k, "\n".join(v.snmp_deployment)))


if __name__ == "__main__":
    main()
