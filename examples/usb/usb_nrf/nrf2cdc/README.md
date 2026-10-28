# USB2NRF: nRF24L01+ to USB CDC bridge

This CH552 example is based on the `nrf2cdc` firmware from [CH552-USB-NRF](https://github.com/wagiminator/CH552-USB-NRF) by **Stefan Wagner (wagiminator)**. The original source headers and credits are preserved.

The firmware provides a USB CDC serial port for sending and receiving nRF24L01+ radio payloads of up to 32 bytes. This example contains its own sources, upload tool, license, and connector pinout; it does not depend on a separate upstream checkout.

## Hardware

The functional wiring follows the supplied 2 × 5 connector diagram:

![nRF24L01+ adapter and CH552 2 × 5 connector pinout](assets/spi_nrf.png)

Viewed from the connector face as shown above, pin 1 is at the upper left and pin 2 at the upper right:

| Left contact | Function and CH552 signal | Right contact | Function and CH552 signal |
| --- | --- | --- | --- |
| 1 | SCK — P1.7 | 2 | GND |
| 3 | MISO — P1.6 | 4 | VCC |
| 5 | CE — P3.2 | 6 | CSN — P1.4 |
| 7 | IRQ — P3.1 | 8 | P3.0 activity output |
| 9 | MOSI — P1.5 | 10 | GND |

The six radio signals connect to the corresponding CE, CSN, SCK, MOSI, MISO, and IRQ contacts on the nRF24L01+ adapter. VCC and both GND contacts provide its power connections. The firmware pin definitions in [`src/config.h`](src/config.h) already match this mapping and use a 16 MHz internal clock. P3.0 is driven as an active-low activity output by the original firmware; it only controls an LED if one is connected to that contact.

The connector table and image above are the wiring reference for this example. With another connector layout, follow the CH552 signal names rather than these contact numbers; P1.5, P1.6, and P1.7 are the fixed SPI pins used by this firmware.

## Build

From the SDK root, build with the Docker based `spkg` tool:

```bash
./spkg/spkg -p ./examples/usb/usb_nrf/nrf2cdc bin
```

The output is `examples/usb/usb_nrf/nrf2cdc/build/main.bin`. You can also build with a locally installed SDCC toolchain:

```bash
make -C examples/usb/usb_nrf/nrf2cdc bin
```

Or use PlatformIO:

```bash
./spkg/spkg pio ./examples/usb/usb_nrf/nrf2cdc run
```

PlatformIO writes `firmware.bin` to `.pio/build/unit_ch552/` within this example.

## Upload and use

Put the CH552 into bootloader mode by holding **BOOT** while connecting USB. Then upload the binary with the included tool:

```bash
python3 examples/usb/usb_nrf/nrf2cdc/tools/chprog.py \
  examples/usb/usb_nrf/nrf2cdc/build/main.bin
```

`chprog.py` requires Python 3 and PyUSB. You can also run `make flash` from this example's directory, or use `./spkg/spkg pio ./examples/usb/usb_nrf/nrf2cdc run -t upload` with the SDK's configured uploader. The device must be in bootloader mode when uploading starts.

After flashing, open the USB CDC serial port. The serial monitor's baud rate does not affect the USB connection. Text sent to the port is transmitted over the radio, and received packets appear in the monitor. Both radios must use the same channel and data rate; one radio's TX address must match the other's RX address.

Commands start with `!`:

| Command | Effect |
| --- | --- |
| `!` | Show the current settings and `nRF SPI: OK` or `nRF SPI: NO RESPONSE`. |
| `!c2A` | Set channel `0x2A` (range `00` to `7F`). |
| `!t7B271F1F1F` | Set the five byte TX address, least significant byte first. |
| `!r41C355AA55` | Set the five byte RX address, least significant byte first. |
| `!s02` | Set data rate: `00` = 250 kb/s, `01` = 1 Mb/s, `02` = 2 Mb/s. |
| `!oADLx` | Enable `A` auto ACK, `D` dynamic payload length, and `L` line ending removal; disable `x` hexadecimal mode. Uppercase enables and lowercase disables each option. |

Configuration changes are stored in the CH552 data flash and survive a restart. See the [original README](https://github.com/wagiminator/CH552-USB-NRF#nrf-to-cdc) for more protocol details.

`nRF SPI: OK` means the CH552 can read the configured registers from the local nRF24L01+ module. It does not indicate that a second radio is connected. `nRF SPI: NO RESPONSE` indicates a missing module, a wiring or power problem, or a failed register readback. Transmission reports `TX failed: no RF ACK` when automatic acknowledgement is enabled and the other radio does not acknowledge the packet; a missing local module reports `nRF SPI: NO RESPONSE` instead. `TX timeout` means SPI still answers, but the radio did not signal completion within the bounded wait.

## Raspberry Pi Pico MicroPython radio peer

[`micropython_slave.py`](micropython_slave.py) is a radio peer for a Raspberry Pi Pico (RP2040) wired to a second nRF24L01+. It uses software SPI so SCK, MOSI, and MISO can use the GPIO numbers below. These are GPIO numbers, not physical header pin numbers. Power the nRF24L01+ from **3.3 V** and connect it to the Pico's GND.

| nRF24L01+ signal | Pico GPIO | Physical Pico pin |
| --- | ---: | ---: |
| CE | 28 | 34 |
| CSN | 27 | 32 |
| SCK | 26 | 31 |
| MOSI | 15 | 20 |
| MISO | 14 | 19 |
| IRQ | 8 | 11 |

Copy the script to the Pico as `main.py`. On the CH55x serial port, send `!` and confirm channel `02`, data rate `250kbps`, TX address `E7E7E7E7E7`, RX address `C2C2C2C2C2`, and `nRF SPI: OK`. If these were changed previously, restore them with `!c02`, `!s00`, `!tE7E7E7E7E7`, and `!rC2C2C2C2C2`. Then send `!oADLx` to enable auto ACK, dynamic payload length, and line ending removal, and to disable hexadecimal input mode. Dynamic payload length is needed for variable-length packets on both ends.

Send `!` again and confirm `Dynamic payload: OK`. The firmware reads back the nRF feature registers and attempts the `ACTIVATE` sequence on compatible modules that need it.

The Pico does not need a CDC connection for the radio link. The `print` calls are optional diagnostics. By default, the Pico only transmits when text is entered in its console or `send_to_ch552("temperature=25")` is called from application code; received messages are displayed as `RX:` without an automatic reply. Messages must be 1–32 bytes. For a temporary link test, set `BEACON_INTERVAL_MS = 5000` to send `PICO_READY` every five seconds, or set `AUTO_ECHO = True` to reply to each received packet with `echo:`. Both diagnostics are off by default.

If a MicroPython console is connected to the Pico, type a message there and press **Enter**. The script reads complete lines without blocking radio reception and sends them to the CH55x. For example, typing `hello from pico` on the Pico should display that text on the CH55x serial port. The Pico console reports `Sent to CH55x` when transmission succeeds. A payload longer than 32 bytes is rejected.

The Pico also has a local configuration menu, shown at startup and with `!h` or `!?`. Type `!` followed by **Enter** to display its settings, nRF SPI status, and feature register status. It uses the same command format as the CH552: `!cXX` for channel, `!tXXXXXXXXXX` for TX address, `!rXXXXXXXXXX` for RX address, `!sXX` for data rate, and `!oADLx` for options. `A/a` turns automatic acknowledgement on/off, `L/l` removes/adds the console newline to transmitted messages, and `X/x` turns hexadecimal console input on/off. `D` keeps dynamic payload enabled; `d` is rejected because this peer requires dynamic payload to receive variable-length packets. Changes are saved to `nrf_pico.json` on the Pico and loaded after a restart. `!!text` sends a message beginning with a literal `!`.

These commands configure the **Pico** when typed in its console and the **CH552** when typed in the CH552 USB CDC port. Configure channel and speed equally on both sides; each side's TX address must match the other side's RX address. For the defaults, use `!c02`, `!s00`, `!tC2C2C2C2C2`, `!rE7E7E7E7E7`, and `!oADLx` on the Pico. The CH552 uses the opposite TX/RX addresses as shown above.

Send `hello` to the CH55x serial port. The MicroPython console should print `RX: b'hello'`. Then enter `pico123` in the Pico console and confirm that it appears on the CH55x serial port; the Pico should print `Sent to CH55x: b'pico123'` when the packet is acknowledged. The CH55x's `nRF SPI: OK` status checks its local module only.

## Origin and licenses

- **Firmware:** Stefan Wagner, [CH552-USB-NRF](https://github.com/wagiminator/CH552-USB-NRF), revision `845308234d6c2fce05ce4d6ec156a478205986f8`. Licensed under **Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)**; see [`LICENSE`](LICENSE) and the [license text](https://creativecommons.org/licenses/by-sa/3.0/).
- **Functional connector pinout and image:** Supplied by the project contributor. The connector table records that diagram's contact numbers and signal mapping.
- **SDK adaptation:** César Bautista. The firmware was integrated as `main.c` and `src/`, with a project `Makefile`, `platformio.ini`, and this documentation. Subsequent changes reserve one extra byte for the command terminator, initialize the character used after an empty packet, reject invalid payload lengths before copying into the buffer, check local SPI register readback, and bound the transmit wait. These firmware changes are distributed under the same **CC BY-SA 3.0** license.
- **`tools/chprog.py`:** Stefan Wagner. This upload tool retains the **MIT** license stated in its header; see [`tools/LICENSE`](tools/LICENSE).

The SDK root's MIT license covers its own tools and structure. The firmware retains its CC BY-SA 3.0 license.
