#!/usr/bin/env python
 
import sys, time
from daemon import Daemon

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.names import dns
from twisted.names import client, server
from twisted.names import authority

from dbresolver import DatabaseAuthority

import mysql.connector
from mysql.connector import errorcode
 
class DnsDaemon(Daemon):
    def run(self):
        authority = DatabaseAuthority()
        resolver = client.Resolver(servers=[('4.2.2.2', 53)])
        verbosity = 0

        factory = server.DNSServerFactory(authorities=[authority], clients=[resolver], verbose=verbosity)

        protocol = dns.DNSDatagramProtocol(factory)
        factory.noisy = protocol.noisy = verbosity

        reactor.listenUDP(53, protocol)
        reactor.listenTCP(53, factory)
        reactor.run()
 
if __name__ == "__main__":
        daemon = DnsDaemon('/tmp/daemon-example.pid')
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                elif 'run' == sys.argv[1]:
                        daemon.run()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)
