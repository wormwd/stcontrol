#!/usr/bin/env python

import time

from configparser import ConfigParser
import xml.etree.ElementTree as ET

import requests
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf


def to_xml(node):
    return b'<?xml version="1.0"?>\n' + ET.tostring(node)


class SoundTouchListener(ServiceListener):
    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = ConfigParser()
        if "soundtouch" not in self.config:
            self.config["soundtouch"] = {}
        self.services = {}
        self.idle = set()
        self.playing = set()

    def remove_service(self, zeroconf, typ, name):
        if name in self.services:
            del self.services[name]
        print(f"Service {name} removed")

    def add_service(self, zeroconf, typ, name):
        info = zeroconf.get_service_info(typ, name)
        print(f"Service {name} added, service info: {info}")
        ip = info.parsed_addresses()[0]
        uri = f"http://{ip}:{info.port}"
        self.services[name] = {
            "uri": uri,
            "ip": ip,
            "mac": info.properties.get(b"MAC").decode(),
            "playing": False,
        }
        service = ET.fromstring(requests.get(f"{uri}/now_playing").text)
        if service.findtext("playStatus") == "PLAY_STATE":
            self.services[name]["playing"] = True
        host, idle = scan(self.services)
        if idle and not host:
            host = play_default(idle[0], self.config)
            idle = idle[1:]
        if host and idle:
            set_zone(host, idle)

    def update_service(self, zc, type_, name):
        pass


def scan(services):
    host = None
    idle = []
    if len(services) > 1:
        for service in services.values():
            if service["playing"] and not host:
                host = service
            else:
                idle.append(service)
    return host, idle


def play_default(host, config):
    key = ET.Element("key")
    key.set("state", "release")
    key.set("sender", "Gabbo")
    preset_num = "1"
    if config.has_section("soundtouch") and "preset" in config["soundtouch"]:
        if config.get("soundtouch", "preset") in [str(i) for i in range(1, 7)]:
            preset_num = config.get("soundtouch", "preset")
    key.text = f"PRESET_{preset_num}"
    print(f"Playing {key.text}")
    requests.post(f"{host.get('uri')}/key", to_xml(key))
    return host


def set_zone(host, idle):
    zone = ET.Element("zone")
    zone.set("master", host.get("mac"))
    zone.set("senderIPAddress", host.get("ip"))
    zone.set("senderIsMaster", "true")
    for client in idle:
        member = ET.SubElement(zone, "member")
        member.set("ipaddress", client.get("ip"))
        member.text = client.get("mac")
    requests.post(f"{host.get('uri')}/setZone", to_xml(zone))


def main():
    config = ConfigParser()
    config.read("config.ini")
    zc = Zeroconf()
    listener = SoundTouchListener(config)
    ServiceBrowser(zc, "_soundtouch._tcp.local.", listener)
    # Wait a bit to make sure we find all devices
    time.sleep(10)
    zc.close()


if __name__ == "__main__":
    main()
