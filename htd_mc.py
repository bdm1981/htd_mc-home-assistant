import socket
import time
import logging

MAX_HTD_VOLUME = 60
DEFAULT_HTD_MC_PORT = 10006

_LOGGER = logging.getLogger(__name__)


def to_correct_string(message):
    string = ""
    for i in range(len(message)):
        string += hex(message[i]) + ","
    return string[:-1]


class HtdMcClient:
    def __init__(self, ip_address, port=DEFAULT_HTD_MC_PORT):
        self.ip_address = ip_address
        self.port = port
        self.zones = {
            k: {
                "zone": k,
                "power": None,
                "input": None,
                "vol": None,
                "mute": None,
                "source": None,
            }
            for k in range(1, 12)
        }

    def parse(self, cmd, message, zone_number):
        if len(message) > 14:
            zones = list()
            # each chunk represents a different zone that should be 14 bytes long,
            # query_all should work for each zone but doesn't, so we only take the first chunk

            # zone0 = message[0:14]
            zone1 = message[14:28]
            zone2 = message[28:42]
            zone3 = message[42:56]
            zone4 = message[56:70]
            zone5 = message[70:84]
            zone6 = message[84:98]
            zone7 = message[98:112]
            zone8 = message[112:126]
            zone9 = message[126:140]
            zone10 = message[140:154]
            zone11 = message[154:168]
            zone12 = message[168:182]

            # again, in a real working world situation, each zone would be correctly populated but we only ever work with 1 and whatever we get back.
            zones.append(zone1)
            zones.append(zone2)
            zones.append(zone3)
            zones.append(zone4)
            zones.append(zone5)
            zones.append(zone6)
            zones.append(zone7)
            zones.append(zone8)
            zones.append(zone9)
            zones.append(zone10)
            zones.append(zone11)
            zones.append(zone12)

            # go through each zone
            for i in zones:
                success = self.parse_message(cmd, i, zone_number) or success
                _LOGGER.debug(self.parse_message(cmd, i, zone_number))

            if not success:
                _LOGGER.warning(f"Update for Zone #{zone_number} failed.")
                print(f"Update for Zone #{zone_number} failed.")

        elif len(message) == 14:
            self.parse_message(cmd, message, zone_number)

        if zone_number is None:
            return self.zones

        return self.zones[zone_number]

    def parse_message(self, cmd, message, zone_number):
        if len(message) != 14:
            return False

        zone = message[2]

        # it seems that even though we send one zone we may not get what we want
        if zone in range(1, 12):
            self.zones[zone]["power"] = "on" if (
                message[4] & 1 << 0) else "off"
            self.zones[zone]["source"] = message[8] + 1
            self.zones[zone]["vol"] = message[9] - 196 if message[9] else 0
            self.zones[zone]["mute"] = "on" if (message[4] & 1 << 1) else "off"

            _LOGGER.debug(
                f"Command for Zone #{zone} retrieved (requested #{zone_number}) --> Cmd = {to_correct_string(cmd)} | Message = {to_correct_string(message)}"
            )
            return True
        else:
            _LOGGER.warning(
                f"Sent command for Zone #{zone_number} but got #{zone} --> Cmd = {to_correct_string(cmd)} | Message = {to_correct_string(message)}"
            )

        return False

    def set_source(self, zone, input):
        computed = 1
        if zone not in range(1, 12):
            _LOGGER.warning("Invalid Zone")
            return

        if input not in range(1, 18):
            _LOGGER.warning("invalid input number")
            return

        if input >= 1 and input <= 12:
            computed = 0x10 + (input - 1)
        elif input >= 13 and input <= 18:
            computed = 0x63 + (input - 13)
        else:
            print("invalid input")

        cmd = bytearray([0x02, 0x00, zone, 0x04, computed])

        self.send_command(cmd, zone)

    def volume_up(self, zone, vol):
        if zone not in range(1, 12):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x01, zone, 0x15, vol])
        self.send_command(cmd, zone)

    def volume_down(self, zone, vol):
        if zone not in range(1, 12):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x01, zone, 0x15, vol])
        self.send_command(cmd, zone)

    def set_volume(self, zone, vol):
        if vol not in range(0, MAX_HTD_VOLUME):
            _LOGGER.warning("Invald Volume")
            return

        zone_info = self.query_zone(zone)

        vol_diff = vol - zone_info["vol"]
        start_time = time.time()

        setVol = vol + 0xC4

        _LOGGER.warning( f"Setting Volume: {sefVol}" )

        if vol_diff < 0:
            for k in range(abs(vol_diff)):
                self.volume_down(zone, setVol)
        elif vol_diff > 0:
            for k in range(vol_diff):
                self.volume_up(zone, setVol)
        else:
            pass

        return

    def toggle_mute(self, zone):
        if zone not in range(1, 12):
            _LOGGER.warning("Invalid Zone")
            return

        if self.zones[zone]["mute"] == "off":
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x1E])
        else:
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x1F])

        self.send_command(cmd, zone)

    def mute_off(self, zone):
        if zone not in range(1, 7):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x1F])
        self.send_command(cmd, zone)

    def query_zone(self, zone):
        if zone not in range(1, 12):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x05, 0x00])
        return self.send_command(cmd, zone)

    def query_all(self):
        cmd = bytearray([0x02, 0x00, 0x00, 0x05, 0x00])
        return self.send_command(cmd)

    def set_power(self, zone, pwr):
        if zone not in range(0, 12):
            _LOGGER.warning("Invalid Zone")
            return

        if pwr not in [0, 1]:
            _LOGGER.warning("invalid power command")
            return

        if zone == 0:
            cmd = bytearray(
                [0x02, 0x00, zone, 0x04, 0x55, 0x5B if pwr else 0x5C])
        else:
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x57 if pwr else 0x58])

        self.send_command(cmd, zone)

    def send_command(self, cmd, zone=None):
        cmd.append(self.checksum(cmd))
        mySocket = socket.socket()
        mySocket.settimeout(0.5)

        try:
            mySocket.connect((self.ip_address, self.port))
            mySocket.send(cmd)
            data = mySocket.recv(1024)
            # _LOGGER.debug(f"Command = {cmd} | Response = {data} ")
            _LOGGER.debug(f"Zone: {zone}")
            mySocket.close()

            return self.parse(cmd, data, zone)
        except socket.timeout:
            print(
                f"unknown response cmd: {cmd} zone: {zone} gateway: {self.ip_address}"
            )
            return self.unknown_response(cmd, zone)

    def unknown_response(self, cmd, zone):
        for zone in range(1, 12):
            self.zones[zone]["power"] = "unknown"
            self.zones[zone]["source"] = 0
            self.zones[zone]["vol"] = 0
            self.zones[zone]["mute"] = "unknown"

        return self.zones[zone]

    def checksum(self, message):
        cs = 0
        for b in message:
            cs += b
        cs = cs & 0xFF
        return cs
