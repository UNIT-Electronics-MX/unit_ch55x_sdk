

# CH552 Docker SDK

> Portable SDK for CH552 firmware development using SDCC inside Docker containers. Includes a cross-platform CLI tool (`spkg`) to simplify builds on both Linux and Windows.

## Features

- Unified CLI tool: `spkg` for Linux, macOS, and Windows (via Git Bash)
- No need to install SDCC or toolchains manually
- Fully Dockerized environment for isolated builds
- Makefile-based project system compatible with CH552/CH55x
- Example project provided in `examples/`


## Requirements

### Common (All Platforms)

- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Linux/macOS

- Git
- Python 3
- Bash shell
- Superuser privileges required to run Docker

### Windows

- [Git Bash](https://gitforwindows.org/)
- Docker Desktop with WSL2 backend or Hyper-V enabled
- MinGW64 (included with Git Bash) for `make` command

> Note: Running `spkg` on Linux may require `sudo` if your user is not part of the `docker` group. You can add your user with:  
> `sudo usermod -aG docker $USER && newgrp docker`

## Installation

Clone the repository:

```bash
git clone git@github.com:UNIT-Electronics-MX/unit_ch55x_docker_sdk.git
cd ch552-docker-sdk/spkg
chmod +x spkg
```

(Optional) Install globally:

```bash
sudo ln -s "$(pwd)/spkg" /usr/local/bin/spkg
```

You can now run `spkg` from any location.

---

## Usage

### Show help

```bash
spkg --help
```

### Build a project

```bash
spkg -p ./examples/Blink
```

### Run `make clean`, `all`, `hex`, etc.

```bash
spkg -p ./examples/Blink clean
spkg -p ./examples/Blink all
spkg -p ./examples/Blink hex
```

### Build Docker image

```bash
spkg compose
```

---

## PlatformIO

This repository can also be used as a local PlatformIO development platform for
CH55x projects. PlatformIO will use SDCC, build `firmware.ihx`,
`firmware.hex`, and `firmware.bin`. Upload defaults to `auto`, which uses
`chprog.py` on Linux/macOS and `vnproch55x` on Windows.

### Build the PlatformIO example

```bash
cd examples/platformio-blink
pio run
```

The generated firmware files will be in:

```text
examples/platformio-blink/.pio/build/unit_ch552/
```

All examples under `examples/` include a `platformio.ini`, so they can be built
the same way:

```bash
cd examples/usb/usb_uart
pio run
```

### Upload

Put the CH55x in bootloader mode and run:

```bash
pio run -t upload
```

On Linux/macOS the default uploader is `chprog.py`, which requires PyUSB in
the PlatformIO Python environment:

```bash
~/.platformio/penv/bin/python -m pip install pyusb
```

On Linux, USB access may also require udev permissions:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="4348", ATTR{idProduct}=="55e0", MODE="666"' | sudo tee /etc/udev/rules.d/99-ch55x.rules
sudo udevadm control --reload-rules
```

If an older checkout fails while installing `tool-devlabtools` or tries to run
`git clone` against a `ch55xduino-tools_*.tar.bz2` URL, update this SDK to
version `v0.1.3` or newer. That archive is a Windows-only Arduino tools archive,
not a PlatformIO package, and Linux/macOS do not need it for the default
`chprog.py` uploader.

### Windows upload with Arduino `vnproch55x`

Arduino uses `vnproch55x.exe` from the `devlabtools` package to upload on
Windows. The default `upload_protocol = auto` selects it automatically on
Windows.

The current Arduino tools archive is not a PlatformIO package, so PlatformIO
cannot install it as a `platform.json` package. When `pio run -t upload` runs
on Windows, the SDK downloads that archive, extracts it into the SDK root, and
then runs `tools/win/vnproch55x.exe`.

If the automatic download is blocked, install it manually in the SDK root:

```powershell
cd C:\path\to\unit_ch55x_docker_sdk
Invoke-WebRequest "https://github.com/UNIT-Electronics/Uelectronics-CH552-Arduino-Package/releases/download/v0.0.6/ch55xduino-tools_mingw32-2026.06.21.tar.bz2" -OutFile "ch55xduino-tools_mingw32-2026.06.21.tar.bz2"
tar -xjf ch55xduino-tools_mingw32-2026.06.21.tar.bz2
Test-Path .\tools\win\vnproch55x.exe
```

The `Test-Path` command must print `True`. The extracted layout must contain:

```text
tools/win/vnproch55x.exe
tools/win/*.dll
```

The tools archive is published by the Arduino package release:

```text
https://github.com/UNIT-Electronics/Uelectronics-CH552-Arduino-Package/releases/download/v0.0.6/ch55xduino-tools_mingw32-2026.06.21.tar.bz2
```

After installing or automatically downloading the uploader, build and upload
from the PlatformIO project:

```powershell
C:\Users\<user>\.platformio\penv\Scripts\platformio.exe run
C:\Users\<user>\.platformio\penv\Scripts\platformio.exe run --target upload
```

The default PlatformIO configuration can stay the same:

```ini
[env:unit_ch552]
platform = ../..
board = unit_ch552

; Arduino defaults to bootcfg 3 for CH552 P3.6 (D+) pull-up.
board_upload.bootcfg = 3
```

You can still force a specific uploader when needed:

```ini
upload_protocol = chprog
upload_protocol = vnproch55x
```

For serial upload:

```ini
upload_protocol = vnproch55x_serial
upload_port = COM5
```

### Use the SDK as a local PlatformIO platform

In a PlatformIO project inside this repository, point `platform` to the SDK
root:

```ini
[env:unit_ch552]
platform = ../..
board = unit_ch552
```

To pin a released SDK version from GitHub, use the release tag in
`platformio.ini`:

```ini
[env:unit_ch552]
platform = https://github.com/UNIT-Electronics-MX/unit_ch55x_docker_sdk.git#v0.1.3
board = unit_ch552
```

For an existing Makefile-style example where `main.c` is at the project root,
set the source directory globally:

```ini
[platformio]
src_dir = .

[env:unit_ch552]
platform = ../..
board = unit_ch552
```

Available boards:

- `unit_ch551`
- `unit_ch552`
- `unit_ch554`
- `unit_ch559`

Common overrides:

```ini
board_build.f_cpu = 24000000
build_flags =
  -D PIN_LED=P34
```

---

### Create a New Project

To create a new project, use the `init` command:
> note: This command will create a new directory with the specified name.
```bash
 ./spkg/spkg init examples/project
 ```
## Output

The compiled binary will be generated at:

```
examples/Blink/build/main.bin
```

You can flash it using:

- `tools/chprog.py`
- [wchusbdfu](https://github.com/DeqingSun/ch554tools)
- [WCHISPTool](https://www.wch-ic.com/downloads/WCHISPTool_Setup_exe.html)

---

## Project Structure

```
ch552-docker-sdk/
├── spkg/                   # Self-contained CLI build system
│   ├── spkg                # CLI launcher (bash script)
│   ├── Dockerfile          # SDCC-based build environment
│   └── docker-compose.yml  # Container configuration
├── examples/               # Example CH552 projects
│   └── Blink/              # Blink example (main.c, src/, tools/, Makefile)
└── README.md
```

---
## License

This SDK is released under the [MIT License](LICENSE).

You may freely use, modify, and distribute the SDK framework and tools (`spkg`, `compilar.sh`, etc.) under the terms of the MIT license.

### Notes on Example Projects

Some example projects inside the `examples/` directory are derived from the work of Stefan Wagner:  
[https://github.com/wagiminator/Development-Boards](https://github.com/wagiminator/CH552-USB-CDC-OLED-Terminal)

These files are licensed under the  
**Creative Commons Attribution-ShareAlike 3.0 Unported License (CC BY-SA 3.0)**.

Each source file includes a license header stating its origin and terms of use.

You must credit the original author and distribute modifications under the same license.  
See the full license at: [http://creativecommons.org/licenses/by-sa/3.0/](http://creativecommons.org/licenses/by-sa/3.0/)
