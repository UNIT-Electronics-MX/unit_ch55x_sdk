"""nRF24L01+ peer for a Raspberry Pi Pico and the CH55x USB2NRF bridge.

Copy this file to the MicroPython board as main.py. The pin numbers below are
GPIO numbers supplied for the MicroPython board, not CH55x pin numbers.
"""

from machine import Pin, SoftSPI
from time import sleep_ms, sleep_us, ticks_diff, ticks_ms
import json
import sys
try:
    import select
except ImportError:
    import uselect as select


PIN_CE = 28
PIN_CSN = 27
PIN_SCK = 26
PIN_MOSI = 15
PIN_MISO = 14
PIN_IRQ = 8
AUTO_ECHO = False  # set True only to test automatic replies
BEACON_INTERVAL_MS = 0  # set to 5000 to send a diagnostic beacon every 5 s
PICO_MESSAGE = b"PICO_READY"  # diagnostic beacon payload, 1-32 bytes

SETTINGS_FILE = "nrf_pico.json"
# Addresses are reversed: Pico TX = CH55x RX, Pico RX = CH55x TX.
DEFAULT_SETTINGS = {
    "channel": 2,
    "speed": 0,
    "tx": "C2C2C2C2C2",
    "rx": "E7E7E7E7E7",
    "auto_ack": True,
    "strip_line_ends": True,
    "hex_mode": False,
}
SPEED_REGISTERS = (0x26, 0x06, 0x0E)
SPEED_LABELS = ("250kbps", "1Mbps", "2Mbps")


