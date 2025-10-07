# CMSIS-DAP

This repository contains firmware for **CH552G** microcontrollers. The implementation supports seamless operation on **Linux** and **Windows** without requiring proprietary drivers.

![programmer](../static/programmer.png)

| PIN | GPIO | Description |
|-----|------|------------ |
| LED | P11  | pin connected to LED, active low |
| RXD | P30  | pin connected to RXD via 470R resistor |
| TXD | P31  | pin connected to TXD via 470R resistor |
| SWD | P16  | pin connected to SWDIO/TMS via 100R resistor |
| SWK | P15  | pin connected to SWCLK/TCK via 100R resistor |
| RST | P17  | pin connected to nRESET |
| TDO | P14  | pin connected to TDO via 100R resistor |
| TDI | P33  | pin connected to TDI via 100R resistor |
| TRST| P32  | pin connected to nTRST |

