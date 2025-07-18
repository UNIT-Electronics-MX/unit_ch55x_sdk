
# CH552 USB Multi-Protocol Programmer

**Supports AVR / ARM (CMSIS-DAP) / CPLD (MAX II)**

| Component         | Description                      |
| ----------------- | -------------------------------- |
| Microcontroller   | CH552G / CH552E                  |
| USB Interface     | Full-Speed (CDC / HID)           |
| Target Voltage    | Selectable 3.3 V / 5 V           |
| Firmware Profiles | Configurable per target/protocol |
| Programming       | Via USB bootloader (CH55x)       |

---

## Supported Firmware Profiles

### AVR Programmer

| Feature   | Details                  |
| --------- | ------------------------ |
| Protocols | USBasp, UPDI (serial)    |
| Targets   | ATmega, ATtiny           |
| Tools     | `avrdude`                |
| USB Mode  | HID (USBasp), CDC (UPDI) |

---

### CMSIS-DAP Debugger (picoDAP)

| Feature  | Details                           |
| -------- | --------------------------------- |
| Protocol | SWD (CMSIS-DAP)                   |
| Targets  | ARM Cortex-M (STM32, nRF52, etc.) |
| Tools    | OpenOCD, PyOCD                    |
| USB Mode | HID with optional CDC UART        |

---

### CPLD Programmer (USB-Blaster)

| Feature      | Details                                     |
| ------------ | ------------------------------------------- |
| Targets      | Intel MAX II (e.g., EPM240)                 |
| Protocol     | JTAG (USB-Blaster emulation)                |
| Tools        | Intel Quartus Programmer                    |
| USB VID\:PID | `16C0:05DC` (default), `09FB:6001` (compat) |
| Voltage      | 3.3 V / 5 V (hardware switch)               |

---

## Toolchain

| Requirement      | Usage                    |
| ---------------- | ------------------------ |
| SDCC             | Firmware compilation     |
| Python 3 + pyusb | USB flashing             |
| chprog.py        | Upload binary to CH552   |
| WCHISPTool       | Windows flashing utility |

---

## Bootloader Access (CH552)

| Step | Action                         |
| ---- | ------------------------------ |
| 1    | Disconnect power               |
| 2    | Hold the BOOT button           |
| 3    | Connect USB while holding BOOT |
| 4    | Release button                 |

**udev rule for Linux (optional):**

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="4348", ATTR{idProduct}=="55e0", MODE="666"' \
| sudo tee /etc/udev/rules.d/99-ch55x.rules
sudo udevadm control --reload && sudo udevadm trigger
```

---

## Firmware Feature Matrix

| Firmware        | Protocols     | Target Devices        | USB Interface | Compatible Tools   |
| --------------- | ------------- | --------------------- | ------------- | ------------------ |
| AVR Programmer  | USBasp / UPDI | ATmega, ATtiny        | HID / CDC     | `avrdude`          |
| CMSIS-DAP       | SWD           | ARM Cortex-M          | HID + CDC     | OpenOCD, PyOCD     |
| CPLD Programmer | JTAG          | MAX II (e.g., EPM240) | HID           | Quartus Programmer |

---

## License

This project is licensed under the [Creative Commons Attribution-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-sa/3.0/).

![license.png](https://i.creativecommons.org/l/by-sa/3.0/88x31.png)
