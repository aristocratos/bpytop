# ![bpytop](https://github.com/aristocratos/bpytop/raw/master/Imgs/logo.png)

![Linux](https://img.shields.io/badge/-Linux-grey?logo=linux)
![OSX](https://img.shields.io/badge/-OSX-black?logo=apple)
![FreeBSD](https://img.shields.io/badge/-FreeBSD-red?logo=freebsd)
![Usage](https://img.shields.io/badge/Usage-System%20resource%20monitor-yellow)
![Python](https://img.shields.io/badge/Python-v3.6%5E-green?logo=python)
![bpytop_version](https://img.shields.io/github/v/tag/aristocratos/bpytop?label=version)
[![pypi_version](https://img.shields.io/pypi/v/bpytop?label=pypi)](https://pypi.org/project/bpytop)
[![Donate](https://img.shields.io/badge/-Donate-yellow?logo=paypal)](https://paypal.me/aristocratos)
[![Sponsor](https://img.shields.io/badge/-Sponsor-red?logo=github)](https://github.com/sponsors/aristocratos)
[![Coffee](https://img.shields.io/badge/-Buy%20me%20a%20Coffee-grey?logo=Ko-fi)](https://ko-fi.com/aristocratos)

## Index

* [Documents](#documents)
* [Description](#description)
* [Features](#features)
* [Themes](#themes)
* [Support and funding](#support-and-funding)
* [Prerequisites](#prerequisites)
* [Dependencies](#dependencies)
* [Screenshots](#screenshots)
* [Installation](#installation)
* [Configurability](#configurability)
* [TODO](#todo)
* [License](#license)

## Documents

#### [CHANGELOG.md](https://github.com/aristocratos/bpytop/blob/master/CHANGELOG.md)

#### [CONTRIBUTING.md](https://github.com/aristocratos/bpytop/blob/master/CONTRIBUTING.md)

#### [CODE_OF_CONDUCT.md](https://github.com/aristocratos/bpytop/blob/master/CODE_OF_CONDUCT.md)

## Description

Resource monitor that shows usage and stats for processor, memory, disks, network and processes.

Python port of [bashtop](https://github.com/aristocratos/bashtop).

## Features

* Easy to use, with a game inspired menu system.
* Full mouse support, all buttons with a highlighted key is clickable and mouse scroll works in process list and menu boxes.
* Fast and responsive UI with UP, DOWN keys process selection.
* Function for showing detailed stats for selected process.
* Ability to filter processes, multiple filters can be entered.
* Easy switching between sorting options.
* Send SIGTERM, SIGKILL, SIGINT to selected process.
* UI menu for changing all config file options.
* Auto scaling graph for network usage.
* Shows message in menu if new version is available
* Shows current read and write speeds for disks

## Themes

Bpytop uses the same theme files as bashtop so any theme made for bashtop will work.

See [themes](https://github.com/aristocratos/bpytop/tree/master/themes) folder for available themes.

The `make install` command places the default themes in `/usr/local/share/bpytop/themes`.
If installed with `pip3` the themes will be located in a folder called `bpytop-themes` in the python3 site-packages folder.
User created themes should be placed in `$HOME/.config/bpytop/themes`.

Let me know if you want to contribute with new themes.

## Support and funding

You can sponsor this project through github, see [my sponsors page](https://github.com/sponsors/aristocratos) for options.

Or donate through [paypal](https://paypal.me/aristocratos) or [ko-fi](https://ko-fi.com/aristocratos).

Any support is greatly appreciated!

## Prerequisites

#### Mac Os X

Will not display correctly in the standard terminal!
Recommended alternative [iTerm2](https://www.iterm2.com/)

Will also need to be run as superuser to display stats for processes not owned by user.

#### Linux, Mac Os X and FreeBSD

For correct display, a terminal with support for:

* 24-bit truecolor ([See list of terminals with truecolor support](https://gist.github.com/XVilka/8346728))
* Wide characters (Are sometimes problematic in web-based terminals)

Also needs a UTF8 locale and a font that covers:

* Unicode Block “Braille Patterns” U+2800 - U+28FF
* Unicode Block “Geometric Shapes” U+25A0 - U+25FF
* Unicode Block "Box Drawing" and "Block Elements" U+2500 - U+259F

#### Notice

Dropbear seems to not be able to set correct locale. So if accessing bpytop over ssh, OpenSSH is recommended.

## Dependencies

**[Python3](https://www.python.org/downloads/)** (v3.6 or later)

**[psutil module](https://github.com/giampaolo/psutil)** (v5.7.0 or later)

## Optionals for additional stats

(Optional OSX) **[osx-cpu-temp](https://github.com/lavoiesl/osx-cpu-temp)** Needed to show CPU temperatures.

## Screenshots

Main UI showing details for a selected process.
![Screenshot 1](https://github.com/aristocratos/bpytop/raw/master/Imgs/main.png)

Main UI in mini mode.
![Screenshot 2](https://github.com/aristocratos/bpytop/raw/master/Imgs/mini.png)

Main menu.
![Screenshot 3](https://github.com/aristocratos/bpytop/raw/master/Imgs/menu.png)

Options menu.
![Screenshot 4](https://github.com/aristocratos/bpytop/raw/master/Imgs/options.png)

## Installation

### PyPi (will always have latest version)

> Install or update to latest version
``` bash
pip3 install bpytop --upgrade
```

### Arch Linux

Available in the AUR as `bpytop`

https://aur.archlinux.org/packages/bpytop/

### Debian based

Available for debian/ubuntu from [Azlux's repository](http://packages.azlux.fr/)

### FreeBSD package

Available in [FreeBSD ports](https://www.freshports.org/sysutils/bpytop/)

>Install pre-built package

``` bash
sudo pkg install bpytop
```

### Fedora/CentOS 8 package

[Available](https://src.fedoraproject.org/rpms/bpytop) in the Fedora and [EPEL-8 repository](https://fedoraproject.org/wiki/EPEL).

>Installation

``` bash
sudo dnf install bpytop
```

### Snap package

by @kz6fittycent

https://github.com/kz6fittycent/bpytop-snap

>Install the package
``` bash
sudo snap install bpytop
```

>Give permissions
``` bash
sudo snap connect bpytop:mount-observe
sudo snap connect bpytop:network-control
sudo snap connect bpytop:hardware-observe
sudo snap connect bpytop:system-observe
sudo snap connect bpytop:process-control
sudo snap connect bpytop:physical-memory-observe
```

The config folder will be located in `~/snap/bpytop/current/.config/bpytop`

## Manual installation

#### Dependencies installation Linux

>Install python3 and git with a package manager of you choice

>Install psutil python module (sudo might be required)

``` bash
python3 -m pip install psutil
```

#### Dependencies installation OSX

>Install homebrew if not already installed

``` bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
```

>Install python3 if not already installed

``` bash
brew install python3 git
```

>Install psutil python module

``` bash
python3 -m pip install psutil
```

>Install optional dependency osx-cpu-temp

``` bash
brew install osx-cpu-temp
```

#### Dependencies installation FreeBSD

>Install with pkg and pip

``` bash
sudo pkg install git python3 py37-psutil
```

#### Manual installation Linux, OSX and FreeBSD

>Clone and install

``` bash
git clone https://github.com/aristocratos/bpytop.git
cd bpytop
sudo make install
```

>to uninstall it

``` bash
sudo make uninstall
```

## Configurability

All options changeable from within UI.
Config files stored in "$HOME/.config/bpytop" folder

#### bpytop.cfg: (auto generated if not found)

"/etc/bpytop.conf" will be used as default seed for config file creation if it exists.

```bash
#? Config file for bpytop v. 1.0.22

#* Color theme, looks for a .theme file in "/usr/[local/]share/bpytop/themes" and "~/.config/bpytop/themes", "Default" for builtin default theme.
#* Prefix name by a plus sign (+) for a theme located in user themes folder, i.e. color_theme="+monokai"
color_theme="Default"

#* If the theme set background should be shown, set to False if you want terminal background transparency
theme_background=False

#* Set bpytop view mode, "full" for everything shown, "proc" for cpu stats and processes, "stat" for cpu, mem, disks and net stats shown.
view_mode=full

#* Update time in milliseconds, increases automatically if set below internal loops processing time, recommended 2000 ms or above for better sample times for graphs.
update_ms=2000

#* Processes sorting, "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive",
#* "cpu lazy" updates top process over time, "cpu responsive" updates top process directly.
proc_sorting="cpu lazy"

#* Reverse sorting order, True or False.
proc_reversed=False

#* Show processes as a tree
proc_tree=False

#* Use the cpu graph colors in the process list.
proc_colors=True

#* Use a darkening gradient in the process list.
proc_gradient=True

#* If process cpu usage should be of the core it's running on or usage of the total available cpu power.
proc_per_core=True

#* Show process memory as bytes instead of percent
proc_mem_bytes=True

#* Check cpu temperature, needs "osx-cpu-temp" on MacOS X.
check_temp=True

#* Draw a clock at top of screen, formatting according to strftime, empty string to disable.
draw_clock="%X"

#* Update main ui in background when menus are showing, set this to false if the menus is flickering too much for comfort.
background_update=True

#* Custom cpu model name, empty string to disable.
custom_cpu_name=""

#* Optional filter for shown disks, should be last folder in path of a mountpoint, "root" replaces "/", separate multiple values with comma.
#* Begin line with "exclude=" to change to exclude filter, oterwise defaults to "most include" filter. Example: disks_filter="exclude=boot, home"
disks_filter=""

#* Show graphs instead of meters for memory values.
mem_graphs=True

#* If swap memory should be shown in memory box.
show_swap=True

#* Show swap as a disk, ignores show_swap value above, inserts itself after first disk.
swap_disk=True

#* If mem box should be split to also show disks info.
show_disks=True

#* Set fixed values for network graphs, default "10M" = 10 Mibibytes, possible units "K", "M", "G", append with "bit" for bits instead of bytes, i.e "100mbit"
net_download="100Mbit"
net_upload="100Mbit"

#* Start in network graphs auto rescaling mode, ignores any values set above and rescales down to 10 Kibibytes at the lowest.
net_auto=True

#* Sync the scaling for download and upload to whichever currently has the highest scale
net_sync=False

#* If the network graphs color gradient should scale to bandwith usage or auto scale, bandwith usage is based on "net_download" and "net_upload" values
net_color_fixed=False

#* Show init screen at startup, the init screen is purely cosmetical
show_init=False

#* Enable check for new version from github.com/aristocratos/bpytop at start.
update_check=True

#* Set loglevel for "~/.config/bpytop/error.log" levels are: "ERROR" "WARNING" "INFO" "DEBUG".
#* The level set includes all lower levels, i.e. "DEBUG" will show all logging info.
log_level=WARNING

```

#### Command line options:

``` text
USAGE: bpytop [argument]

Arguments:
    -f, --full            Start in full mode showing all boxes [default]
    -p, --proc            Start in minimal mode without memory and net boxes
    -s, --stat            Start in minimal mode without process box
    -v, --version         Show version info and exit
    -h, --help            Show this help message and exit
    --debug               Start with loglevel set to DEBUG overriding value set in config
```

## TODO

- [ ] Add gpu temp and usage.
- [ ] Add cpu and mem stats for docker containers. (If feasible)
- [x] Change process list to line scroll instead of page change.
- [ ] Add options for resizing all boxes.
- [x] Add command line argument parsing.

- [ ] Miscellaneous optimizations and code cleanup.


## LICENSE

[Apache License 2.0](https://github.com/aristocratos/bpytop/blob/master/LICENSE)
