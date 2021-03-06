#!/usr/bin/env python3

from typing import Dict, List

import signal
import pprint

from xml.etree import ElementTree
from collections import defaultdict

from PyQt5.QtDBus import QDBusConnection
from PyQt5.QtDBus import QDBusReply, QDBusMessage, QDBusInterface
from PyQt5.QtCore import QObject, pyqtSlot, QCoreApplication


def call(obj, method, *args):
    msg = obj.call(method, *args)
    reply = QDBusReply(msg)
    if not reply.isValid():
        raise Exception("Error on method call '{}': {}: {}".format(
            method,
            reply.error().name(),
            reply.error().message()))
    else:
        return msg.arguments()


class UDiskManager(QObject):

    def __init__(self, bus):
        super().__init__()

        bus.registerObject('/', self)

        bus.connect('', '',
                    'org.freedesktop.DBus.ObjectManager',
                    'InterfacesAdded', self._on_interfaces_added)

        bus.connect('', '',
                    'org.freedesktop.DBus.ObjectManager',
                    'InterfacesRemoved', self._on_interfaces_removed)

        if False:
            ud_objectmanager = QDBusInterface("org.freedesktop.UDisks2",
                                              "/org/freedesktop/UDisks2",
                                              "org.freedesktop.DBus.ObjectManager",
                                              connection=bus)

            result = call(ud_objectmanager, "GetManagedObjects")
            pprint.pprint(result)

            self._print_blockdevices(bus)
            self._print_drives(bus)

        self.udisks_manager = QDBusInterface("org.freedesktop.UDisks2",
                                             "/org/freedesktop/UDisks2/Manager",
                                             "org.freedesktop.UDisks2.Manager",
                                             connection=bus)

        self._drives: Dict[str, List[str]] = defaultdict(list)
        block_devices = call(self.udisks_manager, "GetBlockDevices", {})[0]

        for block_device in block_devices:
            # block_iface = QDBusInterface("org.freedesktop.UDisks2",
            #                              block_device,
            #                              "org.freedesktop.UDisks2.Block",
            #                              connection=bus)

            block_props = QDBusInterface("org.freedesktop.UDisks2",
                                         block_device,
                                         "org.freedesktop.DBus.Properties",
                                         connection=bus)
            drive = call(block_props, "Get", "org.freedesktop.UDisks2.Block", "Drive")[0]

            self._drives[drive].append(block_device)

    def print_info(self):
        for drive, block_devices in self._drives.items():
            print(drive)
            for block_device in sorted(block_devices):
                print("    ", block_device)
            print()

    def _print_blockdevices(self, bus):
        udisks_manager_introspect = QDBusInterface("org.freedesktop.UDisks2",
                                                   "/org/freedesktop/UDisks2/block_devices",
                                                   "org.freedesktop.DBus.Introspectable",
                                                   connection=bus)

        xml_text, = call(udisks_manager_introspect, "Introspect")
        print(xml_text)
        root = ElementTree.fromstring(xml_text)
        for el in root.findall("./interface"):
            print("  ", el.attrib['name'])

    def _print_drives(self, bus):
        udisks_manager_introspect = QDBusInterface("org.freedesktop.UDisks2",
                                                   "/org/freedesktop/UDisks2/drives",
                                                   "org.freedesktop.DBus.Introspectable",
                                                   connection=bus)

        xml_text, = call(udisks_manager_introspect, "Introspect")
        print(xml_text)
        root = ElementTree.fromstring(xml_text)
        for el in root.findall("./interface"):
            print("  ", el.attrib['name'])

    @pyqtSlot(QDBusMessage)
    def _on_interfaces_added(self, msg: QDBusMessage):
        objpath, interfaces = msg.arguments()
        print("added", objpath)
        for interface, properties in interfaces.items():
            print("  ", interface)
            for name, value in properties.items():
                print("    ", name, "=", value)

    @pyqtSlot(QDBusMessage)
    def _on_interfaces_removed(self, msg: QDBusMessage):
        print("removed", msg.arguments())


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QCoreApplication([])
    bus = QDBusConnection.systemBus()

    udisk_manager = UDiskManager(bus)
    udisk_manager.print_info()
    app.exec()


if __name__ == "__main__":
    main()


# EOF #
