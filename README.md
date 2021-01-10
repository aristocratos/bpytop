# ![bpytop](https://github.com/aristocratos/bpytop/raw/master/Imgs/logo.png)

<a href="https://repology.org/project/bpytop/versions">
    <img src="https://repology.org/badge/vertical-allrepos/bpytop.svg" alt="Packaging status" align="right">
</a>

![Linux](https://img.shields.io/badge/-Linux-grey?logo=linux)
![OSX](https://img.shields.io/badge/-OSX-black?logo=apple)
![FreeBSD](https://img.shields.io/badge/-FreeBSD-red?logo=freebsd)
![Usage](https://img.shields.io/badge/Usage-System%20resource%20monitor-yellow)
![Python](https://img.shields.io/badge/Python-v3.7%5E-green?logo=python)
![bpytop_version](https://img.shields.io/github/v/tag/aristocratos/bpytop?label=version)
[![pypi_version](https://img.shields.io/pypi/v/bpytop?label=pypi)](https://pypi.org/project/bpytop)
[![Test Status](https://img.shields.io/github/workflow/status/aristocratos/bpytop/Testing?label=tests)](https://github.com/aristocratos/bpytop/actions?query=workflow%3Atesting)
[![Donate](https://img.shields.io/badge/-Donate-yellow?logo=paypal)](https://paypal.me/aristocratos)
[![Sponsor](https://img.shields.io/badge/-Sponsor-red?logo=github)](https://github.com/sponsors/aristocratos)
[![Coffee](https://img.shields.io/badge/-Buy%20me%20a%20Coffee-grey?logo=Ko-fi)](https://ko-fi.com/aristocratos)

[![bpytop](https://img.shields.io/badge/-snapcraft.io-black)](https://snapcraft.io/bpytop)[![bpytop](https://snapcraft.io//bpytop/badge.svg)](https://snapcraft.io/bpytop)

## Index

* [Documents](#documents)
* [Description](#description)
* [Features](#features)
* [Themes](#themes)
* [Support and funding](#support-and-funding)
* [Prerequisites](#prerequisites) (Read this if you are having issues!)
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

Will not display correctly in the standard terminal (unless truecolor is set to False)!
Recommended alternative [iTerm2](https://www.iterm2.com/)

Will also need to be run as superuser to display stats for processes not owned by user.

OsX on Apple Silicon (arm) requires psutil version 5.8.0 to work and currently has no temperature monitoring.
Upgrade psutil with `sudo pip3 install psutil --upgrade`

#### Linux, Mac Os X and FreeBSD

For correct display, a terminal with support for:

* 24-bit truecolor ([See list of terminals with truecolor support](https://gist.github.com/XVilka/8346728))
* 256-color terminals are supported through 24-bit to 256-color conversion when setting "truecolor" to False in the options or with "-lc/--low-color" argument.
* Wide characters (Are sometimes problematic in web-based terminals)

Also needs a UTF8 locale and a font that covers:

* Unicode Block “Braille Patterns” U+2800 - U+28FF
* Unicode Block “Geometric Shapes” U+25A0 - U+25FF
* Unicode Block "Box Drawing" and "Block Elements" U+2500 - U+259F

#### Notice (Text rendering issues)

If you are having problems with the characters in the graphs not looking like they do in the screenshots,
it's likely a problem with your systems configured fallback font not having support for braille characters.

See [Terminess Powerline](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/Terminus/terminus-ttf-4.40.1) for an example of a font that includes the braille symbols.

See comments by @sgleizes [link](https://github.com/aristocratos/bpytop/issues/100#issuecomment-684036827) and @XenHat [link](https://github.com/aristocratos/bpytop/issues/100#issuecomment-691585587) in issue #100 for possible solutions.

If text are misaligned and you are using Konsole or Yakuake, turning off "Bi-Directional text rendering" is a possible fix.

Characters clipping in to each other or text/border misalignments is not bugs caused by bpytop, but most likely a fontconfig or terminal problem where the braille characters making up the graphs aren't rendered correctly.
Look to the creators of the terminal emulator you use to fix these issues if the previous mentioned fixes don't work for you.

#### Notice (SSH)

Dropbear seems to not be able to set correct locale. So if accessing bpytop over ssh, OpenSSH is recommended.

## Dependencies

**[Python3](https://www.python.org/downloads/)** (v3.7 or later)

**[psutil module](https://github.com/giampaolo/psutil)** (v5.7.0 or later)

## Optionals for additional stats

(Optional OSX) **[coretemp](https://github.com/hacker1024/coretemp)** (recommended), or **[osx-cpu-temp](https://github.com/lavoiesl/osx-cpu-temp)** (less accurate) needed to show CPU temperatures.

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

### Mac OsX

>Install with Homebrew
```bash
brew install bpytop
```

>Optional coretemp (Shows temperatures for cpu cores)
```bash
brew install hacker1024/hacker1024/coretemp
```

>Alternatively install with MacPorts
```bash
port install bpytop
```

OsX on Apple Silicon (arm) requires psutil version 5.8.0 to work and currently has no temperature monitoring.
Upgrade psutil with `sudo pip3 install psutil --upgrade`

### Arch Linux

Available in the Arch Linux [community] repository as `bpytop`

>Installation

```bash
sudo pacman -S bpytop
```

### Debian based

Available in [official Debian repository](https://tracker.debian.org/pkg/bpytop) since Debian 11

>Installation

```bash
sudo apt install bpytop
```

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

### Gentoo / Calculate Linux

Available from [adrien-overlay](https://github.com/aaaaadrien/adrien-overlay)

>Installation

``` bash
sudo emerge -av sys-process/bpytop
```

### Mageia Cauldron (Mageia 8)

Available in Mageia Cauldron and then Mageia 8 when it is released.

>Installation

``` bash
sudo urpmi bpytop
sudo dnf install bpytop
```

### MX Linux

Available in the MX Test Repo as `bpytop`
Please use MX Package Installer MX Test Repo tab to install.

http://mxrepo.com/mx/testrepo/pool/test/b/bpytop/

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

>Install optional dependency coretemp (recommended), or osx-cpu-temp (less accurate)

``` bash
brew install hacker1024/hacker1024/coretemp
```

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
#? Config file for bpytop v. 1.0.58

#* Color theme, looks for a .theme file in "/usr/[local/]share/bpytop/themes" and "~/.config/bpytop/themes", "Default" for builtin default theme.
#* Prefix name by a plus sign (+) for a theme located in user themes folder, i.e. color_theme="+monokai"
color_theme="monokai"

#* If the theme set background should be shown, set to False if you want terminal background transparency
theme_background=False

#* Sets if 24-bit truecolor should be used, will convert 24-bit colors to 256 color (6x6x6 color cube) if false.
truecolor=True

#* Manually set which boxes to show. Available values are "cpu mem net proc", seperate values with whitespace.
shown_boxes="cpu mem net proc"

#* Update time in milliseconds, increases automatically if set below internal loops processing time, recommended 2000 ms or above for better sample times for graphs.
update_ms=2000

#* Processes update multiplier, sets how often the process list is updated as a multiplier of "update_ms".
#* Set to 2 or higher to greatly decrease bpytop cpu usage. (Only integers)
proc_update_mult=2

#* Processes sorting, "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive",
#* "cpu lazy" updates top process over time, "cpu responsive" updates top process directly.
proc_sorting="cpu lazy"

#* Reverse sorting order, True or False.
proc_reversed=False

#* Show processes as a tree
proc_tree=False

#* Which depth the tree view should auto collapse processes at
tree_depth=3

#* Use the cpu graph colors in the process list.
proc_colors=True

#* Use a darkening gradient in the process list.
proc_gradient=True

#* If process cpu usage should be of the core it's running on or usage of the total available cpu power.
proc_per_core=False

#* Show process memory as bytes instead of percent
proc_mem_bytes=True

#* Check cpu temperature, needs "osx-cpu-temp" on MacOS X.
check_temp=True

#* Which sensor to use for cpu temperature, use options menu to select from list of available sensors.
cpu_sensor=Auto

#* Show temperatures for cpu cores also if check_temp is True and sensors has been found
show_coretemp=True

#* Draw a clock at top of screen, formatting according to strftime, empty string to disable.
draw_clock="%H:%M"

#* Update main ui in background when menus are showing, set this to false if the menus is flickering too much for comfort.
background_update=True

#* Custom cpu model name, empty string to disable.
custom_cpu_name=""

#* Optional filter for shown disks, should be full path of a mountpoint, separate multiple values with a comma ",".
#* Begin line with "exclude=" to change to exclude filter, oterwise defaults to "most include" filter. Example: disks_filter="exclude=/boot, /home/user"
disks_filter="exclude=/boot"

#* Show graphs instead of meters for memory values.
mem_graphs=True

#* If swap memory should be shown in memory box.
show_swap=True

#* Show swap as a disk, ignores show_swap value above, inserts itself after first disk.
swap_disk=True

#* If mem box should be split to also show disks info.
show_disks=True

#* Filter out non physical disks. Set this to False to include network disks, RAM disks and similar.
only_physical=True

#* Read disks list from /etc/fstab. This also disables only_physical.
use_fstab=True

#* Toggles io mode for disks, showing only big graphs for disk read/write speeds.
io_mode=False

#* Set to True to show combined read/write io graphs in io mode.
io_graph_combined=False

#* Set the top speed for the io graphs in MiB/s (10 by default), use format "device:speed" seperate disks with a comma ",".
#* Example: "/dev/sda:100, /dev/sdb:20"
io_graph_speeds=""

#* Set fixed values for network graphs, default "10M" = 10 Mibibytes, possible units "K", "M", "G", append with "bit" for bits instead of bytes, i.e "100mbit"
net_download="100Mbit"
net_upload="100Mbit"

#* Start in network graphs auto rescaling mode, ignores any values set above and rescales down to 10 Kibibytes at the lowest.
net_auto=True

#* Sync the scaling for download and upload to whichever currently has the highest scale
net_sync=True

#* If the network graphs color gradient should scale to bandwith usage or auto scale, bandwith usage is based on "net_download" and "net_upload" values
net_color_fixed=False

#* Starts with the Network Interface specified here.
net_iface=""

#* Show battery stats in top right if battery is present
show_battery=True

#* Show init screen at startup, the init screen is purely cosmetical
show_init=False

#* Enable check for new version from github.com/aristocratos/bpytop at start.
update_check=True

#* Set loglevel for "~/.config/bpytop/error.log" levels are: "ERROR" "WARNING" "INFO" "DEBUG".
#* The level set includes all lower levels, i.e. "DEBUG" will show all logging info.
log_level=DEBUG

```

#### Command line options:

``` text
usage: bpytop.py [-h] [-b BOXES] [-lc] [-v] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  -b BOXES, --boxes BOXES
                        which boxes to show at start, example: -b "cpu mem net proc"
  -lc, --low-color      disable truecolor, converts 24-bit colors to 256-color
  -v, --version         show version info and exit
  --debug               start with loglevel set to DEBUG overriding value set in config
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