def decode_address(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("address must contain 10 hexadecimal digits")
    if any(char not in "0123456789abcdefABCDEF" for char in value):
        raise ValueError("invalid hexadecimal address")
    address = bytearray()
    for i in range(0, 10, 2):
        address.append(int(value[i:i + 2], 16))
    return bytes(address)


def validate_settings(value):
    if not isinstance(value, dict):
        raise ValueError("invalid configuration")
    if type(value.get("channel")) is not int or not 0 <= value["channel"] <= 0x7F:
        raise ValueError("channel out of range (00-7F)")
    if type(value.get("speed")) is not int or not 0 <= value["speed"] <= 2:
        raise ValueError("data rate out of range (00-02)")
    decode_address(value.get("tx"))
    decode_address(value.get("rx"))
    for key in ("auto_ack", "strip_line_ends", "hex_mode"):
        if type(value.get(key)) is not bool:
            raise ValueError("invalid option: " + key)
    return value


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as settings_file:
            saved = json.load(settings_file)
        return validate_settings(saved)
    except (OSError, ValueError, TypeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(value):
    with open(SETTINGS_FILE, "w") as settings_file:
        settings_file.write(json.dumps(value))


class NRF24Peer:
    CONFIG = 0x00
    EN_AA = 0x01
    EN_RXADDR = 0x02
    SETUP_AW = 0x03
    SETUP_RETR = 0x04
    RF_CH = 0x05
    RF_SETUP = 0x06
    STATUS = 0x07
    RX_ADDR_P0 = 0x0A
    RX_ADDR_P1 = 0x0B
    TX_ADDR = 0x10
    FIFO_STATUS = 0x17
    DYNPD = 0x1C
    FEATURE = 0x1D

    def __init__(self, settings):
        self.settings = settings
        self.ce = Pin(PIN_CE, Pin.OUT, value=0)
        self.csn = Pin(PIN_CSN, Pin.OUT, value=1)
        self.irq = Pin(PIN_IRQ, Pin.IN)
        self.spi = SoftSPI(
            baudrate=100_000,
            polarity=0,
            phase=0,
            sck=Pin(PIN_SCK),
            mosi=Pin(PIN_MOSI),
            miso=Pin(PIN_MISO),
        )
        sleep_ms(100)
        try:
            self._configure()
        except OSError as exc:
            print("nRF error:", exc)

    def _read_reg(self, reg):
        self.csn.off()
        self.spi.write(bytes((reg,)))
        value = self.spi.read(1)[0]
        self.csn.on()
        return value

    def _write_reg(self, reg, value):
        self.csn.off()
        self.spi.write(bytes((0x20 | reg, value)))
        self.csn.on()

    def _write_addr(self, reg, address):
        self.csn.off()
        self.spi.write(bytes((0x20 | reg,)) + address)
        self.csn.on()

    def _command(self, command):
        self.csn.off()
        self.spi.write(bytes((command,)))
        self.csn.on()

    def _configure(self):
        self.ce.off()
        self._write_reg(self.CONFIG, 0x0C)  # 16-bit CRC, power down
        self._write_reg(self.SETUP_AW, 0x03)  # five-byte addresses
        self._write_reg(self.EN_RXADDR, 0x03)  # pipes 0 (ACK) and 1 (data)
        self._write_reg(self.EN_AA, 0x03 if self.settings["auto_ack"] else 0x00)
        self._write_reg(self.SETUP_RETR, 0x4F)
        self._write_reg(self.RF_CH, self.settings["channel"])
        self._write_reg(self.RF_SETUP, SPEED_REGISTERS[self.settings["speed"]])
        tx_address = decode_address(self.settings["tx"])
        self._write_addr(self.TX_ADDR, tx_address)
        self._write_addr(self.RX_ADDR_P0, tx_address)
        self._write_addr(self.RX_ADDR_P1, decode_address(self.settings["rx"]))
        self._write_reg(self.FEATURE, 0x04)  # dynamic payload length
        if self._read_reg(self.FEATURE) != 0x04:
            # Some compatible modules need ACTIVATE before FEATURE is writable.
            self.csn.off()
            self.spi.write(b"\x50\x73")
            self.csn.on()
            self._write_reg(self.FEATURE, 0x04)
        self._write_reg(self.DYNPD, 0x03)
        if (self._read_reg(self.SETUP_AW) != 0x03
                or self._read_reg(self.RF_CH) != self.settings["channel"]
                or self._read_reg(self.RF_SETUP) != SPEED_REGISTERS[self.settings["speed"]]
                or self._read_reg(self.EN_AA) != (0x03 if self.settings["auto_ack"] else 0x00)
                or self._read_reg(self.FEATURE) != 0x04
                or self._read_reg(self.DYNPD) != 0x03):
            raise OSError("nRF24L01+ does not respond over SPI; check power and wiring")
        self._write_reg(self.STATUS, 0x70)  # clear pending IRQ flags
        self._command(0xE1)  # flush TX
        self._command(0xE2)  # flush RX
        self._write_reg(self.CONFIG, 0x0F)  # power up, RX mode
        sleep_ms(2)
        self.ce.on()

    def connected(self):
        return (self._read_reg(self.CONFIG) == 0x0F
                and self._read_reg(self.SETUP_AW) == 0x03
                and self._read_reg(self.RF_CH) == self.settings["channel"]
                and self._read_reg(self.RF_SETUP) == SPEED_REGISTERS[self.settings["speed"]])

    def receive(self):
        if not self.connected():
            return None
        # IRQ is active low; also check the FIFO in case an IRQ flag was cleared.
        if self.irq.value() and (self._read_reg(self.FIFO_STATUS) & 0x01):
            return None
        self.csn.off()
        self.spi.write(b"\x60")  # R_RX_PL_WID
        size = self.spi.read(1)[0]
        self.csn.on()
        if not 1 <= size <= 32:
            self._command(0xE2)
            self._write_reg(self.STATUS, 0x40)
            return None
        self.csn.off()
        self.spi.write(b"\x61")  # R_RX_PAYLOAD
        payload = self.spi.read(size)
        self.csn.on()
        self._write_reg(self.STATUS, 0x40)
        return payload

    def send(self, payload):
        payload = bytes(payload)
        if not 1 <= len(payload) <= 32:
            raise ValueError("message must contain 1 to 32 bytes")
        if not self.connected():
            raise OSError("nRF24L01+ does not respond over SPI")
        self.ce.off()
        self._write_reg(self.CONFIG, 0x0E)  # TX mode
        sleep_us(150)
        self._write_reg(self.STATUS, 0x30)
        self._command(0xE1)
        self.csn.off()
        self.spi.write(b"\xA0" + payload)  # W_TX_PAYLOAD
        self.csn.on()
        self.ce.on()
        sleep_us(15)
        self.ce.off()
        start = ticks_ms()
        status = 0
        while ticks_diff(ticks_ms(), start) < 100:
            status = self._read_reg(self.STATUS)
            if status & 0x30:
                break
            sleep_ms(1)
        self._write_reg(self.STATUS, 0x30)
        if not (status & 0x20):
            self._command(0xE1)
        self._write_reg(self.CONFIG, 0x0F)  # return to RX mode
        sleep_us(150)
        self.ce.on()
        if not self.connected():
            raise OSError("nRF24L01+ does not respond over SPI")
        if status & 0x20:
            return True
        if status & 0x10:
            return False  # MAX_RT: no RF acknowledgement
        raise OSError("nRF24L01+ transmission did not complete")


def parse_hex_byte(value):
    if len(value) != 2 or any(char not in "0123456789abcdefABCDEF" for char in value):
        raise ValueError("two hexadecimal digits are required")
    return int(value, 16)


def print_menu():
    print("\n# Pico nRF24L01+ menu (local commands)")
    print("!              Show settings and SPI status")
    print("!h or !?       Show this menu")
    print("!cXX           Channel 00-7F, example !c02")
    print("!tXXXXXXXXXX   Five-byte TX address, example !tC2C2C2C2C2")
    print("!rXXXXXXXXXX   Five-byte RX address, example !rE7E7E7E7E7")
    print("!sXX           Data rate: 00=250kbps, 01=1Mbps, 02=2Mbps")
    print("!oADLx         Options: A/a ACK, D dynamic, L strip LF/l add LF, X/x hex")
    print("               d is unavailable; dynamic payload is required")
    print("text + Enter   Send text to CH55x; !! sends a literal !")
    print("Settings are saved in", SETTINGS_FILE)


def print_settings():
    print("# nRF24L01+ Configuration (Pico):")
    print("# RF channel: %02X" % settings["channel"])
    print("# TX address:", settings["tx"])
    print("# RX address:", settings["rx"])
    print("# Data rate: ", SPEED_LABELS[settings["speed"]])
    print("nRF SPI:", "OK" if radio.connected() else "NO RESPONSE")
    print("Dynamic payload:", "OK" if radio._read_reg(radio.FEATURE) == 0x04
          and radio._read_reg(radio.DYNPD) == 0x03 else "ERROR")
    print("Config register: %02X" % radio._read_reg(radio.CONFIG))
    print("Status register: %02X" % radio._read_reg(radio.STATUS))
    print("FIFO Status register: %02X" % radio._read_reg(radio.FIFO_STATUS))
    print("Options: %s %s %s %s" % (
        "A" if settings["auto_ack"] else "a",
        "D",  # variable-length radio packets require dynamic payload
        "L" if settings["strip_line_ends"] else "l",
        "X" if settings["hex_mode"] else "x",
    ))


settings = load_settings()
radio = NRF24Peer(settings)
print("Pico nRF24L01+: waiting for CH55x messages")
print_menu()
print_settings()
last_beacon = ticks_ms()
console_line = bytearray()
console_overflow = False
try:
    console_poll = select.poll()
    console_poll.register(sys.stdin, select.POLLIN)
    print("Type a message or ! to configure; press Enter")
except (OSError, AttributeError, TypeError):
    console_poll = None  # radio reception still works without a console
    print("Console input unavailable; check the Pico USB serial connection")


def send_to_ch552(message):
    """Send 1-32 bytes from the Pico to the CH552 radio/USB bridge."""
    if isinstance(message, str):
        message = message.encode()
    return radio.send(message)


def configure_from_console(command):
    global settings
    if command in ("!h", "!?"):
        print_menu()
        print_settings()
        return
    if command == "!":
        print_settings()
        return
    candidate = settings.copy()
    kind = command[1:2]
    argument = command[2:]
    try:
        if kind == "c":
            candidate["channel"] = parse_hex_byte(argument)
        elif kind == "s":
            candidate["speed"] = parse_hex_byte(argument)
        elif kind in ("t", "r"):
            decode_address(argument)
            candidate["tx" if kind == "t" else "rx"] = argument.upper()
        elif kind == "o":
            if not argument:
                raise ValueError("missing options; use !oADLx")
            for option in argument:
                if option == "A":
                    candidate["auto_ack"] = True
                elif option == "a":
                    candidate["auto_ack"] = False
                elif option == "L":
                    candidate["strip_line_ends"] = True
                elif option == "l":
                    candidate["strip_line_ends"] = False
                elif option == "X":
                    candidate["hex_mode"] = True
                elif option == "x":
                    candidate["hex_mode"] = False
                elif option == "D":
                    pass  # always enabled for variable-length payloads
                elif option == "d":
                    raise ValueError("!od is unavailable: this version requires dynamic payload")
                else:
                    raise ValueError("unknown option: " + option)
        else:
            raise ValueError("unknown command; use !h")
        validate_settings(candidate)
        if candidate == settings:
            print_settings()
            return
        radio_changed = any(candidate[key] != settings[key]
                            for key in ("channel", "speed", "tx", "rx", "auto_ack"))
        if radio_changed:
            radio.settings = candidate
            try:
                radio._configure()
            except OSError:
                radio.settings = settings
                try:
                    radio._configure()
                except OSError:
                    pass
                raise
        settings = candidate
        try:
            save_settings(settings)
        except OSError as exc:
            print("Could not save settings:", exc)
        print_settings()
    except (ValueError, OSError) as exc:
        print("Configuration error:", exc)


def send_console_line(line):
    literal_bang = line.startswith(b"!!")
    if literal_bang:
        line = line[1:]  # send a literal ! over the radio
    elif line.startswith(b"!"):
        configure_from_console(line.decode())
        return
    if settings["hex_mode"] and not literal_bang:
        try:
            digits = b"".join(line.split())
            if len(digits) % 2:
                raise ValueError("hex input must contain pairs of digits")
            payload = bytearray()
            for i in range(0, len(digits), 2):
                payload.append(int(digits[i:i + 2], 16))
            payload = bytes(payload)
        except ValueError as exc:
            print("Invalid hex input:", exc)
            return
    else:
        payload = bytes(line)
    if not settings["strip_line_ends"]:
        payload += b"\n"
    if not 1 <= len(payload) <= 32:
        print("Message must contain 1 to 32 bytes")
        return
    try:
        if send_to_ch552(payload):
            print("Sent to CH55x:", payload)
        else:
            print("No ACK from CH55x")
    except (OSError, ValueError) as exc:
        print("Send error:", exc)


while True:
    message = radio.receive()
    if message is not None:
        print("RX:", message)
        if AUTO_ECHO:
            reply = b"echo:" + message[:27]
            try:
                if send_to_ch552(reply):
                    print("TX:", reply)
                else:
                    print("No ACK from CH55x")
            except OSError as exc:
                print("Reply error:", exc)
    if console_poll is not None:
        # Drain pending characters without blocking incoming radio packets.
        for _ in range(64):
            events = console_poll.poll(0)
            if not events:
                break
            if not (events[0][1] & select.POLLIN):
                console_poll = None
                break
            char = sys.stdin.read(1)
            if not char:
                console_poll = None
                break
            data = char.encode() if isinstance(char, str) else char
            if data in (b"\r", b"\n"):
                if console_overflow:
                    print("Maximum message length exceeded")
                elif console_line:
                    send_console_line(bytes(console_line))
                console_line = bytearray()
                console_overflow = False
            elif data in (b"\x08", b"\x7f"):
                if console_line:
                    del console_line[-1]
            elif data[0] >= 0x20:
                if len(console_line) + len(data) <= 64:
                    console_line.extend(data)
                else:
                    console_overflow = True
    if BEACON_INTERVAL_MS and ticks_diff(ticks_ms(), last_beacon) >= BEACON_INTERVAL_MS:
        last_beacon = ticks_ms()
        try:
            send_to_ch552(PICO_MESSAGE)
        except OSError:
            pass  # retry on the next interval if the local radio stopped answering
    sleep_ms(10)
