# ![bpytop](Imgs/logo.png)

![Linux](https://img.shields.io/badge/-Linux-grey?logo=linux)
![OSX](https://img.shields.io/badge/-OSX-black?logo=apple)
![FreeBSD](https://img.shields.io/badge/-FreeBSD-red?logo=freebsd)
![Usage](https://img.shields.io/badge/Usage-System%20resource%20monitor-blue)
![Python](https://img.shields.io/badge/Python-v3.6%5E-orange?logo=python)
![bpytop_version](https://img.shields.io/github/v/tag/aristocratos/bpytop?label=version)
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

#### [CHANGELOG.md](CHANGELOG.md)

#### [CONTRIBUTING.md](CONTRIBUTING.md)

#### [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

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

See [themes](themes) folder for available themes.

The `make install` command places the default themes in `/usr/local/share/bpytop/themes`.
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
![Screenshot 1](Imgs/main.png)

Main UI in mini mode.
![Screenshot 2](Imgs/mini.png)

Main menu.
![Screenshot 3](Imgs/menu.png)

Options menu.
![Screenshot 4](Imgs/options.png)

## Installation

PyPi packaging for installation with `pip` will be setup later.

If you want to help speed this up, help with setting up proper testing is welcome!

#### Dependencies installation Linux

>Install python3 and git with a package manager of you choice

>Install psutil python module for your python3 interpreter. If your system interpreter is version 3.6 or later, you can use it.

``` bash
python3 -m pip install psutil
```

#### Dependencies installation OSX

>If you haven't installed git and python 3.6 or later,
>you can install them via [homebrew](https://brew.sh/). 

>Install python3 if not already installed

``` bash
brew install python3 git
```

>Install psutil python module for your python3 interpreter. If your system interpreter is version 3.6 or later, you can use it.

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
sudo pkg install python3 git
sudo python3 -m ensurepip
sudo python3 -m pip install psutil
```

#### Manual installation Linux, OSX and FreeBSD

>Clone and install



``` bash
git clone https://github.com/aristocratos/bpytop.git
cd bpytop
make install
```
>The default interpreter will be `/usr/bin/python3`. If you want to use a different one, you can run `make install PYTHON_INTERPRETER=$YOUR_INTERPRETER`. For example
```bash
make install PYTHON_INTERPRETER=$(which python)
```
>Just make sure that you've installed `psutil` for the selected interpreter.

>to uninstall it

``` bash
make uninstall
```

## Configurability

All options changeable from within UI.
Config files stored in "$HOME/.config/bpytop" folder

#### bpytop.cfg: (auto generated if not found)

"/etc/bpytop.conf" will be used as default seed for config file creation if it exists.

```bash
#? Config file for bpytop v. 1.0.0

#* Color theme, looks for a .theme file in "/usr/[local/]share/bpytop/themes" and "~/.config/bpytop/themes", "Default" for builtin default theme.
#* Prefix name by a plus sign (+) for a theme located in user themes folder, i.e. color_theme="+monokai"
color_theme="Default"

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
proc_per_core=False

#* Check cpu temperature, needs "vcgencmd" on Raspberry Pi and "osx-cpu-temp" on MacOS X.
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
show_swap=False

#* Show swap as a disk, ignores show_swap value above, inserts itself after first disk.
swap_disk=True

#* If mem box should be split to also show disks info.
show_disks=True

#* Show init screen at startup, the init screen is purely cosmetical
show_init=True

#* Enable check for new version from github.com/aristocratos/bpytop at start.
update_check=True

#* Enable start in mini mode, can be toggled with shift+m at any time.
mini_mode=False

#* Set loglevel for "~/.config/bpytop/error.log" levels are: "ERROR" "WARNING" "INFO" "DEBUG".
#* The level set includes all lower levels, i.e. "DEBUG" will show all logging info.
log_level=WARNING

```

#### Command line options: (not yet implemented)

``` text
USAGE: bpytop [argument]

Arguments:
    -m, --mini            Start in minimal mode without memory and net boxes
    -v, --version         Show version info and exit
    -h, --help            Show this help message and exit
    --debug               Start with loglevel set to DEBUG overriding value set in config
```

## TODO

- [ ] See TODOs from [Bashtop](https://github.com/aristocratos/bashtop#todo).

## LICENSE

[Apache License 2.0](LICENSE)
