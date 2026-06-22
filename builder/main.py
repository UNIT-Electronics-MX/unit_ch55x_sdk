from os import listdir, walk
from os.path import abspath, basename, dirname, exists, join, splitext

from SCons.Script import AlwaysBuild, Builder, Default, DefaultEnvironment


env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
SDK_DIR = dirname(dirname(abspath(env.subst("$BUILD_SCRIPT"))))


def _board_value(name, default):
    return str(board.get("build.%s" % name, default)).rstrip("L")


def _prepend_toolchain_path():
    package_dir = platform.get_package_dir("toolchain-sdcc")
    if package_dir:
        env.PrependENVPath("PATH", join(package_dir, "bin"))


def _copy_hex(target, source, env):
    with open(str(source[0]), "r") as src:
        data = src.read()
    with open(str(target[0]), "w") as dst:
        dst.write(data)


def _parse_ihx_record(line):
    if not line.startswith(":"):
        raise ValueError("invalid IHX record: %s" % line)
    count = int(line[1:3], 16)
    address = int(line[3:7], 16)
    record_type = int(line[7:9], 16)
    data = bytes(int(line[index:index + 2], 16) for index in range(9, 9 + count * 2, 2))
    return count, address, record_type, data


def _ihx_to_bin(target, source, env):
    memory = {}
    upper = 0

    with open(str(source[0]), "r") as ihx:
        for raw_line in ihx:
            line = raw_line.strip()
            if not line:
                continue
            count, address, record_type, data = _parse_ihx_record(line)
            if record_type == 0x00:
                base = upper + address
                for offset in range(count):
                    memory[base + offset] = data[offset]
            elif record_type == 0x01:
                break
            elif record_type == 0x04:
                upper = int.from_bytes(data, "big") << 16

    if not memory:
        open(str(target[0]), "wb").close()
        return

    image = bytearray(max(memory) + 1)
    for address, value in memory.items():
        image[address] = value

    with open(str(target[0]), "wb") as binary:
        binary.write(image)


def _print_size(target, source, env):
    mem_path = str(source[0]).rsplit(".", 1)[0] + ".mem"
    flash = iram = xram = "unknown"

    if exists(mem_path):
        with open(mem_path, "r") as mem_file:
            for line in mem_file:
                parts = line.split()
                if not parts:
                    continue
                if parts[0] == "ROM/EPROM/FLASH" and len(parts) >= 4:
                    flash = parts[3]
                elif parts[0] == "Stack" and len(parts) >= 10:
                    try:
                        iram = str(248 - int(parts[9], 0))
                    except ValueError:
                        iram = "unknown"
                elif parts[0] == "EXTERNAL" and len(parts) >= 5:
                    try:
                        xram = str(int(_board_value("xram_loc", "0x0100"), 0) + int(parts[4], 0))
                    except ValueError:
                        xram = "unknown"

    print("------------------")
    print("FLASH: %s bytes" % flash)
    print("IRAM:  %s bytes" % iram)
    print("XRAM:  %s bytes" % xram)
    print("------------------")


def _get_uploader():
    project_uploader = join("$PROJECT_DIR", "tools", "chprog.py")
    platform_uploader = join(SDK_DIR, "template", "tools", "chprog.py")
    return project_uploader if exists(env.subst(project_uploader)) else platform_uploader


def _host_tool_dir():
    if env["PLATFORM"] == "win32":
        return "win", "vnproch55x.exe"
    if env["PLATFORM"] == "darwin":
        return "macosx", "vnproch55x"
    return "linux", "vnproch55x"


def _get_vnproch55x():
    tool_dir, executable = _host_tool_dir()
    package_names = ("tool-devlabtools", "devlabtools", "tool-vnproch55x")
    package_dirs = []
    for name in package_names:
        try:
            package_dir = platform.get_package_dir(name)
        except KeyError:
            package_dir = None
        if package_dir:
            package_dirs.append(package_dir)

    candidates = []
    for package_dir in package_dirs:
        candidates.extend([
            join(package_dir, "tools", tool_dir, executable),
            join(package_dir, tool_dir, executable),
            join(package_dir, executable),
        ])

    candidates.extend([
        join("$PROJECT_DIR", "tools", tool_dir, executable),
        join(SDK_DIR, "tools", tool_dir, executable),
    ])

    for candidate in candidates:
        resolved = env.subst(candidate)
        if exists(resolved):
            return candidate

    return executable


def _resolve_upload_protocol(upload_protocol):
    if upload_protocol != "auto":
        return upload_protocol
    if env["PLATFORM"] == "win32":
        return "vnproch55x"
    return "chprog"


