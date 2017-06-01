# -*- coding: utf-8 -*-
"""
Onyx Project
http://onyxproject.fr
Software under licence Creative Commons 3.0 France
http://creativecommons.org/licenses/by-nc-sa/3.0/fr/
You may not use this software for commercial purposes.
@author :: Cassim Khouani
"""
import os
import sys
sys.path.append("/home/pi/Onyx")
import threading
import time
import traceback
try:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import SimpleHTTPRequestHandler

try:
    from SocketServer import TCPServer as HTTPServer
except ImportError:
    from http.server import HTTPServer
from os.path import dirname, realpath
from shutil import copyfile
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep

from pyric import pyw
from wifi import Cell

from onyx.messagebus.client.ws import WebsocketClient
from onyx.messagebus.message import Message
from onyx.util import connected
from onyx.util.log import getLogger

LOG = getLogger("WiFiClient")

SCRIPT_DIR = dirname(realpath(__file__))

def cli_no_output(*args):
    ''' Invoke a command line and return result '''
    LOG.info("Command: %s" % list(args))
    proc = Popen(args=args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return {'code': proc.returncode, 'stdout': stdout, 'stderr': stderr}


def cli(*args):
    ''' Invoke a command line, then log and return result '''
    LOG.info("Command: %s" % list(args))
    proc = Popen(args=args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    result = {'code': proc.returncode, 'stdout': stdout, 'stderr': stderr}
    LOG.info("Command result: %s" % result)
    return result


def wpa(*args):
    idx = 0
    result = cli('wpa_cli', '-i', *args)
    out = result.get("stdout", "\n")
    if "interface" in out:
        idx = 1
    return str(out.split("\n")[idx])


def sysctrl(*args):
    return cli('systemctl', *args)


class CaptiveHTTPRequestHandler(SimpleHTTPRequestHandler):
    ''' Serve a single website, 303 redirecting all other requests to it '''

    def do_HEAD(self):
        LOG.info("do_HEAD being called....")
        if not self.redirect():
            SimpleHTTPRequestHandler.do_HEAD(self)

    def do_GET(self):
        LOG.info("do_GET being called....")
        if not self.redirect():
            SimpleHTTPRequestHandler.do_GET(self)

    def redirect(self):
        try:
            LOG.info("***********************")
            LOG.info("**   HTTP Request   ***")
            LOG.info("***********************")
            LOG.info("Requesting: " + self.path)
            LOG.info("REMOTE_ADDR:" + self.client_address[0])
            LOG.info("SERVER_NAME:" + self.server.server_address[0])
            LOG.info("SERVER_PORT:" + str(self.server.server_address[1]))
            LOG.info("SERVER_PROTOCOL:" + self.request_version)
            LOG.info("HEADERS...")
            LOG.info(self.headers)
            LOG.info("***********************")

            # path = self.translate_path(self.path)
            if "onyx.ai" in self.headers['host']:
                LOG.info("No redirect")
                return False
            else:
                LOG.info("303 redirect to http://start.onyx.ai")
                self.send_response(303)
                self.send_header("Location", "http://start.onyx.ai")
                self.end_headers()
                return True
        except:
            tb = traceback.format_exc()
            LOG.info("exception caught")
            LOG.info(tb)
            return False


class WebServer(Thread):
    ''' Web server for devices connected to the temporary access point '''

    def __init__(self, host, port):
        super(WebServer, self).__init__()
        self.daemon = True
        LOG.info("Creating TCPServer...")
        self.server = HTTPServer((host, port), CaptiveHTTPRequestHandler)
        LOG.info("Created TCPServer")

    def run(self):
        LOG.info("Starting Web Server at %s:%s" % self.server.server_address)
        LOG.info("Serving from: %s" % os.path.join(SCRIPT_DIR, 'web'))
        os.chdir(os.path.join(SCRIPT_DIR, 'web'))
        self.server.serve_forever()
        LOG.info("Web Server stopped!")


class AccessPoint:
    template = """interface={interface}
bind-interfaces
server={server}
domain-needed
bogus-priv
dhcp-range={dhcp_range_start}, {dhcp_range_end}, 12h
address=/#/{server}
"""

    def __init__(self, wiface):
        self.wiface = wiface
        self.iface = 'p2p-wlan0-0'
        self.subnet = '172.24.1'
        self.ip = self.subnet + '.1'
        self.ip_start = self.subnet + '.50'
        self.ip_end = self.subnet + '.150'
        self.password = "ONYXLABS"

    def up(self):
        try:
            card = pyw.getcard(self.iface)
        except:
            wpa(self.wiface, 'p2p_group_add', 'persistent=0')
            card = pyw.getcard(self.wiface)
        pyw.inetset(card, self.ip)
        copyfile('/etc/dnsmasq.conf', '/tmp/dnsmasq-bk.conf')
        self.save()
        sysctrl('restart', 'dnsmasq.service')

    def get_iface(self):
        for iface in pyw.winterfaces():
            if "p2p" in iface:
                return iface

    def down(self):
        sysctrl('stop', 'dnsmasq.service')
        sysctrl('disable', 'dnsmasq.service')
        wpa(self.wiface, 'p2p_group_remove', self.iface)
        copyfile('/tmp/dnsmasq-bk.conf', '/etc/dnsmasq.conf')

    def save(self):
        data = {
            "interface": self.iface,
            "server": self.ip,
            "dhcp_range_start": self.ip_start,
            "dhcp_range_end": self.ip_end
        }
        try:
            LOG.info("Writing to: /etc/dnsmasq.conf")
            with open('/etc/dnsmasq.conf', 'w') as f:
                f.write(self.template.format(**data))
        except Exception as e:
            LOG.error("Fail to write: /etc/dnsmasq.conf")
            raise e


class WiFi:
    def __init__(self):
        self.iface = pyw.winterfaces()[0]
        self.ap = AccessPoint(self.iface)
        self.server = None
        self.ws = WebsocketClient()
        self.init_events()
        self.conn_monitor = None
        self.conn_monitor_stop = threading.Event()

    def init_events(self):
        '''
            Register handlers for various websocket events used
            to communicate with outside systems.
        '''

        self.ws.on('onyx.wifi.start', self.start)

        # These events are generated by Javascript in the captive
        # portal.
        self.ws.on('onyx.wifi.stop', self.stop)
        self.ws.on('onyx.wifi.scan', self.scan)
        self.ws.on('onyx.wifi.connect', self.connect)

    def start(self, event=None):
        '''
           Fire up the Onyx access point for the user to connect to
           with a phone or computer.
        '''
        LOG.info("Starting access point...")

        # Fire up our access point
        self.ap.up()
        if not self.server:
            LOG.info("Creating web server...")
            self.server = WebServer(self.ap.ip, 80)
            LOG.info("Starting web server...")
            self.server.start()
            LOG.info("Created web server.")

        LOG.info("Access point started!\n%s" % self.ap.__dict__)
        self._start_connection_monitor()

    def _connection_prompt(self, prefix):
        # let the user know to connect to it...
        passwordSpelled = ",  ".join(self.ap.password)
        ################SPEAKKKKK FONCTIONNNN #####################


    def _start_connection_monitor(self):
        LOG.info("Starting monitor thread...\n")
        if self.conn_monitor is not None:
            LOG.info("Killing old thread...\n")
            self.conn_monitor_stop.set()
            self.conn_monitor_stop.wait()

        self.conn_monitor = threading.Thread(
            target=self._do_connection_monitor,
            args={})
        self.conn_monitor.daemon = True
        self.conn_monitor.start()
        LOG.info("Monitor thread setup complete.\n")

    def _stop_connection_monitor(self):
        ''' Set flag that will let monitoring thread close '''
        self.conn_monitor_stop.set()

    def _do_connection_monitor(self):
        LOG.info("Invoked monitor thread...\n")
        mtimeLast = os.path.getmtime('/var/lib/misc/dnsmasq.leases')
        bHasConnected = False
        cARPFailures = 0
        timeStarted = time.time()
        timeLastAnnounced = 0  # force first announcement to now
        self.conn_monitor_stop.clear()

        while not self.conn_monitor_stop.isSet():
            # do our monitoring...
            mtime = os.path.getmtime('/var/lib/misc/dnsmasq.leases')
            if mtimeLast != mtime:
                # Something changed in the dnsmasq lease file -
                # presumably a (re)new lease
                bHasConnected = True
                cARPFailures = 0
                mtimeLast = mtime
                timeStarted = time.time()  # reset start time after connection
                timeLastAnnounced = time.time() - 45  # announce how to connect

            if time.time() - timeStarted > 60 * 5:
                # After 5 minutes, shut down the access point
                LOG.info("Auto-shutdown of access point after 5 minutes")
                self.stop()
                continue

            if time.time() - timeLastAnnounced >= 45:
                if bHasConnected:
                    print('done')
                    ####SPEAK FONCTION####
                else:
                    self._connection_prompt("Allow me to walk you through the "
                                            " wifi setup process; ")
                timeLastAnnounced = time.time()

            if bHasConnected:
                # Flush the ARP entries associated with our access point
                # This will require all network hardware to re-register
                # with the ARP tables if still present.
                if cARPFailures == 0:
                    res = cli_no_output('ip', '-s', '-s', 'neigh', 'flush',
                                        self.ap.subnet + '.0/24')
                    # Give ARP system time to re-register hardware
                    sleep(5)

                # now look at the hardware that has responded, if no entry
                # shows up on our access point after 2*5=10 seconds, the user
                # has disconnected
                if not self._is_ARP_filled():
                    cARPFailures += 1
                    if cARPFailures > 2:
                        self._connection_prompt("Connection lost,")
                        bHasConnected = False
                else:
                    cARPFailures = 0
            sleep(5)  # wait a bit to prevent thread from hogging CPU

        LOG.info("Exiting monitor thread...\n")
        self.conn_monitor_stop.clear()

    def _is_ARP_filled(self):
        res = cli_no_output('/usr/sbin/arp', '-n')
        out = str(res.get("stdout"))
        if out:
            # Parse output, skipping header
            for o in out.split("\n")[1:]:
                if o[0:len(self.ap.subnet)] == self.ap.subnet:
                    if "(incomplete)" in o:
                        # ping the IP to get the ARP table entry reloaded
                        ip_disconnected = o.split(" ")[0]
                        cli_no_output('/bin/ping', '-c', '1', '-W', '3',
                                      ip_disconnected)
                    else:
                        return True  # something on subnet is connected!
        return False

    def scan(self, event=None):
        LOG.info("Scanning wifi connections...")
        networks = {}
        status = self.get_status()

        for cell in Cell.all(self.iface):
            update = True
            ssid = cell.ssid
            quality = self.get_quality(cell.quality)

            # If there are duplicate network IDs (e.g. repeaters) only
            # report the strongest signal
            if networks.__contains__(ssid):
                update = networks.get(ssid).get("quality") < quality
            if update and ssid:
                networks[ssid] = {
                    'quality': quality,
                    'encrypted': cell.encrypted,
                    'connected': self.is_connected(ssid, status)
                }
        self.ws.emit(Message("onyx.wifi.scanned",
                             {'networks': networks}))
        LOG.info("Wifi connections scanned!\n%s" % networks)

    @staticmethod
    def get_quality(quality):
        values = quality.split("/")
        return float(values[0]) / float(values[1])

    def connect(self, event=None):
        if event and event.data:
            ssid = event.data.get("ssid")
            connected = self.is_connected(ssid)

            if connected:
                LOG.warn("Onyx is already connected to %s" % ssid)
            else:
                self.disconnect()
                LOG.info("Connecting to: %s" % ssid)
                nid = wpa(self.iface, 'add_network')
                wpa(self.iface, 'set_network', nid, 'ssid', '"' + ssid + '"')

                if event.data.__contains__("pass"):
                    psk = '"' + event.data.get("pass") + '"'
                    wpa(self.iface, 'set_network', nid, 'psk', psk)
                else:
                    wpa(self.iface, 'set_network', nid, 'key_mgmt', 'NONE')

                wpa(self.iface, 'enable', nid)
                connected = self.get_connected(ssid)
                if connected:
                    wpa(self.iface, 'save_config')

            self.ws.emit(Message("onyx.wifi.connected",
                                 {'connected': connected}))
            LOG.info("Connection status for %s = %s" % (ssid, connected))

            if connected:
                print("Thank you, I'm now connected to the internet and ready for use")

    def disconnect(self):
        status = self.get_status()
        nid = status.get("id")
        if nid:
            ssid = status.get("ssid")
            wpa(self.iface, 'disable', nid)
            LOG.info("Disconnecting %s id: %s" % (ssid, nid))

    def get_status(self):
        res = cli('wpa_cli', '-i', self.iface, 'status')
        out = str(res.get("stdout"))
        if out:
            return dict(o.split("=") for o in out.split("\n")[:-1])
        return {}

    def get_connected(self, ssid, retry=5):
        connected = self.is_connected(ssid)
        while not connected and retry > 0:
            sleep(2)
            retry -= 1
            connected = self.is_connected(ssid)
        return connected

    def is_connected(self, ssid, status=None):
        status = status or self.get_status()
        state = status.get("wpa_state")
        return status.get("ssid") == ssid and state == "COMPLETED"

    def stop(self, event=None):
        LOG.info("Stopping access point...")
        self._stop_connection_monitor()
        self.ap.down()
        if self.server:
            self.server.server.shutdown()
            self.server.server.server_close()
            self.server.join()
            self.server = None
        LOG.info("Access point stopped!")

    def _do_net_check(self):
        # give system 5 seconds to resolve network or get plugged in
        sleep(5)

        LOG.info("Checking internet connection again")
        if not connected() and self.conn_monitor is None:
            #####SPEAK FONCTION ###
            print(
                "This device is not connected to the Internet. Either plug "
                "in a network cable or hold the button on top for two "
                "seconds, then select wifi from the menu")

    def run(self):
        try:
            # When the system first boots up, check for a valid internet
            # connection.
            LOG.info("Checking internet connection")
            if not connected():
                LOG.info("No connection initially, waiting 20...")
                self.net_check = threading.Thread(
                    target=self._do_net_check,
                    args={})
                self.net_check.daemon = True
                self.net_check.start()
            else:
                LOG.info("Connection found!")

            self.ws.run_forever()
        except Exception as e:
            LOG.error("Error: {0}".format(e))
            self.stop()


def main():
    wifi = WiFi()
    try:
        wifi.run()
    except Exception as e:
        print(e)
    finally:
        sys.exit()


if __name__ == "__main__":
    main()