def _sdk_sources():
    sdk_dir = join(SDK_DIR, "template", "src")
    project_src_dir = env.subst("$PROJECT_SRC_DIR")
    project_sources = set()

    for root, _, files in walk(project_src_dir):
        for filename in files:
            if filename.endswith(".c"):
                project_sources.add(filename)

    if "oled_term.c" in project_sources:
        project_sources.add("oled.c")

    return [
        join(sdk_dir, filename)
        for filename in listdir(sdk_dir)
        if filename.endswith(".c") and filename not in project_sources
    ]


_prepend_toolchain_path()

env.Replace(
    AR="sdar",
    AS="sdas8051",
    CC="sdcc",
    CXX="sdcc",
    LINK="sdcc",
    OBJCOPY="sdobjcopy",
    RANLIB="sdranlib",
    OBJSUFFIX=".rel",
    PROGNAME="firmware",
    PROGSUFFIX=".ihx",
    SIZEPRINTCMD="$PYTHONEXE $SIZETOOL $SOURCES",
)

if not env.get("SRC_FILTER"):
    env.Replace(SRC_FILTER=["+<*>", "-<.git/>", "-<.svn/>", "-<build/>", "-<.pio/>"])

common_flags = [
    "-mmcs51",
    "--model-small",
    "--no-xinit-opt",
    "--xram-size",
    _board_value("xram_size", "0x0300"),
    "--xram-loc",
    _board_value("xram_loc", "0x0100"),
    "--code-size",
    _board_value("code_size", "0x3800"),
]

env.Append(
    CPPDEFINES=[
        "F_CPU=%s" % _board_value("f_cpu", "16000000"),
        "MCU_%s" % _board_value("mcu", "ch552").upper(),
    ],
    CPPPATH=[
        join("$PROJECT_DIR", "src"),
        join("$PROJECT_DIR", "include"),
        "$PROJECT_DIR",
        join(SDK_DIR, "template", "src"),
    ],
    CFLAGS=common_flags,
    LINKFLAGS=common_flags,
    BUILDERS=dict(
        IhxToHex=Builder(action=_copy_hex, suffix=".hex"),
        IhxToBin=Builder(action=_ihx_to_bin, suffix=".bin"),
        PrintCh55xSize=Builder(action=_print_size),
    ),
)

env.Replace(
    CCCOM="$CC -c $CFLAGS $CCFLAGS $_CCCOMCOM -o $TARGET $SOURCE",
    LINKCOM="$LINK $SOURCES $LINKFLAGS -o $TARGET",
)

sdk_objects = [
    obj
    for source in _sdk_sources()
    for obj in env.Object(join("$BUILD_DIR", "unit_ch55x_sdk", splitext(basename(source))[0]), source)
]
env.Append(LINKFLAGS=sdk_objects)

target_ihx = env.BuildProgram()
env.Depends(target_ihx, sdk_objects)
target_hex = env.IhxToHex(join("$BUILD_DIR", "${PROGNAME}"), target_ihx)
target_bin = env.IhxToBin(join("$BUILD_DIR", "${PROGNAME}"), target_ihx)

size = env.Alias("size", target_ihx, env.PrintCh55xSize(join("$BUILD_DIR", "size"), target_ihx))
AlwaysBuild(size)

env.Replace(
    UPLOADER=_get_uploader(),
    UPLOADCMD='"$PYTHONEXE" "$UPLOADER" "$SOURCE"',
)

upload_protocol = _resolve_upload_protocol(env.subst("$UPLOAD_PROTOCOL"))
if upload_protocol in ("vnproch55x", "vnproch55x_usb"):
    env.Replace(
        UPLOADER=_get_vnproch55x(),
        UPLOADERFLAGS=[
            "-r", "2",
            "-t", _board_value("mcu", "ch552").upper(),
            "-c", str(board.get("upload.bootcfg", "3")),
        ],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS "$SOURCE"',
    )
    upload_source = target_hex
elif upload_protocol == "vnproch55x_serial":
    env.Replace(
        UPLOADER=_get_vnproch55x(),
        UPLOADERFLAGS=[
            "-s", "$UPLOAD_PORT",
            "-t", _board_value("mcu", "ch552").upper(),
        ],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS "$SOURCE"',
    )
    upload_source = target_hex
else:
    upload_source = target_bin

upload = env.Alias("upload", upload_source, env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE"))
AlwaysBuild(upload)

AlwaysBuild(env.Alias("buildprog", [target_ihx, target_hex, target_bin]))
Default([target_ihx, target_hex, target_bin, size])
