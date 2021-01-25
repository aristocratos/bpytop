#!/usr/bin/env python3
# pylint: disable=not-callable, no-member, unsubscriptable-object
# indent = tab
# tab-size = 4

# Copyright 2020 Aristocratos (jakob@qvantnet.com)

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os, sys, io, threading, signal, re, subprocess, logging, logging.handlers, argparse
import urllib.request
from time import time, sleep, strftime, localtime
from datetime import timedelta
from _thread import interrupt_main
from collections import defaultdict
from select import select
from distutils.util import strtobool
from string import Template
from math import ceil, floor
from random import randint
from shutil import which
from typing import List, Set, Dict, Tuple, Optional, Union, Any, Callable, ContextManager, Iterable, Type, NamedTuple

errors: List[str] = []
try: import fcntl, termios, tty, pwd
except Exception as e: errors.append(f'{e}')

try: import psutil # type: ignore
except Exception as e: errors.append(f'{e}')

SELF_START = time()

SYSTEM: str
if "linux" in sys.platform: SYSTEM = "Linux"
elif "bsd" in sys.platform: SYSTEM = "BSD"
elif "darwin" in sys.platform: SYSTEM = "MacOS"
else: SYSTEM = "Other"

if errors:
	print("ERROR!")
	print("\n".join(errors))
	if SYSTEM == "Other":
		print("\nUnsupported platform!\n")
	else:
		print("\nInstall required modules!\n")
	raise SystemExit(1)

VERSION: str = "1.0.61"

#? Argument parser ------------------------------------------------------------------------------->
args = argparse.ArgumentParser()
args.add_argument("-b", "--boxes",		action="store",	dest="boxes", 	help = "which boxes to show at start, example: -b \"cpu mem net proc\"")
args.add_argument("-lc", "--low-color", action="store_true", 			help = "disable truecolor, converts 24-bit colors to 256-color")
args.add_argument("-v", "--version",	action="store_true", 			help = "show version info and exit")
args.add_argument("--debug",			action="store_true", 			help = "start with loglevel set to DEBUG overriding value set in config")
stdargs = args.parse_args()

if stdargs.version:
	print(f'bpytop version: {VERSION}\n'
		f'psutil version: {".".join(str(x) for x in psutil.version_info)}')
	raise SystemExit(0)

ARG_BOXES: str = stdargs.boxes
LOW_COLOR: bool = stdargs.low_color
DEBUG: bool = stdargs.debug

#? Variables ------------------------------------------------------------------------------------->

BANNER_SRC: List[Tuple[str, str, str]] = [
	("#ffa50a", "#0fd7ff", "██████╗ ██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗"),
	("#f09800", "#00bfe6", "██╔══██╗██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗"),
	("#db8b00", "#00a6c7", "██████╔╝██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝"),
	("#c27b00", "#008ca8", "██╔══██╗██╔═══╝   ╚██╔╝     ██║   ██║   ██║██╔═══╝ "),
	("#a86b00", "#006e85", "██████╔╝██║        ██║      ██║   ╚██████╔╝██║"),
	("#000000", "#000000", "╚═════╝ ╚═╝        ╚═╝      ╚═╝    ╚═════╝ ╚═╝"),
]

#*?This is the template used to create the config file
DEFAULT_CONF: Template = Template(f'#? Config file for bpytop v. {VERSION}' + '''

#* Color theme, looks for a .theme file in "/usr/[local/]share/bpytop/themes" and "~/.config/bpytop/themes", "Default" for builtin default theme.
#* Prefix name by a plus sign (+) for a theme located in user themes folder, i.e. color_theme="+monokai"
color_theme="$color_theme"

#* If the theme set background should be shown, set to False if you want terminal background transparency
theme_background=$theme_background

#* Sets if 24-bit truecolor should be used, will convert 24-bit colors to 256 color (6x6x6 color cube) if false.
truecolor=$truecolor

#* Manually set which boxes to show. Available values are "cpu mem net proc", seperate values with whitespace.
shown_boxes="$shown_boxes"

#* Update time in milliseconds, increases automatically if set below internal loops processing time, recommended 2000 ms or above for better sample times for graphs.
update_ms=$update_ms

#* Processes update multiplier, sets how often the process list is updated as a multiplier of "update_ms".
#* Set to 2 or higher to greatly decrease bpytop cpu usage. (Only integers)
proc_update_mult=$proc_update_mult

#* Processes sorting, "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive",
#* "cpu lazy" updates top process over time, "cpu responsive" updates top process directly.
proc_sorting="$proc_sorting"

#* Reverse sorting order, True or False.
proc_reversed=$proc_reversed

#* Show processes as a tree
proc_tree=$proc_tree

#* Which depth the tree view should auto collapse processes at
tree_depth=$tree_depth

#* Use the cpu graph colors in the process list.
proc_colors=$proc_colors

#* Use a darkening gradient in the process list.
proc_gradient=$proc_gradient

#* If process cpu usage should be of the core it's running on or usage of the total available cpu power.
proc_per_core=$proc_per_core

#* Show process memory as bytes instead of percent
proc_mem_bytes=$proc_mem_bytes

#* Sets the CPU stat shown in upper half of the CPU graph, "total" is always available, see:
#* https://psutil.readthedocs.io/en/latest/#psutil.cpu_times for attributes available on specific platforms.
#* Select from a list of detected attributes from the options menu
cpu_graph_upper="$cpu_graph_upper"

#* Sets the CPU stat shown in lower half of the CPU graph, "total" is always available, see:
#* https://psutil.readthedocs.io/en/latest/#psutil.cpu_times for attributes available on specific platforms.
#* Select from a list of detected attributes from the options menu
cpu_graph_lower="$cpu_graph_lower"

#* Toggles if the lower CPU graph should be inverted.
cpu_invert_lower=$cpu_invert_lower

#* Set to True to completely disable the lower CPU graph.
cpu_single_graph=$cpu_single_graph

#* Shows the system uptime in the CPU box.
show_uptime=$show_uptime

#* Check cpu temperature, needs "osx-cpu-temp" on MacOS X.
check_temp=$check_temp

#* Which sensor to use for cpu temperature, use options menu to select from list of available sensors.
cpu_sensor=$cpu_sensor

#* Show temperatures for cpu cores also if check_temp is True and sensors has been found
show_coretemp=$show_coretemp

#* Draw a clock at top of screen, formatting according to strftime, empty string to disable.
draw_clock="$draw_clock"

#* Update main ui in background when menus are showing, set this to false if the menus is flickering too much for comfort.
background_update=$background_update

#* Custom cpu model name, empty string to disable.
custom_cpu_name="$custom_cpu_name"

#* Optional filter for shown disks, should be full path of a mountpoint, separate multiple values with a comma ",".
#* Begin line with "exclude=" to change to exclude filter, oterwise defaults to "most include" filter. Example: disks_filter="exclude=/boot, /home/user"
disks_filter="$disks_filter"

#* Show graphs instead of meters for memory values.
mem_graphs=$mem_graphs

#* If swap memory should be shown in memory box.
show_swap=$show_swap

#* Show swap as a disk, ignores show_swap value above, inserts itself after first disk.
swap_disk=$swap_disk

#* If mem box should be split to also show disks info.
show_disks=$show_disks

#* Filter out non physical disks. Set this to False to include network disks, RAM disks and similar.
only_physical=$only_physical

#* Read disks list from /etc/fstab. This also disables only_physical.
use_fstab=$use_fstab

#* Toggles if io stats should be shown in regular disk usage view
show_io_stat=$show_io_stat

#* Toggles io mode for disks, showing only big graphs for disk read/write speeds.
io_mode=$io_mode

#* Set to True to show combined read/write io graphs in io mode.
io_graph_combined=$io_graph_combined

#* Set the top speed for the io graphs in MiB/s (10 by default), use format "device:speed" seperate disks with a comma ",".
#* Example: "/dev/sda:100, /dev/sdb:20"
io_graph_speeds="$io_graph_speeds"

#* Set fixed values for network graphs, default "10M" = 10 Mibibytes, possible units "K", "M", "G", append with "bit" for bits instead of bytes, i.e "100mbit"
net_download="$net_download"
net_upload="$net_upload"

#* Start in network graphs auto rescaling mode, ignores any values set above and rescales down to 10 Kibibytes at the lowest.
net_auto=$net_auto

#* Sync the scaling for download and upload to whichever currently has the highest scale
net_sync=$net_sync

#* If the network graphs color gradient should scale to bandwith usage or auto scale, bandwith usage is based on "net_download" and "net_upload" values
net_color_fixed=$net_color_fixed

#* Starts with the Network Interface specified here.
net_iface="$net_iface"

#* Show battery stats in top right if battery is present
show_battery=$show_battery

#* Show init screen at startup, the init screen is purely cosmetical
show_init=$show_init

#* Enable check for new version from github.com/aristocratos/bpytop at start.
update_check=$update_check

#* Set loglevel for "~/.config/bpytop/error.log" levels are: "ERROR" "WARNING" "INFO" "DEBUG".
#* The level set includes all lower levels, i.e. "DEBUG" will show all logging info.
log_level=$log_level
''')

CONFIG_DIR: str = f'{os.path.expanduser("~")}/.config/bpytop'
if not os.path.isdir(CONFIG_DIR):
	try:
		os.makedirs(CONFIG_DIR)
		os.mkdir(f'{CONFIG_DIR}/themes')
	except PermissionError:
		print(f'ERROR!\nNo permission to write to "{CONFIG_DIR}" directory!')
		raise SystemExit(1)
CONFIG_FILE: str = f'{CONFIG_DIR}/bpytop.conf'
THEME_DIR: str = ""

if os.path.isdir(f'{os.path.dirname(__file__)}/bpytop-themes'):
	THEME_DIR = f'{os.path.dirname(__file__)}/bpytop-themes'
else:
	for td in ["/usr/local/", "/usr/", "/snap/bpytop/current/usr/"]:
		if os.path.isdir(f'{td}share/bpytop/themes'):
			THEME_DIR = f'{td}share/bpytop/themes'
			break
USER_THEME_DIR: str = f'{CONFIG_DIR}/themes'

CORES: int = psutil.cpu_count(logical=False) or 1
THREADS: int = psutil.cpu_count(logical=True) or 1

THREAD_ERROR: int = 0

DEFAULT_THEME: Dict[str, str] = {
	"main_bg" : "#00",
	"main_fg" : "#cc",
	"title" : "#ee",
	"hi_fg" : "#969696",
	"selected_bg" : "#7e2626",
	"selected_fg" : "#ee",
	"inactive_fg" : "#40",
	"graph_text" : "#60",
	"meter_bg" : "#40",
	"proc_misc" : "#0de756",
	"cpu_box" : "#3d7b46",
	"mem_box" : "#8a882e",
	"net_box" : "#423ba5",
	"proc_box" : "#923535",
	"div_line" : "#30",
	"temp_start" : "#4897d4",
	"temp_mid" : "#5474e8",
	"temp_end" : "#ff40b6",
	"cpu_start" : "#50f095",
	"cpu_mid" : "#f2e266",
	"cpu_end" : "#fa1e1e",
	"free_start" : "#223014",
	"free_mid" : "#b5e685",
	"free_end" : "#dcff85",
	"cached_start" : "#0b1a29",
	"cached_mid" : "#74e6fc",
	"cached_end" : "#26c5ff",
	"available_start" : "#292107",
	"available_mid" : "#ffd77a",
	"available_end" : "#ffb814",
	"used_start" : "#3b1f1c",
	"used_mid" : "#d9626d",
	"used_end" : "#ff4769",
	"download_start" : "#231a63",
	"download_mid" : "#4f43a3",
	"download_end" : "#b0a9de",
	"upload_start" : "#510554",
	"upload_mid" : "#7d4180",
	"upload_end" : "#dcafde",
	"process_start" : "#80d0a3",
	"process_mid" : "#dcd179",
	"process_end" : "#d45454",
}

MENUS: Dict[str, Dict[str, Tuple[str, ...]]] = {
	"options" : {
		"normal" : (
			"┌─┐┌─┐┌┬┐┬┌─┐┌┐┌┌─┐",
			"│ │├─┘ │ ││ ││││└─┐",
			"└─┘┴   ┴ ┴└─┘┘└┘└─┘"),
		"selected" : (
			"╔═╗╔═╗╔╦╗╦╔═╗╔╗╔╔═╗",
			"║ ║╠═╝ ║ ║║ ║║║║╚═╗",
			"╚═╝╩   ╩ ╩╚═╝╝╚╝╚═╝") },
	"help" : {
		"normal" : (
			"┬ ┬┌─┐┬  ┌─┐",
			"├─┤├┤ │  ├─┘",
			"┴ ┴└─┘┴─┘┴  "),
		"selected" : (
			"╦ ╦╔═╗╦  ╔═╗",
			"╠═╣║╣ ║  ╠═╝",
			"╩ ╩╚═╝╩═╝╩  ") },
	"quit" : {
		"normal" : (
			"┌─┐ ┬ ┬ ┬┌┬┐",
			"│─┼┐│ │ │ │ ",
			"└─┘└└─┘ ┴ ┴ "),
		"selected" : (
			"╔═╗ ╦ ╦ ╦╔╦╗ ",
			"║═╬╗║ ║ ║ ║  ",
			"╚═╝╚╚═╝ ╩ ╩  ") }
}

MENU_COLORS: Dict[str, Tuple[str, ...]] = {
	"normal" : ("#0fd7ff", "#00bfe6", "#00a6c7", "#008ca8"),
	"selected" : ("#ffa50a", "#f09800", "#db8b00", "#c27b00")
}

#? Units for floating_humanizer function
UNITS: Dict[str, Tuple[str, ...]] = {
	"bit" : ("bit", "Kib", "Mib", "Gib", "Tib", "Pib", "Eib", "Zib", "Yib", "Bib", "GEb"),
	"byte" : ("Byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB", "BiB", "GEB")
}

SUBSCRIPT: Tuple[str, ...] = ("₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉")
SUPERSCRIPT: Tuple[str, ...] = ("⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹")

#? Setup error logger ---------------------------------------------------------------->

try:
	errlog = logging.getLogger("ErrorLogger")
	errlog.setLevel(logging.DEBUG)
	eh = logging.handlers.RotatingFileHandler(f'{CONFIG_DIR}/error.log', maxBytes=1048576, backupCount=4)
	eh.setLevel(logging.DEBUG)
	eh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s: %(message)s", datefmt="%d/%m/%y (%X)"))
	errlog.addHandler(eh)
except PermissionError:
	print(f'ERROR!\nNo permission to write to "{CONFIG_DIR}" directory!')
	raise SystemExit(1)

#? Timers for testing and debugging -------------------------------------------------------------->

class TimeIt:
	timers: Dict[str, float] = {}
	paused: Dict[str, float] = {}

	@classmethod
	def start(cls, name):
		cls.timers[name] = time()

	@classmethod
	def pause(cls, name):
		if name in cls.timers:
			cls.paused[name] = time() - cls.timers[name]
			del cls.timers[name]

	@classmethod
	def stop(cls, name):
		if name in cls.timers:
			total: float = time() - cls.timers[name]
			del cls.timers[name]
			if name in cls.paused:
				total += cls.paused[name]
				del cls.paused[name]
			errlog.debug(f'{name} completed in {total:.6f} seconds')

def timeit_decorator(func):
	def timed(*args, **kw):
		ts = time()
		out = func(*args, **kw)
		errlog.debug(f'{func.__name__} completed in {time() - ts:.6f} seconds')
		return out
	return timed

#? Set up config class and load config ----------------------------------------------------------->

class Config:
	'''Holds all config variables and functions for loading from and saving to disk'''
	keys: List[str] = ["color_theme", "update_ms", "proc_sorting", "proc_reversed", "proc_tree", "check_temp", "draw_clock", "background_update", "custom_cpu_name",
						"proc_colors", "proc_gradient", "proc_per_core", "proc_mem_bytes", "disks_filter", "update_check", "log_level", "mem_graphs", "show_swap",
						"swap_disk", "show_disks", "use_fstab", "net_download", "net_upload", "net_auto", "net_color_fixed", "show_init", "theme_background",
						"net_sync", "show_battery", "tree_depth", "cpu_sensor", "show_coretemp", "proc_update_mult", "shown_boxes", "net_iface", "only_physical",
						"truecolor", "io_mode", "io_graph_combined", "io_graph_speeds", "show_io_stat", "cpu_graph_upper", "cpu_graph_lower", "cpu_invert_lower",
						"cpu_single_graph", "show_uptime"]
	conf_dict: Dict[str, Union[str, int, bool]] = {}
	color_theme: str = "Default"
	theme_background: bool = True
	truecolor: bool = True
	shown_boxes: str = "cpu mem net proc"
	update_ms: int = 2000
	proc_update_mult: int = 2
	proc_sorting: str = "cpu lazy"
	proc_reversed: bool = False
	proc_tree: bool = False
	tree_depth: int = 3
	proc_colors: bool = True
	proc_gradient: bool = True
	proc_per_core: bool = False
	proc_mem_bytes: bool = True
	cpu_graph_upper: str = "total"
	cpu_graph_lower: str = "total"
	cpu_invert_lower: bool = True
	cpu_single_graph: bool = False
	show_uptime: bool = True
	check_temp: bool = True
	cpu_sensor: str = "Auto"
	show_coretemp: bool = True
	draw_clock: str = "%X"
	background_update: bool = True
	custom_cpu_name: str = ""
	disks_filter: str = ""
	update_check: bool = True
	mem_graphs: bool = True
	show_swap: bool = True
	swap_disk: bool = True
	show_disks: bool = True
	only_physical: bool = True
	use_fstab: bool = False
	show_io_stat: bool = True
	io_mode: bool = False
	io_graph_combined: bool = False
	io_graph_speeds: str = ""
	net_download: str = "10M"
	net_upload: str = "10M"
	net_color_fixed: bool = False
	net_auto: bool = True
	net_sync: bool = False
	net_iface: str = ""
	show_battery: bool = True
	show_init: bool = True
	log_level: str = "WARNING"

	warnings: List[str] = []
	info: List[str] = []

	sorting_options: List[str] = ["pid", "program", "arguments", "threads", "user", "memory", "cpu lazy", "cpu responsive"]
	log_levels: List[str] = ["ERROR", "WARNING", "INFO", "DEBUG"]
	cpu_percent_fields: List = ["total"]
	cpu_percent_fields.extend(getattr(psutil.cpu_times_percent(), "_fields", []))

	cpu_sensors: List[str] = [ "Auto" ]

	if hasattr(psutil, "sensors_temperatures"):
		try:
			_temps = psutil.sensors_temperatures()
			if _temps:
				for _name, _entries in _temps.items():
					for _num, _entry in enumerate(_entries, 1):
						if hasattr(_entry, "current"):
							cpu_sensors.append(f'{_name}:{_num if _entry.label == "" else _entry.label}')
		except:
			pass

	changed: bool = False
	recreate: bool = False
	config_file: str = ""

	_initialized: bool = False

	def __init__(self, path: str):
		self.config_file = path
		conf: Dict[str, Union[str, int, bool]] = self.load_config()
		if not "version" in conf.keys():
			self.recreate = True
			self.info.append(f'Config file malformatted or missing, will be recreated on exit!')
		elif conf["version"] != VERSION:
			self.recreate = True
			self.info.append(f'Config file version and bpytop version missmatch, will be recreated on exit!')
		for key in self.keys:
			if key in conf.keys() and conf[key] != "_error_":
				setattr(self, key, conf[key])
			else:
				self.recreate = True
				self.conf_dict[key] = getattr(self, key)
		self._initialized = True

	def __setattr__(self, name, value):
		if self._initialized:
			object.__setattr__(self, "changed", True)
		object.__setattr__(self, name, value)
		if name not in ["_initialized", "recreate", "changed"]:
			self.conf_dict[name] = value

	def load_config(self) -> Dict[str, Union[str, int, bool]]:
		'''Load config from file, set correct types for values and return a dict'''
		new_config: Dict[str,Union[str, int, bool]] = {}
		conf_file: str = ""
		if os.path.isfile(self.config_file):
			conf_file = self.config_file
		elif os.path.isfile("/etc/bpytop.conf"):
			conf_file = "/etc/bpytop.conf"
		else:
			return new_config
		try:
			with open(conf_file, "r") as f:
				for line in f:
					line = line.strip()
					if line.startswith("#? Config"):
						new_config["version"] = line[line.find("v. ") + 3:]
						continue
					if not '=' in line:
						continue
					key, line = line.split('=', maxsplit=1)
					if not key in self.keys:
						continue
					line = line.strip('"')
					if type(getattr(self, key)) == int:
						try:
							new_config[key] = int(line)
						except ValueError:
							self.warnings.append(f'Config key "{key}" should be an integer!')
					if type(getattr(self, key)) == bool:
						try:
							new_config[key] = bool(strtobool(line))
						except ValueError:
							self.warnings.append(f'Config key "{key}" can only be True or False!')
					if type(getattr(self, key)) == str:
						new_config[key] = str(line)
		except Exception as e:
			errlog.exception(str(e))
		if "proc_sorting" in new_config and not new_config["proc_sorting"] in self.sorting_options:
			new_config["proc_sorting"] = "_error_"
			self.warnings.append(f'Config key "proc_sorted" didn\'t get an acceptable value!')
		if "log_level" in new_config and not new_config["log_level"] in self.log_levels:
			new_config["log_level"] = "_error_"
			self.warnings.append(f'Config key "log_level" didn\'t get an acceptable value!')
		if "update_ms" in new_config and int(new_config["update_ms"]) < 100:
			new_config["update_ms"] = 100
			self.warnings.append(f'Config key "update_ms" can\'t be lower than 100!')
		for net_name in ["net_download", "net_upload"]:
			if net_name in new_config and not new_config[net_name][0].isdigit(): # type: ignore
				new_config[net_name] = "_error_"
		if "cpu_sensor" in new_config and not new_config["cpu_sensor"] in self.cpu_sensors:
			new_config["cpu_sensor"] = "_error_"
			self.warnings.append(f'Config key "cpu_sensor" does not contain an available sensor!')
		if "shown_boxes" in new_config and not new_config["shown_boxes"] == "":
			for box in new_config["shown_boxes"].split(): #type: ignore
				if not box in ["cpu", "mem", "net", "proc"]:
					new_config["shown_boxes"] = "_error_"
					self.warnings.append(f'Config key "shown_boxes" contains invalid box names!')
					break
		for cpu_graph in ["cpu_graph_upper", "cpu_graph_lower"]:
			if cpu_graph in new_config and not new_config[cpu_graph] in self.cpu_percent_fields:
				new_config[cpu_graph] = "_error_"
				self.warnings.append(f'Config key "{cpu_graph}" does not contain an available cpu stat attribute!')
		return new_config

	def save_config(self):
		'''Save current config to config file if difference in values or version, creates a new file if not found'''
		if not self.changed and not self.recreate: return
		try:
			with open(self.config_file, "w" if os.path.isfile(self.config_file) else "x") as f:
				f.write(DEFAULT_CONF.substitute(self.conf_dict))
		except Exception as e:
			errlog.exception(str(e))

try:
	CONFIG: Config = Config(CONFIG_FILE)
	if DEBUG:
		errlog.setLevel(logging.DEBUG)
	else:
		errlog.setLevel(getattr(logging, CONFIG.log_level))
		DEBUG = CONFIG.log_level == "DEBUG"
	errlog.info(f'New instance of bpytop version {VERSION} started with pid {os.getpid()}')
	errlog.info(f'Loglevel set to {"DEBUG" if DEBUG else CONFIG.log_level}')
	errlog.debug(f'Using psutil version {".".join(str(x) for x in psutil.version_info)}')
	errlog.debug(f'CMD: {" ".join(sys.argv)}')
	if CONFIG.info:
		for info in CONFIG.info:
			errlog.info(info)
		CONFIG.info = []
	if CONFIG.warnings:
		for warning in CONFIG.warnings:
			errlog.warning(warning)
		CONFIG.warnings = []
except Exception as e:
	errlog.exception(f'{e}')
	raise SystemExit(1)

if ARG_BOXES:
	_new_boxes: List = []
	for _box in ARG_BOXES.split():
		if _box in ["cpu", "mem", "net", "proc"]:
			_new_boxes.append(_box)
	CONFIG.shown_boxes = " ".join(_new_boxes)
	del _box, _new_boxes

if SYSTEM == "Linux" and not os.path.isdir("/sys/class/power_supply"):
	CONFIG.show_battery = False

if psutil.version_info[0] < 5 or (psutil.version_info[0] == 5 and psutil.version_info[1] < 7):
	warn = f'psutil version {".".join(str(x) for x in psutil.version_info)} detected, version 5.7.0 or later required for full functionality!'
	print("WARNING!", warn)
	errlog.warning(warn)


#? Classes --------------------------------------------------------------------------------------->

class Term:
	"""Terminal info and commands"""
	width: int = 0
	height: int = 0
	resized: bool = False
	_w : int = 0
	_h : int = 0
	fg: str = "" 												#* Default foreground color
	bg: str = "" 												#* Default background color
	hide_cursor 		= "\033[?25l"							#* Hide terminal cursor
	show_cursor 		= "\033[?25h"							#* Show terminal cursor
	alt_screen 			= "\033[?1049h"							#* Switch to alternate screen
	normal_screen 		= "\033[?1049l"							#* Switch to normal screen
	clear				= "\033[2J\033[0;0f"					#* Clear screen and set cursor to position 0,0
	mouse_on			= "\033[?1002h\033[?1015h\033[?1006h" 	#* Enable reporting of mouse position on click and release
	mouse_off			= "\033[?1002l" 						#* Disable mouse reporting
	mouse_direct_on		= "\033[?1003h"							#* Enable reporting of mouse position at any movement
	mouse_direct_off	= "\033[?1003l"							#* Disable direct mouse reporting
	winch = threading.Event()
	old_boxes: List = []
	min_width: int = 0
	min_height: int = 0

	@classmethod
	def refresh(cls, *args, force: bool = False):
		"""Update width, height and set resized flag if terminal has been resized"""
		if Init.running: cls.resized = False; return
		if cls.resized: cls.winch.set(); return
		cls._w, cls._h = os.get_terminal_size()
		if (cls._w, cls._h) == (cls.width, cls.height) and cls.old_boxes == Box.boxes and not force: return
		if force: Collector.collect_interrupt = True
		if cls.old_boxes != Box.boxes:
			w_p = h_p = 0
			cls.min_width = cls.min_height = 0
			cls.old_boxes = Box.boxes.copy()
			for box_class in Box.__subclasses__():
				for box_name in Box.boxes:
					if box_name in str(box_class).capitalize():
						if not (box_name == "cpu" and "proc" in Box.boxes) and not (box_name == "net" and "mem" in Box.boxes) and w_p + box_class.width_p <= 100:
							w_p += box_class.width_p
							cls.min_width += getattr(box_class, "min_w", 0)
						if not (box_name in ["mem", "net"] and "proc" in Box.boxes) and h_p + box_class.height_p <= 100:
							h_p += box_class.height_p
							cls.min_height += getattr(box_class, "min_h", 0)
		while (cls._w, cls._h) != (cls.width, cls.height) or (cls._w < cls.min_width or cls._h < cls.min_height):
			if Init.running: Init.resized = True
			CpuBox.clock_block = True
			cls.resized = True
			Collector.collect_interrupt = True
			cls.width, cls.height = cls._w, cls._h
			Draw.now(Term.clear)
			box_width = min(50, cls._w - 2)
			Draw.now(f'{create_box(cls._w // 2 - box_width // 2, cls._h // 2 - 2, 50, 3, "resizing", line_color=Colors.green, title_color=Colors.white)}',
				f'{Mv.r(box_width // 4)}{Colors.default}{Colors.black_bg}{Fx.b}Width : {cls._w}   Height: {cls._h}{Fx.ub}{Term.bg}{Term.fg}')
			if cls._w < 80 or cls._h < 24:
				while cls._w < cls.min_width or cls._h < cls.min_height:
					Draw.now(Term.clear)
					box_width = min(50, cls._w - 2)
					Draw.now(f'{create_box(cls._w // 2 - box_width // 2, cls._h // 2 - 2, box_width, 4, "warning", line_color=Colors.red, title_color=Colors.white)}',
						f'{Mv.r(box_width // 4)}{Colors.default}{Colors.black_bg}{Fx.b}Width: {Colors.red if cls._w < cls.min_width else Colors.green}{cls._w}   ',
						f'{Colors.default}Height: {Colors.red if cls._h < cls.min_height else Colors.green}{cls._h}{Term.bg}{Term.fg}',
						f'{Mv.d(1)}{Mv.l(25)}{Colors.default}{Colors.black_bg}Current config need: {cls.min_width} x {cls.min_height}{Fx.ub}{Term.bg}{Term.fg}')
					cls.winch.wait(0.3)
					cls.winch.clear()
					cls._w, cls._h = os.get_terminal_size()
			else:
				cls.winch.wait(0.3)
				cls.winch.clear()
			cls._w, cls._h = os.get_terminal_size()

		Key.mouse = {}
		Box.calc_sizes()
		Collector.proc_counter = 1
		if Menu.active: Menu.resized = True
		Box.draw_bg(now=False)
		cls.resized = False
		Timer.finish()

	@staticmethod
	def echo(on: bool):
		"""Toggle input echo"""
		(iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(sys.stdin.fileno())
		if on:
			lflag |= termios.ECHO # type: ignore
		else:
			lflag &= ~termios.ECHO # type: ignore
		new_attr = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
		termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, new_attr)

	@staticmethod
	def title(text: str = "") -> str:
		out: str = f'{os.environ.get("TERMINAL_TITLE", "")}'
		if out and text: out += " "
		if text: out += f'{text}'
		return f'\033]0;{out}\a'

class Fx:
	"""Text effects
	* trans(string: str): Replace whitespace with escape move right to not overwrite background behind whitespace.
	* uncolor(string: str) : Removes all 24-bit color and returns string ."""
	start					= "\033["			#* Escape sequence start
	sep						= ";"				#* Escape sequence separator
	end						= "m"				#* Escape sequence end
	reset = rs				= "\033[0m"			#* Reset foreground/background color and text effects
	bold = b				= "\033[1m"			#* Bold on
	unbold = ub				= "\033[22m"		#* Bold off
	dark = d				= "\033[2m"			#* Dark on
	undark = ud				= "\033[22m"		#* Dark off
	italic = i				= "\033[3m"			#* Italic on
	unitalic = ui			= "\033[23m"		#* Italic off
	underline = u			= "\033[4m"			#* Underline on
	ununderline = uu		= "\033[24m"		#* Underline off
	blink = bl 				= "\033[5m"			#* Blink on
	unblink = ubl			= "\033[25m"		#* Blink off
	strike = s 				= "\033[9m"			#* Strike / crossed-out on
	unstrike = us			= "\033[29m"		#* Strike / crossed-out off

	#* Precompiled regex for finding a 24-bit color escape sequence in a string
	color_re = re.compile(r"\033\[\d+;\d?;?\d*;?\d*;?\d*m")

	@staticmethod
	def trans(string: str):
		return string.replace(" ", "\033[1C")

	@classmethod
	def uncolor(cls, string: str) -> str:
		return f'{cls.color_re.sub("", string)}'

class Raw(object):
	"""Set raw input mode for device"""
	def __init__(self, stream):
		self.stream = stream
		self.fd = self.stream.fileno()
	def __enter__(self):
		self.original_stty = termios.tcgetattr(self.stream)
		tty.setcbreak(self.stream)
	def __exit__(self, type, value, traceback):
		termios.tcsetattr(self.stream, termios.TCSANOW, self.original_stty)

class Nonblocking(object):
	"""Set nonblocking mode for device"""
	def __init__(self, stream):
		self.stream = stream
		self.fd = self.stream.fileno()
	def __enter__(self):
		self.orig_fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
		fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl | os.O_NONBLOCK)
	def __exit__(self, *args):
		fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl)

class Mv:
	"""Class with collection of cursor movement functions: .t[o](line, column) | .r[ight](columns) | .l[eft](columns) | .u[p](lines) | .d[own](lines) | .save() | .restore()"""
	@staticmethod
	def to(line: int, col: int) -> str:
		return f'\033[{line};{col}f'	#* Move cursor to line, column
	@staticmethod
	def right(x: int) -> str:			#* Move cursor right x columns
		return f'\033[{x}C'
	@staticmethod
	def left(x: int) -> str:			#* Move cursor left x columns
		return f'\033[{x}D'
	@staticmethod
	def up(x: int) -> str:				#* Move cursor up x lines
		return f'\033[{x}A'
	@staticmethod
	def down(x: int) -> str:			#* Move cursor down x lines
		return f'\033[{x}B'

	save: str = "\033[s" 				#* Save cursor position
	restore: str = "\033[u" 			#* Restore saved cursor postion
	t = to
	r = right
	l = left
	u = up
	d = down

class Key:
	"""Handles the threaded input reader for keypresses and mouse events"""
	list: List[str] = []
	mouse: Dict[str, List[List[int]]] = {}
	mouse_pos: Tuple[int, int] = (0, 0)
	escape: Dict[Union[str, Tuple[str, str]], str] = {
		"\n" :					"enter",
		("\x7f", "\x08") :		"backspace",
		("[A", "OA") :			"up",
		("[B", "OB") :			"down",
		("[D", "OD") :			"left",
		("[C", "OC") :			"right",
		"[2~" :					"insert",
		"[3~" :					"delete",
		"[H" :					"home",
		"[F" :					"end",
		"[5~" :					"page_up",
		"[6~" :					"page_down",
		"\t" :					"tab",
		"[Z" :					"shift_tab",
		"OP" :					"f1",
		"OQ" :					"f2",
		"OR" :					"f3",
		"OS" :					"f4",
		"[15" :					"f5",
		"[17" :					"f6",
		"[18" :					"f7",
		"[19" :					"f8",
		"[20" :					"f9",
		"[21" :					"f10",
		"[23" :					"f11",
		"[24" :					"f12"
		}
	new = threading.Event()
	idle = threading.Event()
	mouse_move = threading.Event()
	mouse_report: bool = False
	idle.set()
	stopping: bool = False
	started: bool = False
	reader: threading.Thread
	@classmethod
	def start(cls):
		cls.stopping = False
		cls.reader = threading.Thread(target=cls._get_key)
		cls.reader.start()
		cls.started = True

	@classmethod
	def stop(cls):
		if cls.started and cls.reader.is_alive():
			cls.stopping = True
			try:
				cls.reader.join()
			except:
				pass

	@classmethod
	def last(cls) -> str:
		if cls.list: return cls.list.pop()
		else: return ""

	@classmethod
	def get(cls) -> str:
		if cls.list: return cls.list.pop(0)
		else: return ""

	@classmethod
	def get_mouse(cls) -> Tuple[int, int]:
		if cls.new.is_set():
			cls.new.clear()
		return cls.mouse_pos

	@classmethod
	def mouse_moved(cls) -> bool:
		if cls.mouse_move.is_set():
			cls.mouse_move.clear()
			return True
		else:
			return False

	@classmethod
	def has_key(cls) -> bool:
		return bool(cls.list)

	@classmethod
	def clear(cls):
		cls.list = []

	@classmethod
	def input_wait(cls, sec: float = 0.0, mouse: bool = False) -> bool:
		'''Returns True if key is detected else waits out timer and returns False'''
		if cls.list: return True
		if mouse: Draw.now(Term.mouse_direct_on)
		cls.new.wait(sec if sec > 0 else 0.0)
		if mouse: Draw.now(Term.mouse_direct_off, Term.mouse_on)

		if cls.new.is_set():
			cls.new.clear()
			return True
		else:
			return False

	@classmethod
	def break_wait(cls):
		cls.list.append("_null")
		cls.new.set()
		sleep(0.01)
		cls.new.clear()

	@classmethod
	def _get_key(cls):
		"""Get a key or escape sequence from stdin, convert to readable format and save to keys list. Meant to be run in it's own thread."""
		input_key: str = ""
		clean_key: str = ""
		try:
			while not cls.stopping:
				with Raw(sys.stdin):
					if not select([sys.stdin], [], [], 0.1)[0]:			#* Wait 100ms for input on stdin then restart loop to check for stop flag
						continue
					input_key += sys.stdin.read(1)						#* Read 1 key safely with blocking on
					if input_key == "\033":								#* If first character is a escape sequence keep reading
						cls.idle.clear()								#* Report IO block in progress to prevent Draw functions from getting a IO Block error
						Draw.idle.wait()								#* Wait for Draw function to finish if busy
						with Nonblocking(sys.stdin): 					#* Set non blocking to prevent read stall
							input_key += sys.stdin.read(20)
							if input_key.startswith("\033[<"):
								_ = sys.stdin.read(1000)
						cls.idle.set()									#* Report IO blocking done
					#errlog.debug(f'{repr(input_key)}')
					if input_key == "\033":	clean_key = "escape"		#* Key is "escape" key if only containing \033
					elif input_key.startswith(("\033[<0;", "\033[<35;", "\033[<64;", "\033[<65;")): #* Detected mouse event
						try:
							cls.mouse_pos = (int(input_key.split(";")[1]), int(input_key.split(";")[2].rstrip("mM")))
						except:
							pass
						else:
							if input_key.startswith("\033[<35;"):		#* Detected mouse move in mouse direct mode
									cls.mouse_move.set()
									cls.new.set()
							elif input_key.startswith("\033[<64;"):		#* Detected mouse scroll up
								clean_key = "mouse_scroll_up"
							elif input_key.startswith("\033[<65;"):		#* Detected mouse scroll down
								clean_key = "mouse_scroll_down"
							elif input_key.startswith("\033[<0;") and input_key.endswith("m"): #* Detected mouse click release
								if Menu.active:
									clean_key = "mouse_click"
								else:
									for key_name, positions in cls.mouse.items(): #* Check if mouse position is clickable
										if list(cls.mouse_pos) in positions:
											clean_key = key_name
											break
									else:
										clean_key = "mouse_click"
					elif input_key == "\\": clean_key = "\\"			#* Clean up "\" to not return escaped
					else:
						for code in cls.escape.keys():					#* Go trough dict of escape codes to get the cleaned key name
							if input_key.lstrip("\033").startswith(code):
								clean_key = cls.escape[code]
								break
						else:											#* If not found in escape dict and length of key is 1, assume regular character
							if len(input_key) == 1:
								clean_key = input_key
					if clean_key:
						cls.list.append(clean_key)						#* Store up to 10 keys in input queue for later processing
						if len(cls.list) > 10: del cls.list[0]
						clean_key = ""
						cls.new.set()									#* Set threading event to interrupt main thread sleep
					input_key = ""


		except Exception as e:
			errlog.exception(f'Input thread failed with exception: {e}')
			cls.idle.set()
			cls.list.clear()
			clean_quit(1, thread=True)

class Draw:
	'''Holds the draw buffer and manages IO blocking queue
	* .buffer([+]name[!], *args, append=False, now=False, z=100) : Add *args to buffer
	* - Adding "+" prefix to name sets append to True and appends to name's current string
	* - Adding "!" suffix to name sets now to True and print name's current string
	* .out(clear=False) : Print all strings in buffer, clear=True clear all buffers after
	* .now(*args) : Prints all arguments as a string
	* .clear(*names) : Clear named buffers, all if no argument
	* .last_screen() : Prints all saved buffers
	'''
	strings: Dict[str, str] = {}
	z_order: Dict[str, int] = {}
	saved: Dict[str, str] = {}
	save: Dict[str, bool] = {}
	once: Dict[str, bool] = {}
	idle = threading.Event()
	idle.set()

	@classmethod
	def now(cls, *args):
		'''Wait for input reader and self to be idle then print to screen'''
		Key.idle.wait()
		cls.idle.wait()
		cls.idle.clear()
		try:
			print(*args, sep="", end="", flush=True)
		except BlockingIOError:
			pass
			Key.idle.wait()
			print(*args, sep="", end="", flush=True)
		cls.idle.set()

	@classmethod
	def buffer(cls, name: str, *args: str, append: bool = False, now: bool = False, z: int = 100, only_save: bool = False, no_save: bool = False, once: bool = False):
		string: str = ""
		if name.startswith("+"):
			name = name.lstrip("+")
			append = True
		if name.endswith("!"):
			name = name.rstrip("!")
			now = True
		cls.save[name] = not no_save
		cls.once[name] = once
		if not name in cls.z_order or z != 100: cls.z_order[name] = z
		if args: string = "".join(args)
		if only_save:
			if name not in cls.saved or not append: cls.saved[name] = ""
			cls.saved[name] += string
		else:
			if name not in cls.strings or not append: cls.strings[name] = ""
			cls.strings[name] += string
			if now:
				cls.out(name)

	@classmethod
	def out(cls, *names: str, clear = False):
		out: str = ""
		if not cls.strings: return
		if names:
			for name in sorted(cls.z_order, key=cls.z_order.get, reverse=True): #type: ignore
				if name in names and name in cls.strings:
					out += cls.strings[name]
					if cls.save[name]:
						cls.saved[name] = cls.strings[name]
					if clear or cls.once[name]:
						cls.clear(name)
			cls.now(out)
		else:
			for name in sorted(cls.z_order, key=cls.z_order.get, reverse=True): #type: ignore
				if name in cls.strings:
					out += cls.strings[name]
					if cls.save[name]:
						cls.saved[name] = cls.strings[name]
					if cls.once[name] and not clear:
						cls.clear(name)
			if clear:
				cls.clear()
			cls.now(out)

	@classmethod
	def saved_buffer(cls) -> str:
		out: str = ""
		for name in sorted(cls.z_order, key=cls.z_order.get, reverse=True): #type: ignore
			if name in cls.saved:
				out += cls.saved[name]
		return out


	@classmethod
	def clear(cls, *names, saved: bool = False):
		if names:
			for name in names:
				if name in cls.strings:
					del cls.strings[name]
				if name in cls.save:
					del cls.save[name]
				if name in cls.once:
					del cls.once[name]
				if saved:
					if name in cls.saved:
						del cls.saved[name]
					if name in cls.z_order:
						del cls.z_order[name]
		else:
			cls.strings = {}
			cls.save = {}
			cls.once = {}
			if saved:
				cls.saved = {}
				cls.z_order = {}

class Color:
	'''Holds representations for a 24-bit color value
	__init__(color, depth="fg", default=False)
	-- color accepts 6 digit hexadecimal: string "#RRGGBB", 2 digit hexadecimal: string "#FF" or decimal RGB "255 255 255" as a string.
	-- depth accepts "fg" or "bg"
	__call__(*args) joins str arguments to a string and apply color
	__str__ returns escape sequence to set color
	__iter__ returns iteration over red, green and blue in integer values of 0-255.
	* Values:  .hexa: str  |  .dec: Tuple[int, int, int]  |  .red: int  |  .green: int  |  .blue: int  |  .depth: str  |  .escape: str
	'''
	hexa: str; dec: Tuple[int, int, int]; red: int; green: int; blue: int; depth: str; escape: str; default: bool

	def __init__(self, color: str, depth: str = "fg", default: bool = False):
		self.depth = depth
		self.default = default
		try:
			if not color:
				self.dec = (-1, -1, -1)
				self.hexa = ""
				self.red = self.green = self.blue = -1
				self.escape = "\033[49m" if depth == "bg" and default else ""
				return

			elif color.startswith("#"):
				self.hexa = color
				if len(self.hexa) == 3:
					self.hexa += self.hexa[1:3] + self.hexa[1:3]
					c = int(self.hexa[1:3], base=16)
					self.dec = (c, c, c)
				elif len(self.hexa) == 7:
					self.dec = (int(self.hexa[1:3], base=16), int(self.hexa[3:5], base=16), int(self.hexa[5:7], base=16))
				else:
					raise ValueError(f'Incorrectly formatted hexadecimal rgb string: {self.hexa}')

			else:
				c_t = tuple(map(int, color.split(" ")))
				if len(c_t) == 3:
					self.dec = c_t #type: ignore
				else:
					raise ValueError(f'RGB dec should be "0-255 0-255 0-255"')

			ct = self.dec[0] + self.dec[1] + self.dec[2]
			if ct > 255*3 or ct < 0:
				raise ValueError(f'RGB values out of range: {color}')
		except Exception as e:
			errlog.exception(str(e))
			self.escape = ""
			return

		if self.dec and not self.hexa: self.hexa = f'{hex(self.dec[0]).lstrip("0x").zfill(2)}{hex(self.dec[1]).lstrip("0x").zfill(2)}{hex(self.dec[2]).lstrip("0x").zfill(2)}'

		if self.dec and self.hexa:
			self.red, self.green, self.blue = self.dec
			self.escape = f'\033[{38 if self.depth == "fg" else 48};2;{";".join(str(c) for c in self.dec)}m'

		if not CONFIG.truecolor or LOW_COLOR:
			self.escape = f'{self.truecolor_to_256(rgb=self.dec, depth=self.depth)}'

	def __str__(self) -> str:
		return self.escape

	def __repr__(self) -> str:
		return repr(self.escape)

	def __iter__(self) -> Iterable:
		for c in self.dec: yield c

	def __call__(self, *args: str) -> str:
		if len(args) < 1: return ""
		return f'{self.escape}{"".join(args)}{getattr(Term, self.depth)}'

	@staticmethod
	def truecolor_to_256(rgb: Tuple[int, int, int], depth: str="fg") -> str:
		out: str = ""
		pre: str = f'\033[{"38" if depth == "fg" else "48"};5;'

		greyscale: Tuple[int, int, int] = ( rgb[0] // 11, rgb[1] // 11, rgb[2] // 11 )
		if greyscale[0] == greyscale[1] == greyscale[2]:
			out = f'{pre}{232 + greyscale[0]}m'
		else:
			out = f'{pre}{round(rgb[0] / 51) * 36 + round(rgb[1] / 51) * 6 + round(rgb[2] / 51) + 16}m'

		return out

	@staticmethod
	def escape_color(hexa: str = "", r: int = 0, g: int = 0, b: int = 0, depth: str = "fg") -> str:
		"""Returns escape sequence to set color
		* accepts either 6 digit hexadecimal hexa="#RRGGBB", 2 digit hexadecimal: hexa="#FF"
		* or decimal RGB: r=0-255, g=0-255, b=0-255
		* depth="fg" or "bg"
		"""
		dint: int = 38 if depth == "fg" else 48
		color: str = ""
		if hexa:
			try:
				if len(hexa) == 3:
					c = int(hexa[1:], base=16)
					if CONFIG.truecolor and not LOW_COLOR:
						color = f'\033[{dint};2;{c};{c};{c}m'
					else:
						color = f'{Color.truecolor_to_256(rgb=(c, c, c), depth=depth)}'
				elif len(hexa) == 7:
					if CONFIG.truecolor and not LOW_COLOR:
						color = f'\033[{dint};2;{int(hexa[1:3], base=16)};{int(hexa[3:5], base=16)};{int(hexa[5:7], base=16)}m'
					else:
						color = f'{Color.truecolor_to_256(rgb=(int(hexa[1:3], base=16), int(hexa[3:5], base=16), int(hexa[5:7], base=16)), depth=depth)}'
			except ValueError as e:
				errlog.exception(f'{e}')
		else:
			if CONFIG.truecolor and not LOW_COLOR:
				color = f'\033[{dint};2;{r};{g};{b}m'
			else:
				color = f'{Color.truecolor_to_256(rgb=(r, g, b), depth=depth)}'
		return color

	@classmethod
	def fg(cls, *args) -> str:
		if len(args) > 2: return cls.escape_color(r=args[0], g=args[1], b=args[2], depth="fg")
		else: return cls.escape_color(hexa=args[0], depth="fg")

	@classmethod
	def bg(cls, *args) -> str:
		if len(args) > 2: return cls.escape_color(r=args[0], g=args[1], b=args[2], depth="bg")
		else: return cls.escape_color(hexa=args[0], depth="bg")

class Colors:
	'''Standard colors for menus and dialogs'''
	default = Color("#cc")
	white = Color("#ff")
	red = Color("#bf3636")
	green = Color("#68bf36")
	blue = Color("#0fd7ff")
	yellow = Color("#db8b00")
	black_bg = Color("#00", depth="bg")
	null = Color("")

class Theme:
	'''__init__ accepts a dict containing { "color_element" : "color" }'''

	themes: Dict[str, str] = {}
	cached: Dict[str, Dict[str, str]] = { "Default" : DEFAULT_THEME }
	current: str = ""

	main_bg = main_fg = title = hi_fg = selected_bg = selected_fg = inactive_fg = proc_misc = cpu_box = mem_box = net_box = proc_box = div_line = temp_start = temp_mid = temp_end = cpu_start = cpu_mid = cpu_end = free_start = free_mid = free_end = cached_start = cached_mid = cached_end = available_start = available_mid = available_end = used_start = used_mid = used_end = download_start = download_mid = download_end = upload_start = upload_mid = upload_end = graph_text = meter_bg = process_start = process_mid = process_end = Colors.default

	gradient: Dict[str, List[str]] = {
		"temp" : [],
		"cpu" : [],
		"free" : [],
		"cached" : [],
		"available" : [],
		"used" : [],
		"download" : [],
		"upload" : [],
		"proc" : [],
		"proc_color" : [],
		"process" : [],
	}
	def __init__(self, theme: str):
		self.refresh()
		self._load_theme(theme)

	def __call__(self, theme: str):
		for k in self.gradient.keys(): self.gradient[k] = []
		self._load_theme(theme)

	def _load_theme(self, theme: str):
		tdict: Dict[str, str]
		if theme in self.cached:
			tdict = self.cached[theme]
		elif theme in self.themes:
			tdict = self._load_file(self.themes[theme])
			self.cached[theme] = tdict
		else:
			errlog.warning(f'No theme named "{theme}" found!')
			theme = "Default"
			CONFIG.color_theme = theme
			tdict = DEFAULT_THEME
		self.current = theme
		#if CONFIG.color_theme != theme: CONFIG.color_theme = theme
		if not "graph_text" in tdict and "inactive_fg" in tdict:
			tdict["graph_text"] = tdict["inactive_fg"]
		if not "meter_bg" in tdict and "inactive_fg" in tdict:
			tdict["meter_bg"] = tdict["inactive_fg"]
		if not "process_start" in tdict and "cpu_start" in tdict:
			tdict["process_start"] = tdict["cpu_start"]
			tdict["process_mid"] = tdict.get("cpu_mid", "")
			tdict["process_end"] = tdict.get("cpu_end", "")


		#* Get key names from DEFAULT_THEME dict to not leave any color unset if missing from theme dict
		for item, value in DEFAULT_THEME.items():
			default = item in ["main_fg", "main_bg"]
			depth = "bg" if item in ["main_bg", "selected_bg"] else "fg"
			if item in tdict:
				setattr(self, item, Color(tdict[item], depth=depth, default=default))
			else:
				setattr(self, item, Color(value, depth=depth, default=default))

		#* Create color gradients from one, two or three colors, 101 values indexed 0-100
		self.proc_start, self.proc_mid, self.proc_end = self.main_fg, Colors.null, self.inactive_fg
		self.proc_color_start, self.proc_color_mid, self.proc_color_end = self.inactive_fg, Colors.null, self.process_start

		rgb: Dict[str, Tuple[int, int, int]]
		colors: List[List[int]] = []
		for name in self.gradient:
			rgb = { "start" : getattr(self, f'{name}_start').dec, "mid" : getattr(self, f'{name}_mid').dec, "end" : getattr(self, f'{name}_end').dec }
			colors = [ list(getattr(self, f'{name}_start')) ]
			if rgb["end"][0] >= 0:
				r = 50 if rgb["mid"][0] >= 0 else 100
				for first, second in ["start", "mid" if r == 50 else "end"], ["mid", "end"]:
					for i in range(r):
						colors += [[rgb[first][n] + i * (rgb[second][n] - rgb[first][n]) // r for n in range(3)]]
					if r == 100:
						break
				self.gradient[name] += [ Color.fg(*color) for color in colors ]

			else:
				c = Color.fg(*rgb["start"])
				self.gradient[name] += [c] * 101
		#* Set terminal colors
		Term.fg = f'{self.main_fg}'
		Term.bg = f'{self.main_bg}' if CONFIG.theme_background else "\033[49m"
		Draw.now(self.main_fg, self.main_bg)

	@classmethod
	def refresh(cls):
		'''Sets themes dict with names and paths to all found themes'''
		cls.themes = { "Default" : "Default" }
		try:
			for d in (THEME_DIR, USER_THEME_DIR):
				if not d: continue
				for f in os.listdir(d):
					if f.endswith(".theme"):
						cls.themes[f'{"" if d == THEME_DIR else "+"}{f[:-6]}'] = f'{d}/{f}'
		except Exception as e:
			errlog.exception(str(e))

	@staticmethod
	def _load_file(path: str) -> Dict[str, str]:
		'''Load a bashtop formatted theme file and return a dict'''
		new_theme: Dict[str, str] = {}
		try:
			with open(path, "r") as f:
				for line in f:
					if not line.startswith("theme["): continue
					key = line[6:line.find("]")]
					s = line.find('"')
					value = line[s + 1:line.find('"', s + 1)]
					new_theme[key] = value
		except Exception as e:
			errlog.exception(str(e))

		return new_theme

class Banner:
	'''Holds the bpytop banner, .draw(line, [col=0], [center=False], [now=False])'''
	out: List[str] = []
	c_color: str = ""
	length: int = 0
	if not out:
		for num, (color, color2, line) in enumerate(BANNER_SRC):
			if len(line) > length: length = len(line)
			out_var = ""
			line_color = Color.fg(color)
			line_color2 = Color.fg(color2)
			line_dark = Color.fg(f'#{80 - num * 6}')
			for n, letter in enumerate(line):
				if letter == "█" and c_color != line_color:
					if 5 < n < 25: c_color = line_color2
					else: c_color = line_color
					out_var += c_color
				elif letter == " ":
					letter = f'{Mv.r(1)}'
					c_color = ""
				elif letter != "█" and c_color != line_dark:
					c_color = line_dark
					out_var += line_dark
				out_var += letter
			out.append(out_var)

	@classmethod
	def draw(cls, line: int, col: int = 0, center: bool = False, now: bool = False):
		out: str = ""
		if center: col = Term.width // 2 - cls.length // 2
		for n, o in enumerate(cls.out):
			out += f'{Mv.to(line + n, col)}{o}'
		out += f'{Term.fg}'
		if now: Draw.out(out)
		else: return out

class Symbol:
	h_line: str			= "─"
	v_line: str			= "│"
	left_up: str		= "┌"
	right_up: str		= "┐"
	left_down: str		= "└"
	right_down: str		= "┘"
	title_left: str		= "┤"
	title_right: str	= "├"
	div_up: str			= "┬"
	div_down: str		= "┴"
	graph_up: Dict[float, str] = {
	0.0 : " ", 0.1 : "⢀", 0.2 : "⢠", 0.3 : "⢰", 0.4 : "⢸",
	1.0 : "⡀", 1.1 : "⣀", 1.2 : "⣠", 1.3 : "⣰", 1.4 : "⣸",
	2.0 : "⡄", 2.1 : "⣄", 2.2 : "⣤", 2.3 : "⣴", 2.4 : "⣼",
	3.0 : "⡆", 3.1 : "⣆", 3.2 : "⣦", 3.3 : "⣶", 3.4 : "⣾",
	4.0 : "⡇", 4.1 : "⣇", 4.2 : "⣧", 4.3 : "⣷", 4.4 : "⣿"
	}
	graph_up_small = graph_up.copy()
	graph_up_small[0.0] = "\033[1C"

	graph_down: Dict[float, str] = {
	0.0 : " ", 0.1 : "⠈", 0.2 : "⠘", 0.3 : "⠸", 0.4 : "⢸",
	1.0 : "⠁", 1.1 : "⠉", 1.2 : "⠙", 1.3 : "⠹", 1.4 : "⢹",
	2.0 : "⠃", 2.1 : "⠋", 2.2 : "⠛", 2.3 : "⠻", 2.4 : "⢻",
	3.0 : "⠇", 3.1 : "⠏", 3.2 : "⠟", 3.3 : "⠿", 3.4 : "⢿",
	4.0 : "⡇", 4.1 : "⡏", 4.2 : "⡟", 4.3 : "⡿", 4.4 : "⣿"
	}
	graph_down_small = graph_down.copy()
	graph_down_small[0.0] = "\033[1C"
	meter: str = "■"
	up: str = "↑"
	down: str = "↓"
	left: str = "←"
	right: str = "→"
	enter: str = "↲"
	ok: str = f'{Color.fg("#30ff50")}√{Color.fg("#cc")}'
	fail: str = f'{Color.fg("#ff3050")}!{Color.fg("#cc")}'

class Graph:
	'''Class for creating and adding to graphs
	* __str__ : returns graph as a string
	* add(value: int) : adds a value to graph and returns it as a string
	* __call__ : same as add
	'''
	out: str
	width: int
	height: int
	graphs: Dict[bool, List[str]]
	colors: List[str]
	invert: bool
	max_value: int
	color_max_value: int
	offset: int
	no_zero: bool
	current: bool
	last: int
	symbol: Dict[float, str]

	def __init__(self, width: int, height: int, color: Union[List[str], Color, None], data: List[int], invert: bool = False, max_value: int = 0, offset: int = 0, color_max_value: Union[int, None] = None, no_zero: bool = False):
		self.graphs: Dict[bool, List[str]] = {False : [], True : []}
		self.current: bool = True
		self.width = width
		self.height = height
		self.invert = invert
		self.offset = offset
		self.no_zero = no_zero
		if not data: data = [0]
		if max_value:
			self.max_value = max_value
			data = [ min(100, (v + offset) * 100 // (max_value + offset)) for v in data ] #* Convert values to percentage values of max_value with max_value as ceiling
		else:
			self.max_value = 0
		if color_max_value:
			self.color_max_value = color_max_value
		else:
			self.color_max_value = self.max_value
		if self.color_max_value and self.max_value:
			color_scale = int(100.0 * self.max_value / self.color_max_value)
		else:
			color_scale = 100
		self.colors: List[str] = []
		if isinstance(color, list) and height > 1:
			for i in range(1, height + 1): self.colors.insert(0, color[min(100, i * color_scale // height)]) #* Calculate colors of graph
			if invert: self.colors.reverse()
		elif isinstance(color, Color) and height > 1:
			self.colors = [ f'{color}' for _ in range(height) ]
		else:
			if isinstance(color, list): self.colors = color
			elif isinstance(color, Color): self.colors = [ f'{color}' for _ in range(101) ]
		if self.height == 1:
			self.symbol = Symbol.graph_down_small if invert else Symbol.graph_up_small
		else:
			self.symbol = Symbol.graph_down if invert else Symbol.graph_up
		value_width: int = ceil(len(data) / 2)
		filler: str = ""
		if value_width > width: #* If the size of given data set is bigger then width of graph, shrink data set
			data = data[-(width*2):]
			value_width = ceil(len(data) / 2)
		elif value_width < width: #* If the size of given data set is smaller then width of graph, fill graph with whitespace
			filler = self.symbol[0.0] * (width - value_width)
		if len(data) % 2: data.insert(0, 0)
		for _ in range(height):
			for b in [True, False]:
				self.graphs[b].append(filler)
		self._create(data, new=True)

	def _create(self, data: List[int], new: bool = False):
		h_high: int
		h_low: int
		value: Dict[str, int] = { "left" : 0, "right" : 0 }
		val: int
		side: str

		#* Create the graph
		for h in range(self.height):
			h_high = round(100 * (self.height - h) / self.height) if self.height > 1 else 100
			h_low = round(100 * (self.height - (h + 1)) / self.height) if self.height > 1 else 0
			for v in range(len(data)):
				if new: self.current = bool(v % 2) #* Switch between True and False graphs
				if new and v == 0: self.last = 0
				for val, side in [self.last, "left"], [data[v], "right"]: # type: ignore
					if val >= h_high:
						value[side] = 4
					elif val <= h_low:
						value[side] = 0
					else:
						if self.height == 1: value[side] = round(val * 4 / 100 + 0.5)
						else: value[side] = round((val - h_low) * 4 / (h_high - h_low) + 0.1)
					if self.no_zero and not (new and v == 0 and side == "left") and h == self.height - 1 and value[side] < 1: value[side] = 1
				if new: self.last = data[v]
				self.graphs[self.current][h] += self.symbol[float(value["left"] + value["right"] / 10)]
		if data: self.last = data[-1]
		self.out = ""

		if self.height == 1:
			self.out += f'{"" if not self.colors else (THEME.inactive_fg if self.last < 5 else self.colors[self.last])}{self.graphs[self.current][0]}'
		elif self.height > 1:
			for h in range(self.height):
				if h > 0: self.out += f'{Mv.d(1)}{Mv.l(self.width)}'
				self.out += f'{"" if not self.colors else self.colors[h]}{self.graphs[self.current][h if not self.invert else (self.height - 1) - h]}'
		if self.colors: self.out += f'{Term.fg}'

	def __call__(self, value: Union[int, None] = None) -> str:
		if not isinstance(value, int): return self.out
		self.current = not self.current
		if self.height == 1:
			if self.graphs[self.current][0].startswith(self.symbol[0.0]):
				self.graphs[self.current][0] = self.graphs[self.current][0].replace(self.symbol[0.0], "", 1)
			else:
				self.graphs[self.current][0] = self.graphs[self.current][0][1:]
		else:
			for n in range(self.height):
				self.graphs[self.current][n] = self.graphs[self.current][n][1:]
		if self.max_value: value = (value + self.offset) * 100 // (self.max_value + self.offset) if value < self.max_value else 100
		self._create([value])
		return self.out

	def add(self, value: Union[int, None] = None) -> str:
		return self.__call__(value)

	def __str__(self):
		return self.out

	def __repr__(self):
		return repr(self.out)


class Graphs:
	'''Holds all graphs and lists of graphs for dynamically created graphs'''
	cpu: Dict[str, Graph] = {}
	cores: List[Graph] = [NotImplemented] * THREADS
	temps: List[Graph] = [NotImplemented] * (THREADS + 1)
	net: Dict[str, Graph] = {}
	detailed_cpu: Graph = NotImplemented
	detailed_mem: Graph = NotImplemented
	pid_cpu: Dict[int, Graph] = {}
	disk_io: Dict[str, Dict[str, Graph]] = {}

class Meter:
	'''Creates a percentage meter
	__init__(value, width, theme, gradient_name) to create new meter
	__call__(value) to set value and return meter as a string
	__str__ returns last set meter as a string
	'''
	out: str
	color_gradient: List[str]
	color_inactive: Color
	gradient_name: str
	width: int
	invert: bool
	saved: Dict[int, str]

	def __init__(self, value: int, width: int, gradient_name: str, invert: bool = False):
		self.gradient_name = gradient_name
		self.color_gradient = THEME.gradient[gradient_name]
		self.color_inactive = THEME.meter_bg
		self.width = width
		self.saved = {}
		self.invert = invert
		self.out = self._create(value)

	def __call__(self, value: Union[int, None]) -> str:
		if not isinstance(value, int): return self.out
		if value > 100: value = 100
		elif value < 0: value = 100
		if value in self.saved:
			self.out = self.saved[value]
		else:
			self.out = self._create(value)
		return self.out

	def __str__(self) -> str:
		return self.out

	def __repr__(self):
		return repr(self.out)

	def _create(self, value: int) -> str:
		if value > 100: value = 100
		elif value < 0: value = 100
		out: str = ""
		for i in range(1, self.width + 1):
			if value >= round(i * 100 / self.width):
				out += f'{self.color_gradient[round(i * 100 / self.width) if not self.invert else round(100 - (i * 100 / self.width))]}{Symbol.meter}'
			else:
				out += self.color_inactive(Symbol.meter * (self.width + 1 - i))
				break
		else:
			out += f'{Term.fg}'
		if not value in self.saved:
			self.saved[value] = out
		return out

class Meters:
	cpu: Meter
	battery: Meter
	mem: Dict[str, Union[Meter, Graph]] = {}
	swap: Dict[str, Union[Meter, Graph]] = {}
	disks_used: Dict[str, Meter] = {}
	disks_free: Dict[str, Meter] = {}

class Box:
	'''Box class with all needed attributes for create_box() function'''
	name: str
	num: int = 0
	boxes: List = []
	view_modes: Dict[str, List] = {"full" : ["cpu", "mem", "net", "proc"], "stat" : ["cpu", "mem", "net"], "proc" : ["cpu", "proc"]}
	view_mode: str
	for view_mode in view_modes:
		if sorted(CONFIG.shown_boxes.split(), key=str.lower) == view_modes[view_mode]:
			break
	else:
		view_mode = "user"
		view_modes["user"] = CONFIG.shown_boxes.split()
	height_p: int
	width_p: int
	x: int
	y: int
	width: int
	height: int
	out: str
	bg: str
	_b_cpu_h: int
	_b_mem_h: int
	redraw_all: bool
	buffers: List[str] = []
	clock_on: bool = False
	clock: str = ""
	clock_len: int = 0
	resized: bool = False
	clock_custom_format: Dict[str, Any] = {
		"/host" : os.uname()[1],
		"/user" : os.environ.get("USER") or pwd.getpwuid(os.getuid())[0],
		"/uptime" : "",
		}
	if clock_custom_format["/host"].endswith(".local"):
		clock_custom_format["/host"] = clock_custom_format["/host"].replace(".local", "")

	@classmethod
	def calc_sizes(cls):
		'''Calculate sizes of boxes'''
		cls.boxes = CONFIG.shown_boxes.split()
		for sub in cls.__subclasses__():
			sub._calc_size() # type: ignore
			sub.resized = True # type: ignore

	@classmethod
	def draw_update_ms(cls, now: bool = True):
		if not "cpu" in cls.boxes: return
		update_string: str = f'{CONFIG.update_ms}ms'
		xpos: int = CpuBox.x + CpuBox.width - len(update_string) - 15
		if not "+" in Key.mouse:
			Key.mouse["+"] = [[xpos + 7 + i, CpuBox.y] for i in range(3)]
			Key.mouse["-"] = [[CpuBox.x + CpuBox.width - 4 + i, CpuBox.y] for i in range(3)]
		Draw.buffer("update_ms!" if now and not Menu.active else "update_ms",
			f'{Mv.to(CpuBox.y, xpos)}{THEME.cpu_box(Symbol.h_line * 7, Symbol.title_left)}{Fx.b}{THEME.hi_fg("+")} ',
			f'{THEME.title(update_string)} {THEME.hi_fg("-")}{Fx.ub}{THEME.cpu_box(Symbol.title_right)}', only_save=Menu.active, once=True)
		if now and not Menu.active:
			Draw.clear("update_ms")
			if CONFIG.show_battery and hasattr(psutil, "sensors_battery") and psutil.sensors_battery():
				Draw.out("battery")

	@classmethod
	def draw_clock(cls, force: bool = False):
		if not "cpu" in cls.boxes or not cls.clock_on: return
		out: str = ""
		if force: pass
		elif Term.resized or strftime(CONFIG.draw_clock) == cls.clock: return
		clock_string = cls.clock = strftime(CONFIG.draw_clock)
		for custom in cls.clock_custom_format:
			if custom in clock_string:
				if custom == "/uptime": cls.clock_custom_format["/uptime"] = CpuCollector.uptime
				clock_string = clock_string.replace(custom, cls.clock_custom_format[custom])
		clock_len = len(clock_string[:(CpuBox.width-56)])
		if cls.clock_len != clock_len and not CpuBox.resized:
			out = f'{Mv.to(CpuBox.y, ((CpuBox.width)//2)-(cls.clock_len//2))}{Fx.ub}{THEME.cpu_box}{Symbol.h_line * cls.clock_len}'
		cls.clock_len = clock_len
		now: bool = False if Menu.active else not force
		out += (f'{Mv.to(CpuBox.y, ((CpuBox.width)//2)-(clock_len//2))}{Fx.ub}{THEME.cpu_box}'
			f'{Symbol.title_left}{Fx.b}{THEME.title(clock_string[:clock_len])}{Fx.ub}{THEME.cpu_box}{Symbol.title_right}{Term.fg}')
		Draw.buffer("clock", out, z=1, now=now, once=not force, only_save=Menu.active)
		if now and not Menu.active:
			if CONFIG.show_battery and hasattr(psutil, "sensors_battery") and psutil.sensors_battery():
				Draw.out("battery")

	@classmethod
	def empty_bg(cls) -> str:
		return (f'{Term.clear}' +
				(f'{Banner.draw(Term.height // 2 - 10, center=True)}'
				f'{Mv.d(1)}{Mv.l(46)}{Colors.black_bg}{Colors.default}{Fx.b}[esc] Menu'
				f'{Mv.r(25)}{Fx.i}Version: {VERSION}{Fx.ui}' if Term.height > 22 else "") +
				f'{Mv.d(1)}{Mv.l(34)}{Fx.b}All boxes hidden!'
				f'{Mv.d(1)}{Mv.l(17)}{Fx.b}[1] {Fx.ub}Toggle CPU box'
				f'{Mv.d(1)}{Mv.l(18)}{Fx.b}[2] {Fx.ub}Toggle MEM box'
				f'{Mv.d(1)}{Mv.l(18)}{Fx.b}[3] {Fx.ub}Toggle NET box'
				f'{Mv.d(1)}{Mv.l(18)}{Fx.b}[4] {Fx.ub}Toggle PROC box'
				f'{Mv.d(1)}{Mv.l(19)}{Fx.b}[m] {Fx.ub}Cycle presets'
				f'{Mv.d(1)}{Mv.l(17)}{Fx.b}[q] Quit {Fx.ub}{Term.bg}{Term.fg}')

	@classmethod
	def draw_bg(cls, now: bool = True):
		'''Draw all boxes outlines and titles'''
		out: str = ""
		if not cls.boxes:
			out = cls.empty_bg()
		else:
			out = "".join(sub._draw_bg() for sub in cls.__subclasses__()) # type: ignore
		Draw.buffer("bg", out, now=now, z=1000, only_save=Menu.active, once=True)
		cls.draw_update_ms(now=now)
		if CONFIG.draw_clock: cls.draw_clock(force=True)

class SubBox:
	box_x: int = 0
	box_y: int = 0
	box_width: int = 0
	box_height: int = 0
	box_columns: int = 0
	column_size: int = 0

class CpuBox(Box, SubBox):
	name = "cpu"
	num = 1
	x = 1
	y = 1
	height_p = 32
	width_p = 100
	min_w: int = 60
	min_h: int = 8
	resized: bool = True
	redraw: bool = False
	buffer: str = "cpu"
	battery_percent: int = 1000
	battery_secs: int = 0
	battery_status: str = "Unknown"
	old_battery_pos = 0
	old_battery_len = 0
	battery_path: Union[str, None] = ""
	battery_clear: bool = False
	battery_symbols: Dict[str, str] = {"Charging": "▲",
									"Discharging": "▼",
									"Full": "■",
									"Not charging": "■"}
	clock_block: bool = True
	Box.buffers.append(buffer)

	@classmethod
	def _calc_size(cls):
		if not "cpu" in cls.boxes:
			Box._b_cpu_h = 0
			cls.width = Term.width
			return
		cpu = CpuCollector
		height_p: int
		if cls.boxes == ["cpu"]:
			height_p = 100
		else:
			height_p = cls.height_p
		cls.width = round(Term.width * cls.width_p / 100)
		cls.height = round(Term.height * height_p / 100)
		if cls.height < 8: cls.height = 8
		Box._b_cpu_h = cls.height
		#THREADS = 64
		cls.box_columns = ceil((THREADS + 1) / (cls.height - 5))
		if cls.box_columns * (20 + 13 if cpu.got_sensors else 21) < cls.width - (cls.width // 3):
			cls.column_size = 2
			cls.box_width = (20 + 13 if cpu.got_sensors else 21) * cls.box_columns - ((cls.box_columns - 1) * 1)
		elif cls.box_columns * (15 + 6 if cpu.got_sensors else 15) < cls.width - (cls.width // 3):
			cls.column_size = 1
			cls.box_width = (15 + 6 if cpu.got_sensors else 15) * cls.box_columns - ((cls.box_columns - 1) * 1)
		elif cls.box_columns * (8 + 6 if cpu.got_sensors else 8) < cls.width - (cls.width // 3):
			cls.column_size = 0
		else:
			cls.box_columns = (cls.width - cls.width // 3) // (8 + 6 if cpu.got_sensors else 8); cls.column_size = 0

		if cls.column_size == 0: cls.box_width = (8 + 6 if cpu.got_sensors else 8) * cls.box_columns + 1

		cls.box_height = ceil(THREADS / cls.box_columns) + 4

		if cls.box_height > cls.height - 2: cls.box_height = cls.height - 2
		cls.box_x = (cls.width - 1) - cls.box_width
		cls.box_y = cls.y + ceil((cls.height - 2) / 2) - ceil(cls.box_height / 2) + 1

	@classmethod
	def _draw_bg(cls) -> str:
		if not "cpu" in cls.boxes: return ""
		if not "M" in Key.mouse:
			Key.mouse["M"] = [[cls.x + 10 + i, cls.y] for i in range(6)]
		return (f'{create_box(box=cls, line_color=THEME.cpu_box)}'
		f'{Mv.to(cls.y, cls.x + 10)}{THEME.cpu_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg("M")}{THEME.title("enu")}{Fx.ub}{THEME.cpu_box(Symbol.title_right)}'
		f'{create_box(x=cls.box_x, y=cls.box_y, width=cls.box_width, height=cls.box_height, line_color=THEME.div_line, fill=False, title=CPU_NAME[:cls.box_width - 14] if not CONFIG.custom_cpu_name else CONFIG.custom_cpu_name[:cls.box_width - 14])}')

	@classmethod
	def battery_activity(cls) -> bool:
		if not hasattr(psutil, "sensors_battery") or psutil.sensors_battery() == None:
			if cls.battery_percent != 1000:
				cls.battery_clear = True
			return False

		if cls.battery_path == "":
			cls.battery_path = None
			if os.path.isdir("/sys/class/power_supply"):
				for directory in sorted(os.listdir("/sys/class/power_supply")):
					if directory.startswith('BAT') or 'battery' in directory.lower():
						cls.battery_path = f'/sys/class/power_supply/{directory}/'
						break

		return_true: bool = False
		percent: int = ceil(getattr(psutil.sensors_battery(), "percent", 0))
		if percent != cls.battery_percent:
			cls.battery_percent = percent
			return_true = True

		seconds: int = getattr(psutil.sensors_battery(), "secsleft", 0)
		if seconds != cls.battery_secs:
			cls.battery_secs = seconds
			return_true = True

		status: str = "not_set"
		if cls.battery_path:
			status = readfile(cls.battery_path + "status", default="not_set")
		if status == "not_set" and getattr(psutil.sensors_battery(), "power_plugged", None) == True:
			status = "Charging" if cls.battery_percent < 100 else "Full"
		elif status == "not_set" and getattr(psutil.sensors_battery(), "power_plugged", None) == False:
			status = "Discharging"
		elif status == "not_set":
			status = "Unknown"
		if status != cls.battery_status:
			cls.battery_status = status
			return_true = True

		return return_true or cls.resized or cls.redraw or Menu.active

	@classmethod
	def _draw_fg(cls):
		if not "cpu" in cls.boxes: return
		cpu = CpuCollector
		if cpu.redraw: cls.redraw = True
		out: str = ""
		out_misc: str = ""
		lavg: str = ""
		x, y, w, h = cls.x + 1, cls.y + 1, cls.width - 2, cls.height - 2
		bx, by, bw, bh = cls.box_x + 1, cls.box_y + 1, cls.box_width - 2, cls.box_height - 2
		hh: int = ceil(h / 2)
		hh2: int = h - hh
		mid_line: bool = False
		if not CONFIG.cpu_single_graph and CONFIG.cpu_graph_upper != CONFIG.cpu_graph_lower:
			mid_line = True
			if h % 2: hh = floor(h / 2)
			else: hh2 -= 1

		hide_cores: bool = (cpu.cpu_temp_only or not CONFIG.show_coretemp) and cpu.got_sensors
		ct_width: int = (max(6, 6 * cls.column_size)) * hide_cores

		if cls.resized or cls.redraw:
			if not "m" in Key.mouse:
				Key.mouse["m"] = [[cls.x + 16 + i, cls.y] for i in range(12)]
			out_misc += f'{Mv.to(cls.y, cls.x + 16)}{THEME.cpu_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg("m")}{THEME.title}ode:{Box.view_mode}{Fx.ub}{THEME.cpu_box(Symbol.title_right)}'
			Graphs.cpu["up"] = Graph(w - bw - 3, (h if CONFIG.cpu_single_graph else hh), THEME.gradient["cpu"], cpu.cpu_upper)
			if not CONFIG.cpu_single_graph:
				Graphs.cpu["down"] = Graph(w - bw - 3, hh2, THEME.gradient["cpu"], cpu.cpu_lower, invert=CONFIG.cpu_invert_lower)
			Meters.cpu = Meter(cpu.cpu_usage[0][-1], bw - (21 if cpu.got_sensors else 9), "cpu")
			if cls.column_size > 0 or ct_width > 0:
				for n in range(THREADS):
					Graphs.cores[n] = Graph(5 * cls.column_size + ct_width, 1, None, cpu.cpu_usage[n + 1])
			if cpu.got_sensors:
				Graphs.temps[0] = Graph(5, 1, None, cpu.cpu_temp[0], max_value=cpu.cpu_temp_crit, offset=-23)
				if cls.column_size > 1:
					for n in range(1, THREADS + 1):
						if not cpu.cpu_temp[n]:
							continue
						Graphs.temps[n] = Graph(5, 1, None, cpu.cpu_temp[n], max_value=cpu.cpu_temp_crit, offset=-23)
			Draw.buffer("cpu_misc", out_misc, only_save=True)

		if CONFIG.show_battery and cls.battery_activity():
			bat_out: str = ""
			if cls.battery_secs > 0:
				battery_time: str = f' {cls.battery_secs // 3600:02}:{(cls.battery_secs % 3600) // 60:02}'
			else:
				battery_time = ""
			if not hasattr(Meters, "battery") or cls.resized:
				Meters.battery = Meter(cls.battery_percent, 10, "cpu", invert=True)
			battery_symbol: str = cls.battery_symbols.get(cls.battery_status, "○")
			battery_len: int = len(f'{CONFIG.update_ms}') + (11 if cls.width >= 100 else 0) + len(battery_time) + len(f'{cls.battery_percent}')
			battery_pos = cls.width - battery_len - 17
			if (battery_pos != cls.old_battery_pos or battery_len != cls.old_battery_len) and cls.old_battery_pos > 0 and not cls.resized:
				bat_out += f'{Mv.to(y-1, cls.old_battery_pos)}{THEME.cpu_box(Symbol.h_line*(cls.old_battery_len+4))}'
			cls.old_battery_pos, cls.old_battery_len = battery_pos, battery_len
			bat_out += (f'{Mv.to(y-1, battery_pos)}{THEME.cpu_box(Symbol.title_left)}{Fx.b}{THEME.title}BAT{battery_symbol} {cls.battery_percent}%'+
				("" if cls.width < 100 else f' {Fx.ub}{Meters.battery(cls.battery_percent)}{Fx.b}') +
				f'{THEME.title}{battery_time}{Fx.ub}{THEME.cpu_box(Symbol.title_right)}')
			Draw.buffer("battery", f'{bat_out}{Term.fg}', only_save=Menu.active)
		elif cls.battery_clear:
			out += f'{Mv.to(y-1, cls.old_battery_pos)}{THEME.cpu_box(Symbol.h_line*(cls.old_battery_len+4))}'
			cls.battery_clear = False
			cls.battery_percent = 1000
			cls.battery_secs = 0
			cls.battery_status = "Unknown"
			cls.old_battery_pos = 0
			cls.old_battery_len = 0
			cls.battery_path = ""
			Draw.clear("battery", saved=True)

		cx = cy = cc = 0
		ccw = (bw + 1) // cls.box_columns
		if cpu.cpu_freq:
			freq: str = f'{cpu.cpu_freq} Mhz' if cpu.cpu_freq < 1000 else f'{float(cpu.cpu_freq / 1000):.1f} GHz'
			out += f'{Mv.to(by - 1, bx + bw - 9)}{THEME.div_line(Symbol.title_left)}{Fx.b}{THEME.title(freq)}{Fx.ub}{THEME.div_line(Symbol.title_right)}'
		out += f'{Mv.to(y, x)}{Graphs.cpu["up"](None if cls.resized else cpu.cpu_upper[-1])}'
		if mid_line:
			out += (f'{Mv.to(y+hh, x-1)}{THEME.cpu_box(Symbol.title_right)}{THEME.div_line}{Symbol.h_line * (w - bw - 3)}{THEME.div_line(Symbol.title_left)}'
					f'{Mv.to(y+hh, x+((w-bw)//2)-((len(CONFIG.cpu_graph_upper)+len(CONFIG.cpu_graph_lower))//2)-4)}{THEME.main_fg}{CONFIG.cpu_graph_upper}{Mv.r(1)}▲▼{Mv.r(1)}{CONFIG.cpu_graph_lower}')
		if not CONFIG.cpu_single_graph and Graphs.cpu.get("down"):
			out += f'{Mv.to(y + hh + (1 * mid_line), x)}{Graphs.cpu["down"](None if cls.resized else cpu.cpu_lower[-1])}'
		out += (f'{THEME.main_fg}{Mv.to(by + cy, bx + cx)}{Fx.b}{"CPU "}{Fx.ub}{Meters.cpu(cpu.cpu_usage[0][-1])}'
				f'{THEME.gradient["cpu"][cpu.cpu_usage[0][-1]]}{cpu.cpu_usage[0][-1]:>4}{THEME.main_fg}%')
		if cpu.got_sensors:
			try:
				out += (f'{THEME.inactive_fg} ⡀⡀⡀⡀⡀{Mv.l(5)}{THEME.gradient["temp"][min_max(cpu.cpu_temp[0][-1], 0, cpu.cpu_temp_crit) * 100 // cpu.cpu_temp_crit]}{Graphs.temps[0](None if cls.resized else cpu.cpu_temp[0][-1])}'
						f'{cpu.cpu_temp[0][-1]:>4}{THEME.main_fg}°C')
			except:
				cpu.got_sensors = False

		cy += 1
		for n in range(1, THREADS + 1):
			out += f'{THEME.main_fg}{Mv.to(by + cy, bx + cx)}{Fx.b + "C" + Fx.ub if THREADS < 100 else ""}{str(n):<{2 if cls.column_size == 0 else 3}}'
			if cls.column_size > 0 or ct_width > 0:
				out += f'{THEME.inactive_fg}{"⡀" * (5 * cls.column_size + ct_width)}{Mv.l(5 * cls.column_size + ct_width)}{THEME.gradient["cpu"][cpu.cpu_usage[n][-1]]}{Graphs.cores[n-1](None if cls.resized else cpu.cpu_usage[n][-1])}'
			else:
				out += f'{THEME.gradient["cpu"][cpu.cpu_usage[n][-1]]}'
			out += f'{cpu.cpu_usage[n][-1]:>{3 if cls.column_size < 2 else 4}}{THEME.main_fg}%'
			if cpu.got_sensors and cpu.cpu_temp[n] and not hide_cores:
				try:
					if cls.column_size > 1:
						out += f'{THEME.inactive_fg} ⡀⡀⡀⡀⡀{Mv.l(5)}{THEME.gradient["temp"][100 if cpu.cpu_temp[n][-1] >= cpu.cpu_temp_crit else (cpu.cpu_temp[n][-1] * 100 // cpu.cpu_temp_crit)]}{Graphs.temps[n](None if cls.resized else cpu.cpu_temp[n][-1])}'
					else:
						out += f'{THEME.gradient["temp"][100 if cpu.cpu_temp[n][-1] >= cpu.cpu_temp_crit else (cpu.cpu_temp[n][-1] * 100 // cpu.cpu_temp_crit)]}'
					out += f'{cpu.cpu_temp[n][-1]:>4}{THEME.main_fg}°C'
				except:
					cpu.got_sensors = False
			elif cpu.got_sensors and not hide_cores:
				out += f'{Mv.r(max(6, 6 * cls.column_size))}'
			out += f'{THEME.div_line(Symbol.v_line)}'
			cy += 1
			if cy > ceil(THREADS/cls.box_columns) and n != THREADS:
				cc += 1; cy = 1; cx = ccw * cc
				if cc == cls.box_columns: break

		if cy < bh - 1: cy = bh - 1

		if cy < bh and cc < cls.box_columns:
			if cls.column_size == 2 and cpu.got_sensors:
				lavg = f' Load AVG:  {"   ".join(str(l) for l in cpu.load_avg):^19.19}'
			elif cls.column_size == 2 or (cls.column_size == 1 and cpu.got_sensors):
				lavg = f'LAV: {" ".join(str(l) for l in cpu.load_avg):^14.14}'
			elif cls.column_size == 1 or (cls.column_size == 0 and cpu.got_sensors):
				lavg = f'L {" ".join(str(round(l, 1)) for l in cpu.load_avg):^11.11}'
			else:
				lavg = f'{" ".join(str(round(l, 1)) for l in cpu.load_avg[:2]):^7.7}'
			out += f'{Mv.to(by + cy, bx + cx)}{THEME.main_fg}{lavg}{THEME.div_line(Symbol.v_line)}'

		if CONFIG.show_uptime:
			out += f'{Mv.to(y + (0 if not CONFIG.cpu_invert_lower or CONFIG.cpu_single_graph else h - 1), x + 1)}{THEME.graph_text}{Fx.trans("up " + cpu.uptime)}'


		Draw.buffer(cls.buffer, f'{out_misc}{out}{Term.fg}', only_save=Menu.active)
		cls.resized = cls.redraw = cls.clock_block = False

class MemBox(Box):
	name = "mem"
	num = 2
	height_p = 38
	width_p = 45
	min_w: int = 36
	min_h: int = 10
	x = 1
	y = 1
	mem_meter: int = 0
	mem_size: int = 0
	disk_meter: int = 0
	divider: int = 0
	mem_width: int = 0
	disks_width: int = 0
	disks_io_h: int = 0
	disks_io_order: List[str] = []
	graph_speeds: Dict[str, int] = {}
	graph_height: int
	resized: bool = True
	redraw: bool = False
	buffer: str = "mem"
	swap_on: bool = CONFIG.show_swap
	Box.buffers.append(buffer)
	mem_names: List[str] = ["used", "available", "cached", "free"]
	swap_names: List[str] = ["used", "free"]

	@classmethod
	def _calc_size(cls):
		if not "mem" in cls.boxes:
			Box._b_mem_h = 0
			cls.width = Term.width
			return
		width_p: int; height_p: int
		if not "proc" in cls.boxes:
			width_p = 100
		else:
			width_p = cls.width_p

		if not "cpu" in cls.boxes:
			height_p = 60 if "net" in cls.boxes else 98
		elif not "net" in cls.boxes:
			height_p = 98 - CpuBox.height_p
		else:
			height_p = cls.height_p

		cls.width = round(Term.width * width_p / 100)
		cls.height = round(Term.height * height_p / 100) + 1
		if cls.height + Box._b_cpu_h > Term.height: cls.height = Term.height - Box._b_cpu_h
		Box._b_mem_h = cls.height
		cls.y = Box._b_cpu_h + 1
		if CONFIG.show_disks:
			cls.mem_width = ceil((cls.width - 3) / 2)
			cls.disks_width = cls.width - cls.mem_width - 3
			if cls.mem_width + cls.disks_width < cls.width - 2: cls.mem_width += 1
			cls.divider = cls.x + cls.mem_width
		else:
			cls.mem_width = cls.width - 1

		item_height: int = 6 if cls.swap_on and not CONFIG.swap_disk else 4
		if cls.height - (3 if cls.swap_on and not CONFIG.swap_disk else 2) > 2 * item_height: cls.mem_size = 3
		elif cls.mem_width > 25: cls.mem_size = 2
		else: cls.mem_size = 1

		cls.mem_meter = cls.width - (cls.disks_width if CONFIG.show_disks else 0) - (9 if cls.mem_size > 2 else 20)
		if cls.mem_size == 1: cls.mem_meter += 6
		if cls.mem_meter < 1: cls.mem_meter = 0

		if CONFIG.mem_graphs:
			cls.graph_height = round(((cls.height - (2 if cls.swap_on and not CONFIG.swap_disk else 1)) - (2 if cls.mem_size == 3 else 1) * item_height) / item_height)
			if cls.graph_height == 0: cls.graph_height = 1
			if cls.graph_height > 1: cls.mem_meter += 6
		else:
			cls.graph_height = 0

		if CONFIG.show_disks:
			cls.disk_meter = cls.width - cls.mem_width - 23
			if cls.disks_width < 25:
				cls.disk_meter += 10
			if cls.disk_meter < 1: cls.disk_meter = 0

	@classmethod
	def _draw_bg(cls) -> str:
		if not "mem" in cls.boxes: return ""
		out: str = ""
		out += f'{create_box(box=cls, line_color=THEME.mem_box)}'
		if CONFIG.show_disks:
			out += (f'{Mv.to(cls.y, cls.divider + 2)}{THEME.mem_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg("d")}{THEME.title("isks")}{Fx.ub}{THEME.mem_box(Symbol.title_right)}'
					f'{Mv.to(cls.y, cls.divider)}{THEME.mem_box(Symbol.div_up)}'
					f'{Mv.to(cls.y + cls.height - 1, cls.divider)}{THEME.mem_box(Symbol.div_down)}{THEME.div_line}'
					f'{"".join(f"{Mv.to(cls.y + i, cls.divider)}{Symbol.v_line}" for i in range(1, cls.height - 1))}')
			Key.mouse["d"] = [[cls.divider + 3 + i, cls.y] for i in range(5)]
		else:
			out += f'{Mv.to(cls.y, cls.x + cls.width - 9)}{THEME.mem_box(Symbol.title_left)}{THEME.hi_fg("d")}{THEME.title("isks")}{THEME.mem_box(Symbol.title_right)}'
			Key.mouse["d"] = [[cls.x + cls.width - 8 + i, cls.y] for i in range(5)]
		return out

	@classmethod
	def _draw_fg(cls):
		if not "mem" in cls.boxes: return
		mem = MemCollector
		if mem.redraw: cls.redraw = True
		out: str = ""
		out_misc: str = ""
		gbg: str = ""
		gmv: str = ""
		gli: str = ""
		x, y, w, h = cls.x + 1, cls.y + 1, cls.width - 2, cls.height - 2
		if cls.resized or cls.redraw:
			cls.redraw = True
			cls._calc_size()
			out_misc += cls._draw_bg()
			Meters.mem = {}
			Meters.swap = {}
			Meters.disks_used = {}
			Meters.disks_free = {}
			if cls.mem_meter > 0:
				for name in cls.mem_names:
					if CONFIG.mem_graphs:
						Meters.mem[name] = Graph(cls.mem_meter, cls.graph_height, THEME.gradient[name], mem.vlist[name])
					else:
						Meters.mem[name] = Meter(mem.percent[name], cls.mem_meter, name)
				if cls.swap_on:
					for name in cls.swap_names:
						if CONFIG.swap_disk and CONFIG.show_disks:
							break
						elif CONFIG.mem_graphs and not CONFIG.swap_disk:
							Meters.swap[name] = Graph(cls.mem_meter, cls.graph_height, THEME.gradient[name], mem.swap_vlist[name])
						else:
							Meters.swap[name] = Meter(mem.swap_percent[name], cls.mem_meter, name)

			if CONFIG.show_disks and mem.disks:
				if CONFIG.show_io_stat or CONFIG.io_mode:
					d_graph: List[str] = []
					d_no_graph: List[str] = []
					l_vals: List[Tuple[str, int, str, bool]] = []
					if CONFIG.io_mode:
						cls.disks_io_h = (cls.height - 2 - len(mem.disks)) // max(1, len(mem.disks_io_dict))
						if cls.disks_io_h < 2: cls.disks_io_h = 1 if CONFIG.io_graph_combined else 2
					else:
						cls.disks_io_h = 1

					if CONFIG.io_graph_speeds and not cls.graph_speeds:
						try:
							cls.graph_speeds = { spds.split(":")[0] : int(spds.split(":")[1]) for spds in list(i.strip() for i in CONFIG.io_graph_speeds.split(","))}
						except (KeyError, ValueError):
							errlog.error("Wrong formatting in io_graph_speeds variable. Using defaults.")
					for name in mem.disks.keys():
						if name in mem.disks_io_dict:
							d_graph.append(name)
						else:
							d_no_graph.append(name)
							continue
						if CONFIG.io_graph_combined or not CONFIG.io_mode:
							l_vals = [("rw", cls.disks_io_h, "available", False)]
						else:
							l_vals = [("read", cls.disks_io_h // 2, "free", False), ("write", cls.disks_io_h // 2, "used", True)]

						Graphs.disk_io[name] = {_name : Graph(width=cls.disks_width - (6 if not CONFIG.io_mode else 0), height=_height, color=THEME.gradient[_gradient],
												data=mem.disks_io_dict[name][_name], invert=_invert, max_value=cls.graph_speeds.get(name, 10), no_zero=True)
												for _name, _height, _gradient, _invert in l_vals}
					cls.disks_io_order = d_graph + d_no_graph

				if cls.disk_meter > 0:
					for n, name in enumerate(mem.disks.keys()):
						if n * 2 > h: break
						Meters.disks_used[name] = Meter(mem.disks[name]["used_percent"], cls.disk_meter, "used")
						if len(mem.disks) * 3 <= h + 1:
							Meters.disks_free[name] = Meter(mem.disks[name]["free_percent"], cls.disk_meter, "free")
			if not "g" in Key.mouse:
				Key.mouse["g"] = [[x + 8 + i, y-1] for i in range(5)]
			out_misc += (f'{Mv.to(y-1, x + 7)}{THEME.mem_box(Symbol.title_left)}{Fx.b if CONFIG.mem_graphs else ""}'
				f'{THEME.hi_fg("g")}{THEME.title("raph")}{Fx.ub}{THEME.mem_box(Symbol.title_right)}')
			if CONFIG.show_disks:
				if not "s" in Key.mouse:
					Key.mouse["s"] = [[x + w - 6 + i, y-1] for i in range(4)]
				out_misc += (f'{Mv.to(y-1, x + w - 7)}{THEME.mem_box(Symbol.title_left)}{Fx.b if CONFIG.swap_disk else ""}'
				f'{THEME.hi_fg("s")}{THEME.title("wap")}{Fx.ub}{THEME.mem_box(Symbol.title_right)}')
				if not "i" in Key.mouse:
					Key.mouse["i"] = [[x + w - 10 + i, y-1] for i in range(2)]
				out_misc += (f'{Mv.to(y-1, x + w - 11)}{THEME.mem_box(Symbol.title_left)}{Fx.b if CONFIG.io_mode else ""}'
				f'{THEME.hi_fg("i")}{THEME.title("o")}{Fx.ub}{THEME.mem_box(Symbol.title_right)}')

			if Collector.collect_interrupt: return
			Draw.buffer("mem_misc", out_misc, only_save=True)
		try:
			#* Mem
			cx = 1; cy = 1

			out += f'{Mv.to(y, x+1)}{THEME.title}{Fx.b}Total:{mem.string["total"]:>{cls.mem_width - 9}}{Fx.ub}{THEME.main_fg}'
			if cls.graph_height > 0:
				gli = f'{Mv.l(2)}{THEME.mem_box(Symbol.title_right)}{THEME.div_line}{Symbol.h_line * (cls.mem_width - 1)}{"" if CONFIG.show_disks else THEME.mem_box}{Symbol.title_left}{Mv.l(cls.mem_width - 1)}{THEME.title}'
			if cls.graph_height >= 2:
				gbg = f'{Mv.l(1)}'
				gmv = f'{Mv.l(cls.mem_width - 2)}{Mv.u(cls.graph_height - 1)}'

			big_mem: bool = cls.mem_width > 21
			for name in cls.mem_names:
				if cy > h - 1: break
				if Collector.collect_interrupt: return
				if cls.mem_size > 2:
					out += (f'{Mv.to(y+cy, x+cx)}{gli}{name.capitalize()[:None if big_mem else 5]+":":<{1 if big_mem else 6.6}}{Mv.to(y+cy, x+cx + cls.mem_width - 3 - (len(mem.string[name])))}{Fx.trans(mem.string[name])}'
							f'{Mv.to(y+cy+1, x+cx)}{gbg}{Meters.mem[name](None if cls.resized else mem.percent[name])}{gmv}{str(mem.percent[name])+"%":>4}')
					cy += 2 if not cls.graph_height else cls.graph_height + 1
				else:
					out += f'{Mv.to(y+cy, x+cx)}{name.capitalize():{5.5 if cls.mem_size > 1 else 1.1}} {gbg}{Meters.mem[name](None if cls.resized else mem.percent[name])}{mem.string[name][:None if cls.mem_size > 1 else -2]:>{9 if cls.mem_size > 1 else 7}}'
					cy += 1 if not cls.graph_height else cls.graph_height
			#* Swap
			if cls.swap_on and CONFIG.show_swap and not CONFIG.swap_disk and mem.swap_string:
				if h - cy > 5:
					if cls.graph_height > 0: out += f'{Mv.to(y+cy, x+cx)}{gli}'
					cy += 1

				out += f'{Mv.to(y+cy, x+cx)}{THEME.title}{Fx.b}Swap:{mem.swap_string["total"]:>{cls.mem_width - 8}}{Fx.ub}{THEME.main_fg}'
				cy += 1
				for name in cls.swap_names:
					if cy > h - 1: break
					if Collector.collect_interrupt: return
					if cls.mem_size > 2:
						out += (f'{Mv.to(y+cy, x+cx)}{gli}{name.capitalize()[:None if big_mem else 5]+":":<{1 if big_mem else 6.6}}{Mv.to(y+cy, x+cx + cls.mem_width - 3 - (len(mem.swap_string[name])))}{Fx.trans(mem.swap_string[name])}'
								f'{Mv.to(y+cy+1, x+cx)}{gbg}{Meters.swap[name](None if cls.resized else mem.swap_percent[name])}{gmv}{str(mem.swap_percent[name])+"%":>4}')
						cy += 2 if not cls.graph_height else cls.graph_height + 1
					else:
						out += f'{Mv.to(y+cy, x+cx)}{name.capitalize():{5.5 if cls.mem_size > 1 else 1.1}} {gbg}{Meters.swap[name](None if cls.resized else mem.swap_percent[name])}{mem.swap_string[name][:None if cls.mem_size > 1 else -2]:>{9 if cls.mem_size > 1 else 7}}'; cy += 1 if not cls.graph_height else cls.graph_height

			if cls.graph_height > 0 and not cy == h: out += f'{Mv.to(y+cy, x+cx)}{gli}'

			#* Disks
			if CONFIG.show_disks and mem.disks:
				cx = x + cls.mem_width - 1; cy = 0
				big_disk: bool = cls.disks_width >= 25
				gli = f'{Mv.l(2)}{THEME.div_line}{Symbol.title_right}{Symbol.h_line * cls.disks_width}{THEME.mem_box}{Symbol.title_left}{Mv.l(cls.disks_width - 1)}'
				if CONFIG.io_mode:
					for name in cls.disks_io_order:
						item = mem.disks[name]
						io_item = mem.disks_io_dict.get(name, {})
						if Collector.collect_interrupt: return
						if cy > h - 1: break
						out += Fx.trans(f'{Mv.to(y+cy, x+cx)}{gli}{THEME.title}{Fx.b}{item["name"]:{cls.disks_width - 2}.12}{Mv.to(y+cy, x + cx + cls.disks_width - 11)}{item["total"][:None if big_disk else -2]:>9}')
						if big_disk:
							out += Fx.trans(f'{Mv.to(y+cy, x + cx + (cls.disks_width // 2) - (len(str(item["used_percent"])) // 2) - 2)}{Fx.ub}{THEME.main_fg}{item["used_percent"]}%')
						cy += 1

						if io_item:
							if cy > h - 1: break
							if CONFIG.io_graph_combined:
								if cls.disks_io_h <= 1:
									out += f'{Mv.to(y+cy, x+cx-1)}{" " * 5}'
								out += (f'{Mv.to(y+cy, x+cx-1)}{Fx.ub}{Graphs.disk_io[name]["rw"](None if cls.redraw else mem.disks_io_dict[name]["rw"][-1])}'
										f'{Mv.to(y+cy, x+cx-1)}{THEME.main_fg}{item["io"] or "RW"}')
								cy += cls.disks_io_h
							else:
								if cls.disks_io_h <= 3:
									out += f'{Mv.to(y+cy, x+cx-1)}{" " * 5}{Mv.to(y+cy+1, x+cx-1)}{" " * 5}'
								out += (f'{Mv.to(y+cy, x+cx-1)}{Fx.ub}{Graphs.disk_io[name]["read"](None if cls.redraw else mem.disks_io_dict[name]["read"][-1])}'
										f'{Mv.to(y+cy, x+cx-1)}{THEME.main_fg}{item["io_r"] or "R"}')
								cy += cls.disks_io_h // 2
								out += f'{Mv.to(y+cy, x+cx-1)}{Graphs.disk_io[name]["write"](None if cls.redraw else mem.disks_io_dict[name]["write"][-1])}'
								cy += cls.disks_io_h // 2
								out += f'{Mv.to(y+cy-1, x+cx-1)}{THEME.main_fg}{item["io_w"] or "W"}'
				else:
					for name, item in mem.disks.items():
						if Collector.collect_interrupt: return
						if not name in Meters.disks_used:
							continue
						if cy > h - 1: break
						out += Fx.trans(f'{Mv.to(y+cy, x+cx)}{gli}{THEME.title}{Fx.b}{item["name"]:{cls.disks_width - 2}.12}{Mv.to(y+cy, x + cx + cls.disks_width - 11)}{item["total"][:None if big_disk else -2]:>9}')
						if big_disk:
							out += f'{Mv.to(y+cy, x + cx + (cls.disks_width // 2) - (len(item["io"]) // 2) - 2)}{Fx.ub}{THEME.main_fg}{Fx.trans(item["io"])}'
						cy += 1
						if cy > h - 1: break
						if CONFIG.show_io_stat and name in Graphs.disk_io:
							out += f'{Mv.to(y+cy, x+cx-1)}{THEME.main_fg}{Fx.ub}{" IO: " if big_disk else " IO   " + Mv.l(2)}{Fx.ub}{Graphs.disk_io[name]["rw"](None if cls.redraw else mem.disks_io_dict[name]["rw"][-1])}'
							if not big_disk and item["io"]:
								out += f'{Mv.to(y+cy, x+cx-1)}{Fx.ub}{THEME.main_fg}{item["io"]}'
							cy += 1
							if cy > h - 1: break
						out += Mv.to(y+cy, x+cx) + (f'Used:{str(item["used_percent"]) + "%":>4} ' if big_disk else "U ")
						out += f'{Meters.disks_used[name](None if cls.resized else mem.disks[name]["used_percent"])}{item["used"][:None if big_disk else -2]:>{9 if big_disk else 7}}'
						cy += 1

						if len(mem.disks) * 3 + (len(mem.disks_io_dict) if CONFIG.show_io_stat else 0) <= h + 1:
							if cy > h - 1: break
							out += Mv.to(y+cy, x+cx)
							out += f'Free:{str(item["free_percent"]) + "%":>4} ' if big_disk else f'{"F "}'
							out += f'{Meters.disks_free[name](None if cls.resized else mem.disks[name]["free_percent"])}{item["free"][:None if big_disk else -2]:>{9 if big_disk else 7}}'
							cy += 1
							if len(mem.disks) * 4 + (len(mem.disks_io_dict) if CONFIG.show_io_stat else 0) <= h + 1: cy += 1
		except (KeyError, TypeError):
			return
		Draw.buffer(cls.buffer, f'{out_misc}{out}{Term.fg}', only_save=Menu.active)
		cls.resized = cls.redraw = False

class NetBox(Box, SubBox):
	name = "net"
	num = 3
	height_p = 30
	width_p = 45
	min_w: int = 36
	min_h: int = 6
	x = 1
	y = 1
	resized: bool = True
	redraw: bool = True
	graph_height: Dict[str, int] = {}
	symbols: Dict[str, str] = {"download" : "▼", "upload" : "▲"}
	buffer: str = "net"

	Box.buffers.append(buffer)

	@classmethod
	def _calc_size(cls):
		if not "net" in cls.boxes:
			cls.width = Term.width
			return
		if not "proc" in cls.boxes:
			width_p = 100
		else:
			width_p = cls.width_p

		cls.width = round(Term.width * width_p / 100)
		cls.height = Term.height - Box._b_cpu_h - Box._b_mem_h
		cls.y = Term.height - cls.height + 1
		cls.box_width = 27 if cls.width > 45 else 19
		cls.box_height = 9 if cls.height > 10 else cls.height - 2
		cls.box_x = cls.width - cls.box_width - 1
		cls.box_y = cls.y + ((cls.height - 2) // 2) - cls.box_height // 2 + 1
		cls.graph_height["download"] = round((cls.height - 2) / 2)
		cls.graph_height["upload"] = cls.height - 2 - cls.graph_height["download"]
		cls.redraw = True

	@classmethod
	def _draw_bg(cls) -> str:
		if not "net" in cls.boxes: return ""
		return f'{create_box(box=cls, line_color=THEME.net_box)}\
		{create_box(x=cls.box_x, y=cls.box_y, width=cls.box_width, height=cls.box_height, line_color=THEME.div_line, fill=False, title="Download", title2="Upload")}'

	@classmethod
	def _draw_fg(cls):
		if not "net" in cls.boxes: return
		net = NetCollector
		if net.redraw: cls.redraw = True
		if not net.nic: return
		out: str = ""
		out_misc: str = ""
		x, y, w, h = cls.x + 1, cls.y + 1, cls.width - 2, cls.height - 2
		bx, by, bw, bh = cls.box_x + 1, cls.box_y + 1, cls.box_width - 2, cls.box_height - 2
		reset: bool = bool(net.stats[net.nic]["download"]["offset"])

		if cls.resized or cls.redraw:
			out_misc += cls._draw_bg()
			if not "b" in Key.mouse:
				Key.mouse["b"] = [[x+w - len(net.nic[:10]) - 9 + i, y-1] for i in range(4)]
				Key.mouse["n"] = [[x+w - 5 + i, y-1] for i in range(4)]
				Key.mouse["z"] = [[x+w - len(net.nic[:10]) - 14 + i, y-1] for i in range(4)]


			out_misc += (f'{Mv.to(y-1, x+w - 25)}{THEME.net_box}{Symbol.h_line * (10 - len(net.nic[:10]))}{Symbol.title_left}{Fx.b if reset else ""}{THEME.hi_fg("z")}{THEME.title("ero")}'
				f'{Fx.ub}{THEME.net_box(Symbol.title_right)}{Term.fg}'
				f'{THEME.net_box}{Symbol.title_left}{Fx.b}{THEME.hi_fg("<b")} {THEME.title(net.nic[:10])} {THEME.hi_fg("n>")}{Fx.ub}{THEME.net_box(Symbol.title_right)}{Term.fg}')
			if w - len(net.nic[:10]) - 20 > 6:
				if not "a" in Key.mouse: Key.mouse["a"] = [[x+w - 20 - len(net.nic[:10]) + i, y-1] for i in range(4)]
				out_misc += (f'{Mv.to(y-1, x+w - 21 - len(net.nic[:10]))}{THEME.net_box(Symbol.title_left)}{Fx.b if net.auto_min else ""}{THEME.hi_fg("a")}{THEME.title("uto")}'
				f'{Fx.ub}{THEME.net_box(Symbol.title_right)}{Term.fg}')
			if w - len(net.nic[:10]) - 20 > 13:
				if not "y" in Key.mouse: Key.mouse["y"] = [[x+w - 26 - len(net.nic[:10]) + i, y-1] for i in range(4)]
				out_misc += (f'{Mv.to(y-1, x+w - 27 - len(net.nic[:10]))}{THEME.net_box(Symbol.title_left)}{Fx.b if CONFIG.net_sync else ""}{THEME.title("s")}{THEME.hi_fg("y")}{THEME.title("nc")}'
				f'{Fx.ub}{THEME.net_box(Symbol.title_right)}{Term.fg}')
			if net.address and w - len(net.nic[:10]) - len(net.address) - 20 > 15:
				out_misc += (f'{Mv.to(y-1, x+7)}{THEME.net_box(Symbol.title_left)}{Fx.b}{THEME.title(net.address)}{Fx.ub}{THEME.net_box(Symbol.title_right)}{Term.fg}')
			Draw.buffer("net_misc", out_misc, only_save=True)

		cy = 0
		for direction in ["download", "upload"]:
			strings = net.strings[net.nic][direction]
			stats = net.stats[net.nic][direction]
			if cls.redraw: stats["redraw"] = True
			if stats["redraw"] or cls.resized:
				Graphs.net[direction] = Graph(w - bw - 3, cls.graph_height[direction], THEME.gradient[direction], stats["speed"], max_value=net.sync_top if CONFIG.net_sync else stats["graph_top"],
					invert=direction != "download", color_max_value=net.net_min.get(direction) if CONFIG.net_color_fixed else None)
			out += f'{Mv.to(y if direction == "download" else y + cls.graph_height["download"], x)}{Graphs.net[direction](None if stats["redraw"] else stats["speed"][-1])}'

			out += (f'{Mv.to(by+cy, bx)}{THEME.main_fg}{cls.symbols[direction]} {strings["byte_ps"]:<10.10}' +
					("" if bw < 20 else f'{Mv.to(by+cy, bx+bw - 12)}{"(" + strings["bit_ps"] + ")":>12.12}'))
			cy += 1 if bh != 3 else 2
			if bh >= 6:
				out += f'{Mv.to(by+cy, bx)}{cls.symbols[direction]} {"Top:"}{Mv.to(by+cy, bx+bw - 12)}{"(" + strings["top"] + ")":>12.12}'
				cy += 1
			if bh >= 4:
				out += f'{Mv.to(by+cy, bx)}{cls.symbols[direction]} {"Total:"}{Mv.to(by+cy, bx+bw - 10)}{strings["total"]:>10.10}'
				if bh > 2 and bh % 2: cy += 2
				else: cy += 1
			stats["redraw"] = False

		out += (f'{Mv.to(y, x)}{THEME.graph_text(net.sync_string if CONFIG.net_sync else net.strings[net.nic]["download"]["graph_top"])}'
				f'{Mv.to(y+h-1, x)}{THEME.graph_text(net.sync_string if CONFIG.net_sync else net.strings[net.nic]["upload"]["graph_top"])}')

		Draw.buffer(cls.buffer, f'{out_misc}{out}{Term.fg}', only_save=Menu.active)
		cls.redraw = cls.resized = False

class ProcBox(Box):
	name = "proc"
	num = 4
	height_p = 68
	width_p = 55
	min_w: int = 44
	min_h: int = 16
	x = 1
	y = 1
	current_y: int = 0
	current_h: int = 0
	select_max: int = 0
	selected: int = 0
	selected_pid: int = 0
	last_selection: int = 0
	filtering: bool = False
	moved: bool = False
	start: int = 1
	count: int = 0
	s_len: int = 0
	detailed: bool = False
	detailed_x: int = 0
	detailed_y: int = 0
	detailed_width: int = 0
	detailed_height: int = 8
	resized: bool = True
	redraw: bool = True
	buffer: str = "proc"
	pid_counter: Dict[int, int] = {}
	Box.buffers.append(buffer)

	@classmethod
	def _calc_size(cls):
		if not "proc" in cls.boxes:
			cls.width = Term.width
			return
		width_p: int; height_p: int
		if not "net" in cls.boxes and not "mem" in cls.boxes:
			width_p = 100
		else:
			width_p = cls.width_p

		if not "cpu" in cls.boxes:
			height_p = 100
		else:
			height_p = cls.height_p

		cls.width = round(Term.width * width_p / 100)
		cls.height = round(Term.height * height_p / 100)
		if cls.height + Box._b_cpu_h > Term.height: cls.height = Term.height - Box._b_cpu_h
		cls.x = Term.width - cls.width + 1
		cls.y = Box._b_cpu_h + 1
		cls.current_y = cls.y
		cls.current_h = cls.height
		cls.select_max = cls.height - 3
		cls.redraw = True
		cls.resized = True

	@classmethod
	def _draw_bg(cls) -> str:
		if not "proc" in cls.boxes: return ""
		return create_box(box=cls, line_color=THEME.proc_box)

	@classmethod
	def selector(cls, key: str, mouse_pos: Tuple[int, int] = (0, 0)):
		old: Tuple[int, int] = (cls.start, cls.selected)
		new_sel: int
		if key in ["up", "k"]:
			if cls.selected == 1 and cls.start > 1:
				cls.start -= 1
			elif cls.selected == 1:
				cls.selected = 0
			elif cls.selected > 1:
				cls.selected -= 1
		elif key in ["down", "j"]:
			if cls.selected == 0 and ProcCollector.detailed and cls.last_selection:
				cls.selected = cls.last_selection
				cls.last_selection = 0
			if cls.selected == cls.select_max and cls.start < ProcCollector.num_procs - cls.select_max + 1:
				cls.start += 1
			elif cls.selected < cls.select_max:
				cls.selected += 1
		elif key == "mouse_scroll_up" and cls.start > 1:
			cls.start -= 5
		elif key == "mouse_scroll_down" and cls.start < ProcCollector.num_procs - cls.select_max + 1:
			cls.start += 5
		elif key == "page_up" and cls.start > 1:
			cls.start -= cls.select_max
		elif key == "page_down" and cls.start < ProcCollector.num_procs - cls.select_max + 1:
			cls.start += cls.select_max
		elif key == "home":
			if cls.start > 1: cls.start = 1
			elif cls.selected > 0: cls.selected = 0
		elif key == "end":
			if cls.start < ProcCollector.num_procs - cls.select_max + 1: cls.start = ProcCollector.num_procs - cls.select_max + 1
			elif cls.selected < cls.select_max: cls.selected = cls.select_max
		elif key == "mouse_click":
			if mouse_pos[0] > cls.x + cls.width - 4 and cls.current_y + 1 < mouse_pos[1] < cls.current_y + 1 + cls.select_max + 1:
				if mouse_pos[1] == cls.current_y + 2:
					cls.start = 1
				elif mouse_pos[1] == cls.current_y + 1 + cls.select_max:
					cls.start = ProcCollector.num_procs - cls.select_max + 1
				else:
					cls.start = round((mouse_pos[1] - cls.current_y) * ((ProcCollector.num_procs - cls.select_max - 2) / (cls.select_max - 2)))
			else:
				new_sel = mouse_pos[1] - cls.current_y - 1 if mouse_pos[1] >= cls.current_y - 1 else 0
				if new_sel > 0 and new_sel == cls.selected:
					Key.list.insert(0, "enter")
					return
				elif new_sel > 0 and new_sel != cls.selected:
					if cls.last_selection: cls.last_selection = 0
					cls.selected = new_sel
		elif key == "mouse_unselect":
			cls.selected = 0

		if cls.start > ProcCollector.num_procs - cls.select_max + 1 and ProcCollector.num_procs > cls.select_max: cls.start = ProcCollector.num_procs - cls.select_max + 1
		elif cls.start > ProcCollector.num_procs: cls.start = ProcCollector.num_procs
		if cls.start < 1: cls.start = 1
		if cls.selected > ProcCollector.num_procs and ProcCollector.num_procs < cls.select_max: cls.selected = ProcCollector.num_procs
		elif cls.selected > cls.select_max: cls.selected = cls.select_max
		if cls.selected < 0: cls.selected = 0

		if old != (cls.start, cls.selected):
			cls.moved = True
			Collector.collect(ProcCollector, proc_interrupt=True, redraw=True, only_draw=True)


	@classmethod
	def _draw_fg(cls):
		if not "proc" in cls.boxes: return
		proc = ProcCollector
		if proc.proc_interrupt: return
		if proc.redraw: cls.redraw = True
		out: str = ""
		out_misc: str = ""
		n: int = 0
		x, y, w, h = cls.x + 1, cls.current_y + 1, cls.width - 2, cls.current_h - 2
		prog_len: int; arg_len: int; val: int; c_color: str; m_color: str; t_color: str; sort_pos: int; tree_len: int; is_selected: bool; calc: int
		dgx: int; dgw: int; dx: int; dw: int; dy: int
		l_count: int = 0
		scroll_pos: int = 0
		killed: bool = True
		indent: str = ""
		offset: int = 0
		tr_show: bool = True
		usr_show: bool = True
		vals: List[str]
		g_color: str = ""
		s_len: int = 0
		if proc.search_filter: s_len = len(proc.search_filter[:10])
		loc_string: str = f'{cls.start + cls.selected - 1}/{proc.num_procs}'
		end: str = ""

		if proc.detailed:
			dgx, dgw = x, w // 3
			dw = w - dgw - 1
			if dw > 120:
				dw = 120
				dgw = w - 121
			dx = x + dgw + 2
			dy = cls.y + 1

		if w > 67:
			arg_len = w - 53 - (1 if proc.num_procs > cls.select_max else 0)
			prog_len = 15
		else:
			arg_len = 0
			prog_len = w - 38 - (1 if proc.num_procs > cls.select_max else 0)
			if prog_len < 15:
				tr_show = False
				prog_len += 5
			if prog_len < 12:
				usr_show = False
				prog_len += 9

		if CONFIG.proc_tree:
			tree_len = arg_len + prog_len + 6
			arg_len = 0

		#* Buttons and titles only redrawn if needed
		if cls.resized or cls.redraw:
			s_len += len(CONFIG.proc_sorting)
			if cls.resized or s_len != cls.s_len or proc.detailed:
				cls.s_len = s_len
				for k in ["e", "r", "c", "T", "K", "I", "enter", "left", " ", "f", "delete"]:
					if k in Key.mouse: del Key.mouse[k]
			if proc.detailed:
				killed = proc.details.get("killed", False)
				main = THEME.main_fg if cls.selected == 0 and not killed else THEME.inactive_fg
				hi = THEME.hi_fg if cls.selected == 0 and not killed else THEME.inactive_fg
				title = THEME.title if cls.selected == 0 and not killed else THEME.inactive_fg
				if cls.current_y != cls.y + 8 or cls.resized or Graphs.detailed_cpu is NotImplemented:
					cls.current_y = cls.y + 8
					cls.current_h = cls.height - 8
					for i in range(7): out_misc += f'{Mv.to(dy+i, x)}{" " * w}'
					out_misc += (f'{Mv.to(dy+7, x-1)}{THEME.proc_box}{Symbol.title_right}{Symbol.h_line*w}{Symbol.title_left}'
					f'{Mv.to(dy+7, x+1)}{THEME.proc_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg(SUPERSCRIPT[cls.num])}{THEME.title(cls.name)}{Fx.ub}{THEME.proc_box(Symbol.title_right)}{THEME.div_line}')
					for i in range(7):
						out_misc += f'{Mv.to(dy + i, dgx + dgw + 1)}{Symbol.v_line}'

				out_misc += (f'{Mv.to(dy-1, x-1)}{THEME.proc_box}{Symbol.left_up}{Symbol.h_line*w}{Symbol.right_up}'
					f'{Mv.to(dy-1, dgx + dgw + 1)}{Symbol.div_up}'
					f'{Mv.to(dy-1, x+1)}{THEME.proc_box(Symbol.title_left)}{Fx.b}{THEME.title(str(proc.details["pid"]))}{Fx.ub}{THEME.proc_box(Symbol.title_right)}'
					f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{THEME.title(proc.details["name"][:(dgw - 11)])}{Fx.ub}{THEME.proc_box(Symbol.title_right)}')

				if cls.selected == 0:
					Key.mouse["enter"] = [[dx+dw-10 + i, dy-1] for i in range(7)]
				if cls.selected == 0 and not killed:
					Key.mouse["T"] = [[dx+2 + i, dy-1] for i in range(9)]

				out_misc += (f'{Mv.to(dy-1, dx+dw - 11)}{THEME.proc_box(Symbol.title_left)}{Fx.b}{title if cls.selected > 0 else THEME.title}close{Fx.ub} {main if cls.selected > 0 else THEME.main_fg}{Symbol.enter}{THEME.proc_box(Symbol.title_right)}'
					f'{Mv.to(dy-1, dx+1)}{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}T{title}erminate{Fx.ub}{THEME.proc_box(Symbol.title_right)}')
				if dw > 28:
					if cls.selected == 0 and not killed and not "K" in Key.mouse: Key.mouse["K"] = [[dx + 13 + i, dy-1] for i in range(4)]
					out_misc += f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}K{title}ill{Fx.ub}{THEME.proc_box(Symbol.title_right)}'
				if dw > 39:
					if cls.selected == 0 and not killed and not "I" in Key.mouse: Key.mouse["I"] = [[dx + 19 + i, dy-1] for i in range(9)]
					out_misc += f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}I{title}nterrupt{Fx.ub}{THEME.proc_box(Symbol.title_right)}'

				if Graphs.detailed_cpu is NotImplemented or cls.resized:
					Graphs.detailed_cpu = Graph(dgw+1, 7, THEME.gradient["cpu"], proc.details_cpu)
					Graphs.detailed_mem = Graph(dw // 3, 1, None, proc.details_mem)

				cls.select_max = cls.height - 11
				y = cls.y + 9
				h = cls.height - 10

			else:
				if cls.current_y != cls.y or cls.resized:
					cls.current_y = cls.y
					cls.current_h = cls.height
					y, h = cls.y + 1, cls.height - 2
					out_misc += (f'{Mv.to(y-1, x-1)}{THEME.proc_box}{Symbol.left_up}{Symbol.h_line*w}{Symbol.right_up}'
						f'{Mv.to(y-1, x+1)}{THEME.proc_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg(SUPERSCRIPT[cls.num])}{THEME.title(cls.name)}{Fx.ub}{THEME.proc_box(Symbol.title_right)}'
						f'{Mv.to(y+7, x-1)}{THEME.proc_box(Symbol.v_line)}{Mv.r(w)}{THEME.proc_box(Symbol.v_line)}')
				cls.select_max = cls.height - 3


			sort_pos = x + w - len(CONFIG.proc_sorting) - 7
			if not "left" in Key.mouse:
				Key.mouse["left"] = [[sort_pos + i, y-1] for i in range(3)]
				Key.mouse["right"] = [[sort_pos + len(CONFIG.proc_sorting) + 3 + i, y-1] for i in range(3)]


			out_misc += (f'{Mv.to(y-1, x + 8)}{THEME.proc_box(Symbol.h_line * (w - 9))}' +
				("" if not proc.detailed else f"{Mv.to(dy+7, dgx + dgw + 1)}{THEME.proc_box(Symbol.div_down)}") +
				f'{Mv.to(y-1, sort_pos)}{THEME.proc_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg("<")} {THEME.title(CONFIG.proc_sorting)} '
				f'{THEME.hi_fg(">")}{Fx.ub}{THEME.proc_box(Symbol.title_right)}')


			if w > 29 + s_len:
				if not "e" in Key.mouse: Key.mouse["e"] = [[sort_pos - 5 + i, y-1] for i in range(4)]
				out_misc += (f'{Mv.to(y-1, sort_pos - 6)}{THEME.proc_box(Symbol.title_left)}{Fx.b if CONFIG.proc_tree else ""}'
					f'{THEME.title("tre")}{THEME.hi_fg("e")}{Fx.ub}{THEME.proc_box(Symbol.title_right)}')
			if w > 37 + s_len:
				if not "r" in Key.mouse: Key.mouse["r"] = [[sort_pos - 14 + i, y-1] for i in range(7)]
				out_misc += (f'{Mv.to(y-1, sort_pos - 15)}{THEME.proc_box(Symbol.title_left)}{Fx.b if CONFIG.proc_reversed else ""}'
					f'{THEME.hi_fg("r")}{THEME.title("everse")}{Fx.ub}{THEME.proc_box(Symbol.title_right)}')
			if w > 47 + s_len:
				if not "c" in Key.mouse: Key.mouse["c"] = [[sort_pos - 24 + i, y-1] for i in range(8)]
				out_misc += (f'{Mv.to(y-1, sort_pos - 25)}{THEME.proc_box(Symbol.title_left)}{Fx.b if CONFIG.proc_per_core else ""}'
					f'{THEME.title("per-")}{THEME.hi_fg("c")}{THEME.title("ore")}{Fx.ub}{THEME.proc_box(Symbol.title_right)}')

			if not "f" in Key.mouse or cls.resized: Key.mouse["f"] = [[x+6 + i, y-1] for i in range(6 if not proc.search_filter else 2 + len(proc.search_filter[-10:]))]
			if proc.search_filter:
				if not "delete" in Key.mouse: Key.mouse["delete"] = [[x+12 + len(proc.search_filter[-10:]) + i, y-1] for i in range(3)]
			elif "delete" in Key.mouse:
				del Key.mouse["delete"]
			out_misc += (f'{Mv.to(y-1, x + 8)}{THEME.proc_box(Symbol.title_left)}{Fx.b if cls.filtering or proc.search_filter else ""}{THEME.hi_fg("F" if cls.filtering and proc.case_sensitive else "f")}{THEME.title}' +
				("ilter" if not proc.search_filter and not cls.filtering else f' {proc.search_filter[-(10 if w < 83 else w - 74):]}{(Fx.bl + "█" + Fx.ubl) if cls.filtering else THEME.hi_fg(" del")}') +
				f'{THEME.proc_box(Symbol.title_right)}')

			main = THEME.inactive_fg if cls.selected == 0 else THEME.main_fg
			hi = THEME.inactive_fg if cls.selected == 0 else THEME.hi_fg
			title = THEME.inactive_fg if cls.selected == 0 else THEME.title
			out_misc += (f'{Mv.to(y+h, x + 1)}{THEME.proc_box}{Symbol.h_line*(w-4)}'
					f'{Mv.to(y+h, x+1)}{THEME.proc_box(Symbol.title_left)}{main}{Symbol.up} {Fx.b}{THEME.main_fg("select")} {Fx.ub}'
					f'{THEME.inactive_fg if cls.selected == cls.select_max else THEME.main_fg}{Symbol.down}{THEME.proc_box(Symbol.title_right)}'
					f'{THEME.proc_box(Symbol.title_left)}{title}{Fx.b}info {Fx.ub}{main}{Symbol.enter}{THEME.proc_box(Symbol.title_right)}')
			if not "enter" in Key.mouse: Key.mouse["enter"] = [[x + 14 + i, y+h] for i in range(6)]
			if w - len(loc_string) > 34:
				if not "T" in Key.mouse: Key.mouse["T"] = [[x + 22 + i, y+h] for i in range(9)]
				out_misc += f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}T{title}erminate{Fx.ub}{THEME.proc_box(Symbol.title_right)}'
			if w - len(loc_string) > 40:
				if not "K" in Key.mouse: Key.mouse["K"] = [[x + 33 + i, y+h] for i in range(4)]
				out_misc += f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}K{title}ill{Fx.ub}{THEME.proc_box(Symbol.title_right)}'
			if w - len(loc_string) > 51:
				if not "I" in Key.mouse: Key.mouse["I"] = [[x + 39 + i, y+h] for i in range(9)]
				out_misc += f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}I{title}nterrupt{Fx.ub}{THEME.proc_box(Symbol.title_right)}'
			if CONFIG.proc_tree and w - len(loc_string) > 65:
				if not " " in Key.mouse: Key.mouse[" "] = [[x + 50 + i, y+h] for i in range(12)]
				out_misc += f'{THEME.proc_box(Symbol.title_left)}{Fx.b}{hi}spc {title}collapse{Fx.ub}{THEME.proc_box(Symbol.title_right)}'

			#* Processes labels
			selected: str = CONFIG.proc_sorting
			label: str
			if selected == "memory": selected = "mem"
			if selected == "threads" and not CONFIG.proc_tree and not arg_len: selected = "tr"
			if CONFIG.proc_tree:
				label = (f'{THEME.title}{Fx.b}{Mv.to(y, x)}{" Tree:":<{tree_len-2}}' + (f'{"Threads: ":<9}' if tr_show else " "*4) + (f'{"User:":<9}' if usr_show else "") + f'Mem%{"Cpu%":>11}{Fx.ub}{THEME.main_fg} ' +
						(" " if proc.num_procs > cls.select_max else ""))
				if selected in ["pid", "program", "arguments"]: selected = "tree"
			else:
				label = (f'{THEME.title}{Fx.b}{Mv.to(y, x)}{"Pid:":>7} {"Program:" if prog_len > 8 else "Prg:":<{prog_len}}' + (f'{"Arguments:":<{arg_len-4}}' if arg_len else "") +
					((f'{"Threads:":<9}' if arg_len else f'{"Tr:":^5}') if tr_show else "") + (f'{"User:":<9}' if usr_show else "") + f'Mem%{"Cpu%":>11}{Fx.ub}{THEME.main_fg} ' +
					(" " if proc.num_procs > cls.select_max else ""))
				if selected == "program" and prog_len <= 8: selected = "prg"
			selected = selected.split(" ")[0].capitalize()
			if CONFIG.proc_mem_bytes: label = label.replace("Mem%", "MemB")
			label = label.replace(selected, f'{Fx.u}{selected}{Fx.uu}')
			out_misc += label

			Draw.buffer("proc_misc", out_misc, only_save=True)

		#* Detailed box draw
		if proc.detailed:
			if proc.details["status"] == psutil.STATUS_RUNNING: stat_color = Fx.b
			elif proc.details["status"] in [psutil.STATUS_DEAD, psutil.STATUS_STOPPED, psutil.STATUS_ZOMBIE]: stat_color = f'{THEME.inactive_fg}'
			else: stat_color = ""
			expand = proc.expand
			iw = (dw - 3) // (4 + expand)
			iw2 = iw - 1
			out += (f'{Mv.to(dy, dgx)}{Graphs.detailed_cpu(None if cls.moved or proc.details["killed"] else proc.details_cpu[-1])}'
					f'{Mv.to(dy, dgx)}{THEME.title}{Fx.b}{0 if proc.details["killed"] else proc.details["cpu_percent"]}%{Mv.r(1)}{"" if SYSTEM == "MacOS" else (("C" if dgw < 20 else "Core") + str(proc.details["cpu_num"]))}')
			for i, l in enumerate(["C", "P", "U"]):
				out += f'{Mv.to(dy+2+i, dgx)}{l}'
			for i, l in enumerate(["C", "M", "D"]):
				out += f'{Mv.to(dy+4+i, dx+1)}{l}'
			out += (f'{Mv.to(dy, dx+1)} {"Status:":^{iw}.{iw2}}{"Elapsed:":^{iw}.{iw2}}' +
					(f'{"Parent:":^{iw}.{iw2}}' if dw > 28 else "") + (f'{"User:":^{iw}.{iw2}}' if dw > 38 else "") +
					(f'{"Threads:":^{iw}.{iw2}}' if expand > 0 else "") + (f'{"Nice:":^{iw}.{iw2}}' if expand > 1 else "") +
					(f'{"IO Read:":^{iw}.{iw2}}' if expand > 2 else "") + (f'{"IO Write:":^{iw}.{iw2}}' if expand > 3 else "") +
					(f'{"TTY:":^{iw}.{iw2}}' if expand > 4 else "") +
					f'{Mv.to(dy+1, dx+1)}{Fx.ub}{THEME.main_fg}{stat_color}{proc.details["status"]:^{iw}.{iw2}}{Fx.ub}{THEME.main_fg}{proc.details["uptime"]:^{iw}.{iw2}} ' +
					(f'{proc.details["parent_name"]:^{iw}.{iw2}}' if dw > 28 else "") + (f'{proc.details["username"]:^{iw}.{iw2}}' if dw > 38 else "") +
					(f'{proc.details["threads"]:^{iw}.{iw2}}' if expand > 0 else "") + (f'{proc.details["nice"]:^{iw}.{iw2}}' if expand > 1 else "") +
					(f'{proc.details["io_read"]:^{iw}.{iw2}}' if expand > 2 else "") + (f'{proc.details["io_write"]:^{iw}.{iw2}}' if expand > 3 else "") +
					(f'{proc.details["terminal"][-(iw2):]:^{iw}.{iw2}}' if expand > 4 else "") +
					f'{Mv.to(dy+3, dx)}{THEME.title}{Fx.b}{("Memory: " if dw > 42 else "M:") + str(round(proc.details["memory_percent"], 1)) + "%":>{dw//3-1}}{Fx.ub} {THEME.inactive_fg}{"⡀"*(dw//3)}'
					f'{Mv.l(dw//3)}{THEME.proc_misc}{Graphs.detailed_mem(None if cls.moved else proc.details_mem[-1])} '
					f'{THEME.title}{Fx.b}{proc.details["memory_bytes"]:.{dw//3 - 2}}{THEME.main_fg}{Fx.ub}')
			cy = dy + (4 if len(proc.details["cmdline"]) > dw - 5 else 5)
			for i in range(ceil(len(proc.details["cmdline"]) / (dw - 5))):
				out += f'{Mv.to(cy+i, dx + 3)}{proc.details["cmdline"][((dw-5)*i):][:(dw-5)]:{"^" if i == 0 else "<"}{dw-5}}'
				if i == 2: break

		#* Checking for selection out of bounds
		if cls.start > proc.num_procs - cls.select_max + 1 and proc.num_procs > cls.select_max: cls.start = proc.num_procs - cls.select_max + 1
		elif cls.start > proc.num_procs: cls.start = proc.num_procs
		if cls.start < 1: cls.start = 1
		if cls.selected > proc.num_procs and proc.num_procs < cls.select_max: cls.selected = proc.num_procs
		elif cls.selected > cls.select_max: cls.selected = cls.select_max
		if cls.selected < 0: cls.selected = 0

		#* Start iteration over all processes and info
		cy = 1
		for n, (pid, items) in enumerate(proc.processes.items(), start=1):
			if n < cls.start: continue
			l_count += 1
			if l_count == cls.selected:
				is_selected = True
				cls.selected_pid = pid
			else: is_selected = False

			indent, name, cmd, threads, username, mem, mem_b, cpu = [items.get(v, d) for v, d in [("indent", ""), ("name", ""), ("cmd", ""), ("threads", 0), ("username", "?"), ("mem", 0.0), ("mem_b", 0), ("cpu", 0.0)]]

			if CONFIG.proc_tree:
				arg_len = 0
				offset = tree_len - len(f'{indent}{pid}')
				if offset < 1: offset = 0
				indent = f'{indent:.{tree_len - len(str(pid))}}'
				if offset - len(name) > 12:
					cmd = cmd.split(" ")[0].split("/")[-1]
					if not cmd.startswith(name):
						offset = len(name)
						arg_len = tree_len - len(f'{indent}{pid} {name} ') + 2
						cmd = f'({cmd[:(arg_len-4)]})'
			else:
				offset = prog_len - 1
			if cpu > 1.0 or pid in Graphs.pid_cpu:
				if pid not in Graphs.pid_cpu:
					Graphs.pid_cpu[pid] = Graph(5, 1, None, [0])
					cls.pid_counter[pid] = 0
				elif cpu < 1.0:
					cls.pid_counter[pid] += 1
					if cls.pid_counter[pid] > 10:
						del cls.pid_counter[pid], Graphs.pid_cpu[pid]
				else:
					cls.pid_counter[pid] = 0

			end = f'{THEME.main_fg}{Fx.ub}' if CONFIG.proc_colors else Fx.ub
			if cls.selected > cy: calc = cls.selected - cy
			elif 0 < cls.selected <= cy: calc = cy - cls.selected
			else: calc = cy
			if CONFIG.proc_colors and not is_selected:
				vals = []
				for v in [int(cpu), int(mem), int(threads // 3)]:
					if CONFIG.proc_gradient:
						val = ((v if v <= 100 else 100) + 100) - calc * 100 // cls.select_max
						vals += [f'{THEME.gradient["proc_color" if val < 100 else "process"][val if val < 100 else val - 100]}']
					else:
						vals += [f'{THEME.gradient["process"][v if v <= 100 else 100]}']
				c_color, m_color, t_color = vals
			else:
				c_color = m_color = t_color = Fx.b
			if CONFIG.proc_gradient and not is_selected:
				g_color = f'{THEME.gradient["proc"][calc * 100 // cls.select_max]}'
			if is_selected:
				c_color = m_color = t_color = g_color = end = ""
				out += f'{THEME.selected_bg}{THEME.selected_fg}{Fx.b}'

			#* Creates one line for a process with all gathered information
			out += (f'{Mv.to(y+cy, x)}{g_color}{indent}{pid:>{(1 if CONFIG.proc_tree else 7)}} ' +
				f'{c_color}{name:<{offset}.{offset}} {end}' +
				(f'{g_color}{cmd:<{arg_len}.{arg_len-1}}' if arg_len else "") +
				(t_color + (f'{threads:>4} ' if threads < 1000 else "999> ") + end if tr_show else "") +
				(g_color + (f'{username:<9.9}' if len(username) < 10 else f'{username[:8]:<8}+') if usr_show else "") +
				m_color + ((f'{mem:>4.1f}' if mem < 100 else f'{mem:>4.0f} ') if not CONFIG.proc_mem_bytes else f'{floating_humanizer(mem_b, short=True):>4.4}') + end +
				f' {THEME.inactive_fg}{"⡀"*5}{THEME.main_fg}{g_color}{c_color}' + (f' {cpu:>4.1f} ' if cpu < 100 else f'{cpu:>5.0f} ') + end +
				(" " if proc.num_procs > cls.select_max else ""))

			#* Draw small cpu graph for process if cpu usage was above 1% in the last 10 updates
			if pid in Graphs.pid_cpu:
				out += f'{Mv.to(y+cy, x + w - (12 if proc.num_procs > cls.select_max else 11))}{c_color if CONFIG.proc_colors else THEME.proc_misc}{Graphs.pid_cpu[pid](None if cls.moved else round(cpu))}{THEME.main_fg}'

			if is_selected: out += f'{Fx.ub}{Term.fg}{Term.bg}{Mv.to(y+cy, x + w - 1)}{" " if proc.num_procs > cls.select_max else ""}'

			cy += 1
			if cy == h: break
		if cy < h:
			for i in range(h-cy):
				out += f'{Mv.to(y+cy+i, x)}{" " * w}'

		#* Draw scrollbar if needed
		if proc.num_procs > cls.select_max:
			if cls.resized:
				Key.mouse["mouse_scroll_up"] = [[x+w-2+i, y] for i in range(3)]
				Key.mouse["mouse_scroll_down"] = [[x+w-2+i, y+h-1] for i in range(3)]
			scroll_pos = round(cls.start * (cls.select_max - 2) / (proc.num_procs - (cls.select_max - 2)))
			if scroll_pos < 0 or cls.start == 1: scroll_pos = 0
			elif scroll_pos > h - 3 or cls.start >= proc.num_procs - cls.select_max: scroll_pos = h - 3
			out += (f'{Mv.to(y, x+w-1)}{Fx.b}{THEME.main_fg}↑{Mv.to(y+h-1, x+w-1)}↓{Fx.ub}'
					f'{Mv.to(y+1+scroll_pos, x+w-1)}█')
		elif "scroll_up" in Key.mouse:
			del Key.mouse["scroll_up"], Key.mouse["scroll_down"]

		#* Draw current selection and number of processes
		out += (f'{Mv.to(y+h, x + w - 3 - len(loc_string))}{THEME.proc_box}{Symbol.title_left}{THEME.title}'
					f'{Fx.b}{loc_string}{Fx.ub}{THEME.proc_box(Symbol.title_right)}')

		#* Clean up dead processes graphs and counters
		cls.count += 1
		if cls.count == 100:
			cls.count == 0
			for p in list(cls.pid_counter):
				if not psutil.pid_exists(p):
					del cls.pid_counter[p], Graphs.pid_cpu[p]

		Draw.buffer(cls.buffer, f'{out_misc}{out}{Term.fg}', only_save=Menu.active)
		cls.redraw = cls.resized = cls.moved = False

class Collector:
	'''Data collector master class
	* .start(): Starts collector thread
	* .stop(): Stops collector thread
	* .collect(*collectors: Collector, draw_now: bool = True, interrupt: bool = False): queues up collectors to run'''
	stopping: bool = False
	started: bool = False
	draw_now: bool = False
	redraw: bool = False
	only_draw: bool = False
	thread: threading.Thread
	collect_run = threading.Event()
	collect_idle = threading.Event()
	collect_idle.set()
	collect_done = threading.Event()
	collect_queue: List = []
	collect_interrupt: bool = False
	proc_interrupt: bool = False
	use_draw_list: bool = False
	proc_counter: int = 1

	@classmethod
	def start(cls):
		cls.stopping = False
		cls.thread = threading.Thread(target=cls._runner, args=())
		cls.thread.start()
		cls.started = True

	@classmethod
	def stop(cls):
		if cls.started and cls.thread.is_alive():
			cls.stopping = True
			cls.started = False
			cls.collect_queue = []
			cls.collect_idle.set()
			cls.collect_done.set()
			try:
				cls.thread.join()
			except:
				pass

	@classmethod
	def _runner(cls):
		'''This is meant to run in it's own thread, collecting and drawing when collect_run is set'''
		draw_buffers: List[str] = []
		debugged: bool = False
		try:
			while not cls.stopping:
				if CONFIG.draw_clock and CONFIG.update_ms != 1000: Box.draw_clock()
				cls.collect_run.wait(0.1)
				if not cls.collect_run.is_set():
					continue
				draw_buffers = []
				cls.collect_interrupt = False
				cls.collect_run.clear()
				cls.collect_idle.clear()
				cls.collect_done.clear()
				if DEBUG and not debugged: TimeIt.start("Collect and draw")
				while cls.collect_queue:
					collector = cls.collect_queue.pop()
					if not cls.only_draw:
						collector._collect()
					collector._draw()
					if cls.use_draw_list: draw_buffers.append(collector.buffer)
					if cls.collect_interrupt: break
				if DEBUG and not debugged: TimeIt.stop("Collect and draw"); debugged = True
				if cls.draw_now and not Menu.active and not cls.collect_interrupt:
					if cls.use_draw_list: Draw.out(*draw_buffers)
					else: Draw.out()
				if CONFIG.draw_clock and CONFIG.update_ms == 1000: Box.draw_clock()
				cls.collect_idle.set()
				cls.collect_done.set()
		except Exception as e:
			errlog.exception(f'Data collection thread failed with exception: {e}')
			cls.collect_idle.set()
			cls.collect_done.set()
			clean_quit(1, thread=True)

	@classmethod
	def collect(cls, *collectors, draw_now: bool = True, interrupt: bool = False, proc_interrupt: bool = False, redraw: bool = False, only_draw: bool = False):
		'''Setup collect queue for _runner'''
		cls.collect_interrupt = interrupt
		cls.proc_interrupt = proc_interrupt
		cls.collect_idle.wait()
		cls.collect_interrupt = False
		cls.proc_interrupt = False
		cls.use_draw_list = False
		cls.draw_now = draw_now
		cls.redraw = redraw
		cls.only_draw = only_draw

		if collectors:
			cls.collect_queue = [*collectors]
			cls.use_draw_list = True
			if ProcCollector in cls.collect_queue:
				cls.proc_counter = 1

		else:
			cls.collect_queue = list(cls.__subclasses__())
			if CONFIG.proc_update_mult > 1:
				if cls.proc_counter > 1:
					cls.collect_queue.remove(ProcCollector)
				if cls.proc_counter == CONFIG.proc_update_mult:
					cls.proc_counter = 0
				cls.proc_counter += 1

		cls.collect_run.set()


class CpuCollector(Collector):
	'''Collects cpu usage for cpu and cores, cpu frequency, load_avg, uptime and cpu temps'''
	cpu_usage: List[List[int]] = []
	cpu_upper: List[int] = []
	cpu_lower: List[int] = []
	cpu_temp: List[List[int]] = []
	cpu_temp_high: int = 0
	cpu_temp_crit: int = 0
	for _ in range(THREADS + 1):
		cpu_usage.append([])
		cpu_temp.append([])
	freq_error: bool = False
	cpu_freq: int = 0
	load_avg: List[float] = []
	uptime: str = ""
	buffer: str = CpuBox.buffer
	sensor_method: str = ""
	got_sensors: bool = False
	sensor_swap: bool = False
	cpu_temp_only: bool = False

	@classmethod
	def get_sensors(cls):
		'''Check if we can get cpu temps and return method of getting temps'''
		cls.sensor_method = ""
		if SYSTEM == "MacOS":
			try:
				if which("coretemp") and subprocess.check_output(["coretemp", "-p"], universal_newlines=True).strip().replace("-", "").isdigit():
					cls.sensor_method = "coretemp"
				elif which("osx-cpu-temp") and subprocess.check_output("osx-cpu-temp", universal_newlines=True).rstrip().endswith("°C"):
					cls.sensor_method = "osx-cpu-temp"
			except: pass
		elif CONFIG.cpu_sensor != "Auto" and CONFIG.cpu_sensor in CONFIG.cpu_sensors:
			cls.sensor_method = "psutil"
		elif hasattr(psutil, "sensors_temperatures"):
			try:
				temps = psutil.sensors_temperatures()
				if temps:
					for name, entries in temps.items():
						if name.lower().startswith("cpu"):
							cls.sensor_method = "psutil"
							break
						for entry in entries:
							if entry.label.startswith(("Package", "Core 0", "Tdie", "CPU")):
								cls.sensor_method = "psutil"
								break
			except: pass
		if not cls.sensor_method and SYSTEM == "Linux":
			try:
				if which("vcgencmd") and subprocess.check_output(["vcgencmd", "measure_temp"], universal_newlines=True).strip().endswith("'C"):
					cls.sensor_method = "vcgencmd"
			except: pass
		cls.got_sensors = bool(cls.sensor_method)

	@classmethod
	def _collect(cls):
		cls.cpu_usage[0].append(round(psutil.cpu_percent(percpu=False)))
		if len(cls.cpu_usage[0]) > Term.width * 4:
			del cls.cpu_usage[0][0]

		cpu_times_percent = psutil.cpu_times_percent()
		for x in ["upper", "lower"]:
			if getattr(CONFIG, "cpu_graph_" + x) == "total":
				setattr(cls, "cpu_" + x, cls.cpu_usage[0])
			else:
				getattr(cls, "cpu_" + x).append(round(getattr(cpu_times_percent, getattr(CONFIG, "cpu_graph_" + x))))
			if len(getattr(cls, "cpu_" + x)) > Term.width * 4:
				del getattr(cls, "cpu_" + x)[0]

		for n, thread in enumerate(psutil.cpu_percent(percpu=True), start=1):
			cls.cpu_usage[n].append(round(thread))
			if len(cls.cpu_usage[n]) > Term.width * 2:
				del cls.cpu_usage[n][0]
		try:
			if hasattr(psutil.cpu_freq(), "current"):
				cls.cpu_freq = round(psutil.cpu_freq().current)
		except Exception as e:
			if not cls.freq_error:
				cls.freq_error = True
				errlog.error("Exception while getting cpu frequency!")
				errlog.exception(f'{e}')
			else:
				pass
		cls.load_avg = [round(lavg, 2) for lavg in psutil.getloadavg()]
		cls.uptime = str(timedelta(seconds=round(time()-psutil.boot_time(),0)))[:-3].replace(" days,", "d").replace(" day,", "d")

		if CONFIG.check_temp and cls.got_sensors:
			cls._collect_temps()

	@classmethod
	def _collect_temps(cls):
		temp: int = 1000
		cores: List[int] = []
		core_dict: Dict[int, int] = {}
		entry_int: int = 0
		cpu_type: str = ""
		c_max: int = 0
		s_name: str = "_-_"
		s_label: str = "_-_"
		if cls.sensor_method == "psutil":
			try:
				if CONFIG.cpu_sensor != "Auto":
					s_name, s_label = CONFIG.cpu_sensor.split(":", 1)
				for name, entries in psutil.sensors_temperatures().items():
					for num, entry in enumerate(entries, 1):
						if name == s_name and (entry.label == s_label or str(num) == s_label) and round(entry.current) > 0:
							if entry.label.startswith("Package"):
								cpu_type = "intel"
							elif entry.label.startswith("Tdie"):
								cpu_type = "ryzen"
							else:
								cpu_type = "other"
							if getattr(entry, "high", None) != None and entry.high > 1: cls.cpu_temp_high = round(entry.high)
							else: cls.cpu_temp_high = 80
							if getattr(entry, "critical", None) != None and entry.critical > 1: cls.cpu_temp_crit = round(entry.critical)
							else: cls.cpu_temp_crit = 95
							temp = round(entry.current)
						elif entry.label.startswith(("Package", "Tdie")) and cpu_type in ["", "other"] and s_name == "_-_" and hasattr(entry, "current") and round(entry.current) > 0:
							if not cls.cpu_temp_high or cls.sensor_swap or cpu_type == "other":
								cls.sensor_swap = False
								if getattr(entry, "high", None) != None and entry.high > 1: cls.cpu_temp_high = round(entry.high)
								else: cls.cpu_temp_high = 80
								if getattr(entry, "critical", None) != None and entry.critical > 1: cls.cpu_temp_crit = round(entry.critical)
								else: cls.cpu_temp_crit = 95
							cpu_type = "intel" if entry.label.startswith("Package") else "ryzen"
							temp = round(entry.current)
						elif (entry.label.startswith(("Core", "Tccd", "CPU")) or (name.lower().startswith("cpu") and not entry.label)) and hasattr(entry, "current") and round(entry.current) > 0:
							if entry.label.startswith(("Core", "Tccd")):
								entry_int = int(entry.label.replace("Core", "").replace("Tccd", ""))
								if entry_int in core_dict and cpu_type != "ryzen":
									if c_max == 0:
										c_max = max(core_dict) + 1
									if c_max < THREADS // 2 and (entry_int + c_max) not in core_dict:
										core_dict[(entry_int + c_max)] = round(entry.current)
									continue
								elif entry_int in core_dict:
									continue
								core_dict[entry_int] = round(entry.current)
								continue
							elif cpu_type in ["intel", "ryzen"]:
								continue
							if not cpu_type:
								cpu_type = "other"
								if not cls.cpu_temp_high or cls.sensor_swap:
									cls.sensor_swap = False
									if getattr(entry, "high", None) != None and entry.high > 1: cls.cpu_temp_high = round(entry.high)
									else: cls.cpu_temp_high = 60 if name == "cpu_thermal" else 80
									if getattr(entry, "critical", None) != None and entry.critical > 1: cls.cpu_temp_crit = round(entry.critical)
									else: cls.cpu_temp_crit = 80 if name == "cpu_thermal" else 95
								temp = round(entry.current)
							cores.append(round(entry.current))
				if core_dict:
					if not temp or temp == 1000:
						temp = sum(core_dict.values()) // len(core_dict)
					if not cls.cpu_temp_high or not cls.cpu_temp_crit:
						cls.cpu_temp_high, cls.cpu_temp_crit = 80, 95
					cls.cpu_temp[0].append(temp)
					if cpu_type == "ryzen":
						ccds: int = len(core_dict)
						cores_per_ccd: int = CORES // ccds
						z: int = 1
						for x in range(THREADS):
							if x == CORES:
								z = 1
							if CORE_MAP[x] + 1 > cores_per_ccd * z:
								z += 1
							if z in core_dict:
								cls.cpu_temp[x+1].append(core_dict[z])
					else:
						for x in range(THREADS):
							if CORE_MAP[x] in core_dict:
								cls.cpu_temp[x+1].append(core_dict[CORE_MAP[x]])

				elif len(cores) == THREADS / 2:
					cls.cpu_temp[0].append(temp)
					for n, t in enumerate(cores, start=1):
						try:
							cls.cpu_temp[n].append(t)
							cls.cpu_temp[THREADS // 2 + n].append(t)
						except IndexError:
							break

				else:
					cls.cpu_temp[0].append(temp)
					if len(cores) > 1:
						for n, t in enumerate(cores, start=1):
							try:
								cls.cpu_temp[n].append(t)
							except IndexError:
								break
			except Exception as e:
					errlog.exception(f'{e}')
					cls.got_sensors = False
					CpuBox._calc_size()

		else:
			try:
				if cls.sensor_method == "coretemp":
					temp = max(0, int(subprocess.check_output(["coretemp", "-p"], universal_newlines=True).strip()))
					cores = [max(0, int(x)) for x in subprocess.check_output("coretemp", universal_newlines=True).split()]
					if len(cores) == THREADS / 2:
						cls.cpu_temp[0].append(temp)
						for n, t in enumerate(cores, start=1):
							try:
								cls.cpu_temp[n].append(t)
								cls.cpu_temp[THREADS // 2 + n].append(t)
							except IndexError:
								break
					else:
						cores.insert(0, temp)
						for n, t in enumerate(cores):
							try:
								cls.cpu_temp[n].append(t)
							except IndexError:
								break
					if not cls.cpu_temp_high:
						cls.cpu_temp_high = 85
						cls.cpu_temp_crit = 100
				elif cls.sensor_method == "osx-cpu-temp":
					temp = max(0, round(float(subprocess.check_output("osx-cpu-temp", universal_newlines=True).strip()[:-2])))
					if not cls.cpu_temp_high:
						cls.cpu_temp_high = 85
						cls.cpu_temp_crit = 100
				elif cls.sensor_method == "vcgencmd":
					temp = max(0, round(float(subprocess.check_output(["vcgencmd", "measure_temp"], universal_newlines=True).strip()[5:-2])))
					if not cls.cpu_temp_high:
						cls.cpu_temp_high = 60
						cls.cpu_temp_crit = 80
			except Exception as e:
					errlog.exception(f'{e}')
					cls.got_sensors = False
					CpuBox._calc_size()
			else:
				if not cores:
					cls.cpu_temp[0].append(temp)

		if not core_dict and len(cores) <= 1:
			cls.cpu_temp_only = True
		if len(cls.cpu_temp[0]) > 5:
			for n in range(len(cls.cpu_temp)):
				if cls.cpu_temp[n]:
					del cls.cpu_temp[n][0]

	@classmethod
	def _draw(cls):
		CpuBox._draw_fg()

class MemCollector(Collector):
	'''Collects memory and disks information'''
	values: Dict[str, int] = {}
	vlist: Dict[str, List[int]] = {}
	percent: Dict[str, int] = {}
	string: Dict[str, str] = {}

	swap_values: Dict[str, int] = {}
	swap_vlist: Dict[str, List[int]] = {}
	swap_percent: Dict[str, int] = {}
	swap_string: Dict[str, str] = {}

	disks: Dict[str, Dict]
	disk_hist: Dict[str, Tuple] = {}
	timestamp: float = time()
	disks_io_dict: Dict[str, Dict[str, List[int]]] = {}
	recheck_diskutil: bool = True
	diskutil_map: Dict[str, str] = {}

	io_error: bool = False

	old_disks: List[str] = []
	old_io_disks: List[str] = []

	fstab_filter: List[str] = []

	excludes: List[str] = ["squashfs", "nullfs"]
	if SYSTEM == "BSD": excludes += ["devfs", "tmpfs", "procfs", "linprocfs", "gvfs", "fusefs"]

	buffer: str = MemBox.buffer

	@classmethod
	def _collect(cls):
		#* Collect memory
		mem = psutil.virtual_memory()
		if hasattr(mem, "cached"):
			cls.values["cached"] = mem.cached
		else:
			cls.values["cached"] = mem.active
		cls.values["total"], cls.values["free"], cls.values["available"] = mem.total, mem.free, mem.available
		cls.values["used"] = cls.values["total"] - cls.values["available"]

		for key, value in cls.values.items():
			cls.string[key] = floating_humanizer(value)
			if key == "total": continue
			cls.percent[key] = round(value * 100 / cls.values["total"])
			if CONFIG.mem_graphs:
				if not key in cls.vlist: cls.vlist[key] = []
				cls.vlist[key].append(cls.percent[key])
				if len(cls.vlist[key]) > MemBox.width: del cls.vlist[key][0]

		#* Collect swap
		if CONFIG.show_swap or CONFIG.swap_disk:
			swap = psutil.swap_memory()
			cls.swap_values["total"], cls.swap_values["free"] = swap.total, swap.free
			cls.swap_values["used"] = cls.swap_values["total"] - cls.swap_values["free"]

			if swap.total:
				if not MemBox.swap_on:
					MemBox.redraw = True
				MemBox.swap_on = True
				for key, value in cls.swap_values.items():
					cls.swap_string[key] = floating_humanizer(value)
					if key == "total": continue
					cls.swap_percent[key] = round(value * 100 / cls.swap_values["total"])
					if CONFIG.mem_graphs:
						if not key in cls.swap_vlist: cls.swap_vlist[key] = []
						cls.swap_vlist[key].append(cls.swap_percent[key])
						if len(cls.swap_vlist[key]) > MemBox.width: del cls.swap_vlist[key][0]
			else:
				if MemBox.swap_on:
					MemBox.redraw = True
				MemBox.swap_on = False
		else:
			if MemBox.swap_on:
				MemBox.redraw = True
			MemBox.swap_on = False


		if not CONFIG.show_disks: return
		#* Collect disks usage
		disk_read: int = 0
		disk_write: int = 0
		dev_name: str
		disk_name: str
		filtering: Tuple = ()
		filter_exclude: bool = False
		io_string_r: str
		io_string_w: str
		u_percent: int
		cls.disks = {}

		if CONFIG.disks_filter:
			if CONFIG.disks_filter.startswith("exclude="):
				filter_exclude = True
				filtering = tuple(v.strip() for v in CONFIG.disks_filter.replace("exclude=", "").strip().split(","))
			else:
				filtering = tuple(v.strip() for v in CONFIG.disks_filter.strip().split(","))
		try:
			io_counters = psutil.disk_io_counters(perdisk=SYSTEM != "BSD", nowrap=True)
		except ValueError as e:
			if not cls.io_error:
				cls.io_error = True
				errlog.error(f'Non fatal error during disk io collection!')
				if psutil.version_info[0] < 5 or (psutil.version_info[0] == 5 and psutil.version_info[1] < 7):
					errlog.error(f'Caused by outdated psutil version.')
				errlog.exception(f'{e}')
			io_counters = None

		if SYSTEM == "MacOS" and cls.recheck_diskutil:
			cls.recheck_diskutil = False
			try:
				dutil_out = subprocess.check_output(["diskutil", "list", "physical"], universal_newlines=True)
				for line in dutil_out.split("\n"):
					line = line.replace("\u2068", "").replace("\u2069", "")
					if line.startswith("/dev/"):
						xdisk = line.split()[0].replace("/dev/", "")
					elif "Container" in line:
						ydisk = line.split()[3]
						if xdisk and ydisk:
							cls.diskutil_map[xdisk] = ydisk
							xdisk = ydisk = ""
			except:
				pass

		if CONFIG.use_fstab and SYSTEM != "MacOS" and not cls.fstab_filter:
			try:
				with open('/etc/fstab','r') as fstab:
					for line in fstab:
						line = line.strip()
						if line and not line.startswith('#'):
							mount_data = (line.split())
							if mount_data[2].lower() != "swap":
								cls.fstab_filter += [mount_data[1]]
				errlog.debug(f'new fstab_filter set : {cls.fstab_filter}')
			except IOError:
				CONFIG.use_fstab = False
				errlog.warning(f'Error reading fstab, use_fstab flag reset to {CONFIG.use_fstab}')
		if not CONFIG.use_fstab and cls.fstab_filter:
			cls.fstab_filter = []
			errlog.debug(f'use_fstab flag has been turned to {CONFIG.use_fstab}, fstab_filter cleared')

		for disk in psutil.disk_partitions(all=CONFIG.use_fstab or not CONFIG.only_physical):
			disk_io = None
			io_string_r = io_string_w = ""
			if CONFIG.use_fstab and disk.mountpoint not in cls.fstab_filter:
				continue
			disk_name = disk.mountpoint.rsplit('/', 1)[-1] if not disk.mountpoint == "/" else "root"
			if cls.excludes and disk.fstype in cls.excludes:
				continue
			if filtering and ((not filter_exclude and not disk.mountpoint in filtering) or (filter_exclude and disk.mountpoint in filtering)):
				continue
			if SYSTEM == "MacOS" and disk.mountpoint == "/private/var/vm":
				continue
			try:
				disk_u = psutil.disk_usage(disk.mountpoint)
			except:
				pass

			u_percent = round(getattr(disk_u, "percent", 0))
			cls.disks[disk.device] = { "name" : disk_name, "used_percent" : u_percent, "free_percent" : 100 - u_percent }
			for name in ["total", "used", "free"]:
				cls.disks[disk.device][name] = floating_humanizer(getattr(disk_u, name, 0))

			#* Collect disk io
			if io_counters:
				try:
					if SYSTEM != "BSD":
						dev_name = os.path.realpath(disk.device).rsplit('/', 1)[-1]
						if not dev_name in io_counters:
							for names in io_counters:
								if names in dev_name:
									disk_io = io_counters[names]
									break
							else:
								if cls.diskutil_map:
									for names, items in cls.diskutil_map.items():
										if items in dev_name and names in io_counters:
											disk_io = io_counters[names]
						else:
							disk_io = io_counters[dev_name]
					elif disk.mountpoint == "/":
						disk_io = io_counters
					else:
						raise Exception
					disk_read = round((disk_io.read_bytes - cls.disk_hist[disk.device][0]) / (time() - cls.timestamp)) #type: ignore
					disk_write = round((disk_io.write_bytes - cls.disk_hist[disk.device][1]) / (time() - cls.timestamp)) #type: ignore
					if not disk.device in cls.disks_io_dict:
						cls.disks_io_dict[disk.device] = {"read" : [], "write" : [], "rw" : []}
					cls.disks_io_dict[disk.device]["read"].append(disk_read >> 20)
					cls.disks_io_dict[disk.device]["write"].append(disk_write >> 20)
					cls.disks_io_dict[disk.device]["rw"].append((disk_read + disk_write) >> 20)

					if len(cls.disks_io_dict[disk.device]["read"]) > MemBox.width:
						del cls.disks_io_dict[disk.device]["read"][0], cls.disks_io_dict[disk.device]["write"][0], cls.disks_io_dict[disk.device]["rw"][0]

				except:
					disk_read = disk_write = 0
			else:
				disk_read = disk_write = 0

			if disk_io:
				cls.disk_hist[disk.device] = (disk_io.read_bytes, disk_io.write_bytes)
				if CONFIG.io_mode or MemBox.disks_width > 30:
					if disk_read > 0:
						io_string_r = f'▲{floating_humanizer(disk_read, short=True)}'
					if disk_write > 0:
						io_string_w = f'▼{floating_humanizer(disk_write, short=True)}'
					if CONFIG.io_mode:
						cls.disks[disk.device]["io_r"] = io_string_r
						cls.disks[disk.device]["io_w"] = io_string_w
				elif disk_read + disk_write > 0:
					io_string_r += f'▼▲{floating_humanizer(disk_read + disk_write, short=True)}'

			cls.disks[disk.device]["io"] = io_string_r + (" " if io_string_w and io_string_r else "") + io_string_w

		if CONFIG.swap_disk and MemBox.swap_on:
			cls.disks["__swap"] = { "name" : "swap", "used_percent" : cls.swap_percent["used"], "free_percent" : cls.swap_percent["free"], "io" : "" }
			for name in ["total", "used", "free"]:
				cls.disks["__swap"][name] = cls.swap_string[name]
			if len(cls.disks) > 2:
				try:
					new = { list(cls.disks)[0] : cls.disks.pop(list(cls.disks)[0])}
					new["__swap"] = cls.disks.pop("__swap")
					new.update(cls.disks)
					cls.disks = new
				except:
					pass

		if cls.old_disks != list(cls.disks) or cls.old_io_disks != list(cls.disks_io_dict):
			MemBox.redraw = True
			cls.recheck_diskutil = True
			cls.old_disks = list(cls.disks)
			cls.old_io_disks = list(cls.disks_io_dict)

		cls.timestamp = time()

	@classmethod
	def _draw(cls):
		MemBox._draw_fg()

class NetCollector(Collector):
	'''Collects network stats'''
	buffer: str = NetBox.buffer
	nics: List[str] = []
	nic_i: int = 0
	nic: str = ""
	new_nic: str = ""
	nic_error: bool = False
	reset: bool = False
	graph_raise: Dict[str, int] = {"download" : 5, "upload" : 5}
	graph_lower: Dict[str, int] = {"download" : 5, "upload" : 5}
	#min_top: int = 10<<10
	#* Stats structure = stats[netword device][download, upload][total, last, top, graph_top, offset, speed, redraw, graph_raise, graph_low] = int, List[int], bool
	stats: Dict[str, Dict[str, Dict[str, Any]]] = {}
	#* Strings structure strings[network device][download, upload][total, byte_ps, bit_ps, top, graph_top] = str
	strings: Dict[str, Dict[str, Dict[str, str]]] = {}
	switched: bool = False
	timestamp: float = time()
	net_min: Dict[str, int] = {"download" : -1, "upload" : -1}
	auto_min: bool = CONFIG.net_auto
	net_iface: str = CONFIG.net_iface
	sync_top: int = 0
	sync_string: str = ""
	address: str = ""

	@classmethod
	def _get_nics(cls):
		'''Get a list of all network devices sorted by highest throughput'''
		cls.nic_i = 0
		cls.nics = []
		cls.nic = ""
		try:
			io_all = psutil.net_io_counters(pernic=True)
		except Exception as e:
			if not cls.nic_error:
				cls.nic_error = True
				errlog.exception(f'{e}')
		if not io_all: return
		up_stat = psutil.net_if_stats()
		for nic in sorted(io_all.keys(), key=lambda nic: (getattr(io_all[nic], "bytes_recv", 0) + getattr(io_all[nic], "bytes_sent", 0)), reverse=True):
			if nic not in up_stat or not up_stat[nic].isup:
				continue
			cls.nics.append(nic)
		if not cls.nics: cls.nics = [""]
		cls.nic = cls.nics[cls.nic_i]
		if cls.net_iface and cls.net_iface in cls.nics:
                        cls.nic = cls.net_iface
                        cls.nic_i = cls.nics.index(cls.nic)


	@classmethod
	def switch(cls, key: str):
		if cls.net_iface: cls.net_iface = ""
		if len(cls.nics) < 2 and cls.nic in cls.nics:
			return

		if cls.nic_i == -1:
			cls.nic_i = 0 if key == "n" else -1
		else:
			cls.nic_i += +1 if key == "n" else -1

		cls.nic_i %= len(cls.nics)
		cls.new_nic = cls.nics[cls.nic_i]
		cls.switched = True
		Collector.collect(NetCollector, redraw=True)

	@classmethod
	def _collect(cls):
		speed: int
		stat: Dict
		up_stat = psutil.net_if_stats()

		if sorted(cls.nics) != sorted(nic for nic in up_stat if up_stat[nic].isup):
			old_nic = cls.nic
			cls._get_nics()
			cls.nic = old_nic
			if cls.nic not in cls.nics:
				cls.nic_i = -1
			else:
				cls.nic_i = cls.nics.index(cls.nic)

		if cls.switched:
			cls.nic = cls.new_nic
			cls.switched = False

		if not cls.nic or cls.nic not in up_stat:
			cls._get_nics()
			if not cls.nic: return
		try:
			io_all = psutil.net_io_counters(pernic=True)[cls.nic]
		except KeyError:
			pass
			return
		if not cls.nic in cls.stats:
			cls.stats[cls.nic] = {}
			cls.strings[cls.nic] = { "download" : {}, "upload" : {}}
			for direction, value in ["download", io_all.bytes_recv], ["upload", io_all.bytes_sent]:
				cls.stats[cls.nic][direction] = { "total" : value, "last" : value, "top" : 0, "graph_top" : 0, "offset" : 0, "speed" : [], "redraw" : True, "graph_raise" : 0, "graph_lower" : 7 }
				for v in ["total", "byte_ps", "bit_ps", "top", "graph_top"]:
					cls.strings[cls.nic][direction][v] = ""

		cls.stats[cls.nic]["download"]["total"] = io_all.bytes_recv
		cls.stats[cls.nic]["upload"]["total"] = io_all.bytes_sent
		if cls.nic in psutil.net_if_addrs():
			cls.address = getattr(psutil.net_if_addrs()[cls.nic][0], "address", "")

		for direction in ["download", "upload"]:
			stat = cls.stats[cls.nic][direction]
			strings = cls.strings[cls.nic][direction]
			#* Calculate current speed
			stat["speed"].append(round((stat["total"] - stat["last"]) / (time() - cls.timestamp)))
			stat["last"] = stat["total"]
			speed = stat["speed"][-1]

			if cls.net_min[direction] == -1:
				cls.net_min[direction] = units_to_bytes(getattr(CONFIG, "net_" + direction))
				stat["graph_top"] = cls.net_min[direction]
				stat["graph_lower"] = 7
				if not cls.auto_min:
					stat["redraw"] = True
					strings["graph_top"] = floating_humanizer(stat["graph_top"], short=True)

			if stat["offset"] and stat["offset"] > stat["total"]:
				cls.reset = True

			if cls.reset:
				if not stat["offset"]:
					stat["offset"] = stat["total"]
				else:
					stat["offset"] = 0
				if direction == "upload":
					cls.reset = False
					NetBox.redraw = True

			if len(stat["speed"]) > NetBox.width * 2:
				del stat["speed"][0]

			strings["total"] = floating_humanizer(stat["total"] - stat["offset"])
			strings["byte_ps"] = floating_humanizer(stat["speed"][-1], per_second=True)
			strings["bit_ps"] = floating_humanizer(stat["speed"][-1], bit=True, per_second=True)

			if speed > stat["top"] or not stat["top"]:
				stat["top"] = speed
				strings["top"] = floating_humanizer(stat["top"], bit=True, per_second=True)

			if cls.auto_min:
				if speed > stat["graph_top"]:
					stat["graph_raise"] += 1
					if stat["graph_lower"] > 0: stat["graph_lower"] -= 1
				elif speed < stat["graph_top"] // 10:
					stat["graph_lower"] += 1
					if stat["graph_raise"] > 0: stat["graph_raise"] -= 1

				if stat["graph_raise"] >= 5 or stat["graph_lower"] >= 5:
					if stat["graph_raise"] >= 5:
						stat["graph_top"] = round(max(stat["speed"][-5:]) / 0.8)
					elif stat["graph_lower"] >= 5:
						stat["graph_top"] = max(10 << 10, max(stat["speed"][-5:]) * 3)
					stat["graph_raise"] = 0
					stat["graph_lower"] = 0
					stat["redraw"] = True
					strings["graph_top"] = floating_humanizer(stat["graph_top"], short=True)

		cls.timestamp = time()

		if CONFIG.net_sync:
			c_max: int = max(cls.stats[cls.nic]["download"]["graph_top"], cls.stats[cls.nic]["upload"]["graph_top"])
			if c_max != cls.sync_top:
				cls.sync_top = c_max
				cls.sync_string = floating_humanizer(cls.sync_top, short=True)
				NetBox.redraw = True

	@classmethod
	def _draw(cls):
		NetBox._draw_fg()


class ProcCollector(Collector):
	'''Collects process stats'''
	buffer: str = ProcBox.buffer
	search_filter: str = ""
	case_sensitive: bool = False
	processes: Dict = {}
	num_procs: int = 0
	det_cpu: float = 0.0
	detailed: bool = False
	detailed_pid: Union[int, None] = None
	details: Dict[str, Any] = {}
	details_cpu: List[int] = []
	details_mem: List[int] = []
	expand: int = 0
	collapsed: Dict = {}
	tree_counter: int = 0
	p_values: List[str] = ["pid", "name", "cmdline", "num_threads", "username", "memory_percent", "cpu_percent", "cpu_times", "create_time"]
	sort_expr: Dict = {}
	sort_expr["pid"] = compile("p.info['pid']", "str", "eval")
	sort_expr["program"] = compile("'' if p.info['name'] == 0.0 else p.info['name']", "str", "eval")
	sort_expr["arguments"] = compile("' '.join(str(p.info['cmdline'])) or ('' if p.info['name'] == 0.0 else p.info['name'])", "str", "eval")
	sort_expr["threads"] = compile("0 if p.info['num_threads'] == 0.0 else p.info['num_threads']", "str", "eval")
	sort_expr["user"] = compile("'' if p.info['username'] == 0.0 else p.info['username']", "str", "eval")
	sort_expr["memory"] = compile("p.info['memory_percent']", "str", "eval")
	sort_expr["cpu lazy"] = compile("(sum(p.info['cpu_times'][:2] if not p.info['cpu_times'] == 0.0 else [0.0, 0.0]) * 1000 / (time() - p.info['create_time']))", "str", "eval")
	sort_expr["cpu responsive"] = compile("(p.info['cpu_percent'] if CONFIG.proc_per_core else (p.info['cpu_percent'] / THREADS))", "str", "eval")

	@classmethod
	def _collect(cls):
		'''List all processess with pid, name, arguments, threads, username, memory percent and cpu percent'''
		if not "proc" in Box.boxes: return
		out: Dict = {}
		cls.det_cpu = 0.0
		sorting: str = CONFIG.proc_sorting
		reverse: bool = not CONFIG.proc_reversed
		proc_per_cpu: bool = CONFIG.proc_per_core
		search: List[str] = []
		if cls.search_filter:
			if cls.case_sensitive:
				search = [i.strip() for i in cls.search_filter.split(",")]
			else:
				search = [i.strip() for i in cls.search_filter.lower().split(",")]
		err: float = 0.0
		n: int = 0

		if CONFIG.proc_tree and sorting == "arguments":
			sorting = "program"

		sort_cmd = cls.sort_expr[sorting]

		if CONFIG.proc_tree:
			cls._tree(sort_cmd=sort_cmd, reverse=reverse, proc_per_cpu=proc_per_cpu, search=search)
		else:
			for p in sorted(psutil.process_iter(cls.p_values + (["memory_info"] if CONFIG.proc_mem_bytes else []), err), key=lambda p: eval(sort_cmd), reverse=reverse):
				if cls.collect_interrupt or cls.proc_interrupt:
					return
				if p.info["name"] == "idle" or p.info["name"] == err or p.info["pid"] == err:
					continue
				if p.info["cmdline"] == err:
					p.info["cmdline"] = ""
				if p.info["username"] == err:
					p.info["username"] = ""
				if p.info["num_threads"] == err:
					p.info["num_threads"] = 0
				if search:
					if cls.detailed and p.info["pid"] == cls.detailed_pid:
						cls.det_cpu = p.info["cpu_percent"]
					for value in [ p.info["name"], " ".join(p.info["cmdline"]), str(p.info["pid"]), p.info["username"] ]:
						if not cls.case_sensitive:
							value = value.lower()
						for s in search:
							if s in value:
								break
						else: continue
						break
					else: continue

				cpu = p.info["cpu_percent"] if proc_per_cpu else round(p.info["cpu_percent"] / THREADS, 2)
				mem = p.info["memory_percent"]
				if CONFIG.proc_mem_bytes and hasattr(p.info["memory_info"], "rss"):
					mem_b = p.info["memory_info"].rss
				else:
					mem_b = 0

				cmd = " ".join(p.info["cmdline"]) or "[" + p.info["name"] + "]"

				out[p.info["pid"]] = {
					"name" : p.info["name"],
					"cmd" : cmd.replace("\n", "").replace("\t", "").replace("\\", ""),
					"threads" : p.info["num_threads"],
					"username" : p.info["username"],
					"mem" : mem,
					"mem_b" : mem_b,
					"cpu" : cpu }

				n += 1

			cls.num_procs = n
			cls.processes = out.copy()

		if cls.detailed:
			cls.expand = ((ProcBox.width - 2) - ((ProcBox.width - 2) // 3) - 40) // 10
			if cls.expand > 5: cls.expand = 5
		if cls.detailed and not cls.details.get("killed", False):
			try:
				c_pid = cls.detailed_pid
				det = psutil.Process(c_pid)
			except (psutil.NoSuchProcess, psutil.ZombieProcess):
				cls.details["killed"] = True
				cls.details["status"] = psutil.STATUS_DEAD
				ProcBox.redraw = True
			else:
				attrs: List[str] = ["status", "memory_info", "create_time"]
				if not SYSTEM == "MacOS": attrs.extend(["cpu_num"])
				if cls.expand:
					attrs.extend(["nice", "terminal"])
					if not SYSTEM == "MacOS": attrs.extend(["io_counters"])

				if not c_pid in cls.processes: attrs.extend(["pid", "name", "cmdline", "num_threads", "username", "memory_percent"])

				cls.details = det.as_dict(attrs=attrs, ad_value="")
				if det.parent() != None: cls.details["parent_name"] = det.parent().name()
				else: cls.details["parent_name"] = ""

				cls.details["pid"] = c_pid
				if c_pid in cls.processes:
					cls.details["name"] = cls.processes[c_pid]["name"]
					cls.details["cmdline"] = cls.processes[c_pid]["cmd"]
					cls.details["threads"] = f'{cls.processes[c_pid]["threads"]}'
					cls.details["username"] = cls.processes[c_pid]["username"]
					cls.details["memory_percent"] = cls.processes[c_pid]["mem"]
					cls.details["cpu_percent"] = round(cls.processes[c_pid]["cpu"] * (1 if CONFIG.proc_per_core else THREADS))
				else:
					cls.details["cmdline"] = " ".join(cls.details["cmdline"]) or "[" + cls.details["name"] + "]"
					cls.details["threads"] = f'{cls.details["num_threads"]}'
					cls.details["cpu_percent"] = round(cls.det_cpu)

				cls.details["killed"] = False
				if SYSTEM == "MacOS":
					cls.details["cpu_num"] = -1
					cls.details["io_counters"] = ""


				if hasattr(cls.details["memory_info"], "rss"): cls.details["memory_bytes"] = floating_humanizer(cls.details["memory_info"].rss) # type: ignore
				else: cls.details["memory_bytes"] = "? Bytes"

				if isinstance(cls.details["create_time"], float):
					uptime = timedelta(seconds=round(time()-cls.details["create_time"],0))
					if uptime.days > 0: cls.details["uptime"] = f'{uptime.days}d {str(uptime).split(",")[1][:-3].strip()}'
					else: cls.details["uptime"] = f'{uptime}'
				else: cls.details["uptime"] = "??:??:??"

				if cls.expand:
					if cls.expand > 1 : cls.details["nice"] = f'{cls.details["nice"]}'
					if SYSTEM == "BSD":
						if cls.expand > 2:
							if hasattr(cls.details["io_counters"], "read_count"): cls.details["io_read"] = f'{cls.details["io_counters"].read_count}'
							else: cls.details["io_read"] = "?"
						if cls.expand > 3:
							if hasattr(cls.details["io_counters"], "write_count"): cls.details["io_write"] = f'{cls.details["io_counters"].write_count}'
							else: cls.details["io_write"] = "?"
					else:
						if cls.expand > 2:
							if hasattr(cls.details["io_counters"], "read_bytes"): cls.details["io_read"] = floating_humanizer(cls.details["io_counters"].read_bytes)
							else: cls.details["io_read"] = "?"
						if cls.expand > 3:
							if hasattr(cls.details["io_counters"], "write_bytes"): cls.details["io_write"] = floating_humanizer(cls.details["io_counters"].write_bytes)
							else: cls.details["io_write"] = "?"
					if cls.expand > 4 : cls.details["terminal"] = f'{cls.details["terminal"]}'.replace("/dev/", "")

				cls.details_cpu.append(cls.details["cpu_percent"])
				mem = cls.details["memory_percent"]
				if mem > 80: mem = round(mem)
				elif mem > 60: mem = round(mem * 1.2)
				elif mem > 30: mem = round(mem * 1.5)
				elif mem > 10: mem = round(mem * 2)
				elif mem > 5: mem = round(mem * 10)
				else: mem = round(mem * 20)
				cls.details_mem.append(mem)
				if len(cls.details_cpu) > ProcBox.width: del cls.details_cpu[0]
				if len(cls.details_mem) > ProcBox.width: del cls.details_mem[0]

	@classmethod
	def _tree(cls, sort_cmd, reverse: bool, proc_per_cpu: bool, search: List[str]):
		'''List all processess in a tree view with pid, name, threads, username, memory percent and cpu percent'''
		out: Dict = {}
		err: float = 0.0
		det_cpu: float = 0.0
		infolist: Dict = {}
		cls.tree_counter += 1
		tree = defaultdict(list)
		n: int = 0
		for p in sorted(psutil.process_iter(cls.p_values + (["memory_info"] if CONFIG.proc_mem_bytes else []), err), key=lambda p: eval(sort_cmd), reverse=reverse):
			if cls.collect_interrupt: return
			try:
				tree[p.ppid()].append(p.pid)
			except (psutil.NoSuchProcess, psutil.ZombieProcess):
				pass
			else:
				infolist[p.pid] = p.info
				n += 1
		if 0 in tree and 0 in tree[0]:
			tree[0].remove(0)

		def create_tree(pid: int, tree: defaultdict, indent: str = "", inindent: str = " ", found: bool = False, depth: int = 0, collapse_to: Union[None, int] = None):
			nonlocal infolist, proc_per_cpu, search, out, det_cpu
			name: str; threads: int; username: str; mem: float; cpu: float; collapse: bool = False
			cont: bool = True
			getinfo: Dict = {}
			if cls.collect_interrupt: return
			try:
				name = psutil.Process(pid).name()
				if name == "idle": return
			except psutil.Error:
				pass
				cont = False
				name = ""
			if pid in infolist:
				getinfo = infolist[pid]

			if search and not found:
				if cls.detailed and pid == cls.detailed_pid:
						det_cpu = getinfo["cpu_percent"]
				if "username" in getinfo and isinstance(getinfo["username"], float): getinfo["username"] = ""
				if "cmdline" in getinfo and isinstance(getinfo["cmdline"], float): getinfo["cmdline"] = ""
				for value in [ name, str(pid), getinfo.get("username", ""), " ".join(getinfo.get("cmdline", "")) ]:
					if not cls.case_sensitive:
						value = value.lower()
					for s in search:
						if s in value:
							found = True
							break
					else: continue
					break
				else: cont = False
			if cont:
				if getinfo:
					if getinfo["num_threads"] == err: threads = 0
					else: threads = getinfo["num_threads"]
					if getinfo["username"] == err: username = ""
					else: username = getinfo["username"]
					cpu = getinfo["cpu_percent"] if proc_per_cpu else round(getinfo["cpu_percent"] / THREADS, 2)
					mem = getinfo["memory_percent"]
					if getinfo["cmdline"] == err: cmd = ""
					else: cmd = " ".join(getinfo["cmdline"]) or "[" + getinfo["name"] + "]"
					if CONFIG.proc_mem_bytes and hasattr(getinfo["memory_info"], "rss"):
						mem_b = getinfo["memory_info"].rss
					else:
						mem_b = 0
				else:
					threads = mem_b = 0
					username = ""
					mem = cpu = 0.0

				if pid in cls.collapsed:
					collapse = cls.collapsed[pid]
				else:
					collapse = depth > CONFIG.tree_depth
					cls.collapsed[pid] = collapse

				if collapse_to and not search:
					out[collapse_to]["threads"] += threads
					out[collapse_to]["mem"] += mem
					out[collapse_to]["mem_b"] += mem_b
					out[collapse_to]["cpu"] += cpu
				else:
					if pid in tree and len(tree[pid]) > 0:
						sign: str = "+" if collapse else "-"
						inindent = inindent.replace(" ├─ ", "[" + sign + "]─").replace(" └─ ", "[" + sign + "]─")
					out[pid] = {
						"indent" : inindent,
						"name": name,
						"cmd" : cmd.replace("\n", "").replace("\t", "").replace("\\", ""),
						"threads" : threads,
						"username" : username,
						"mem" : mem,
						"mem_b" : mem_b,
						"cpu" : cpu,
						"depth" : depth,
						}

			if search: collapse = False
			elif collapse and not collapse_to:
				collapse_to = pid

			if pid not in tree:
				return
			children = tree[pid][:-1]

			for child in children:
				create_tree(child, tree, indent + " │ ", indent + " ├─ ", found=found, depth=depth+1, collapse_to=collapse_to)
			create_tree(tree[pid][-1], tree, indent + "  ", indent + " └─ ", depth=depth+1, collapse_to=collapse_to)

		create_tree(min(tree), tree)
		cls.det_cpu = det_cpu

		if cls.collect_interrupt: return
		if cls.tree_counter >= 100:
			cls.tree_counter = 0
			for pid in list(cls.collapsed):
				if not psutil.pid_exists(pid):
					del cls.collapsed[pid]
		cls.num_procs = len(out)
		cls.processes = out.copy()

	@classmethod
	def sorting(cls, key: str):
		index: int = CONFIG.sorting_options.index(CONFIG.proc_sorting) + (1 if key in ["right", "l"] else -1)
		if index >= len(CONFIG.sorting_options): index = 0
		elif index < 0: index = len(CONFIG.sorting_options) - 1
		CONFIG.proc_sorting = CONFIG.sorting_options[index]
		if "left" in Key.mouse: del Key.mouse["left"]
		Collector.collect(ProcCollector, interrupt=True, redraw=True)

	@classmethod
	def _draw(cls):
		ProcBox._draw_fg()

class Menu:
	'''Holds all menus'''
	active: bool = False
	close: bool = False
	resized: bool = True
	menus: Dict[str, Dict[str, str]] = {}
	menu_length: Dict[str, int] = {}
	background: str = ""
	for name, menu in MENUS.items():
		menu_length[name] = len(menu["normal"][0])
		menus[name] = {}
		for sel in ["normal", "selected"]:
			menus[name][sel] = ""
			for i in range(len(menu[sel])):
				menus[name][sel] += Fx.trans(f'{Color.fg(MENU_COLORS[sel][i])}{menu[sel][i]}')
				if i < len(menu[sel]) - 1: menus[name][sel] += f'{Mv.d(1)}{Mv.l(len(menu[sel][i]))}'

	@classmethod
	def main(cls):
		if Term.width < 80 or Term.height < 24:
			errlog.warning(f'The menu system only works on a terminal size of 80x24 or above!')
			return
		out: str = ""
		banner: str = ""
		redraw: bool = True
		key: str = ""
		mx: int = 0
		my: int = 0
		skip: bool = False
		mouse_over: bool = False
		mouse_items: Dict[str, Dict[str, int]] = {}
		cls.active = True
		cls.resized = True
		menu_names: List[str] = list(cls.menus.keys())
		menu_index: int = 0
		menu_current: str = menu_names[0]
		cls.background = f'{THEME.inactive_fg}' + Fx.uncolor(f'{Draw.saved_buffer()}') + f'{Term.fg}'

		while not cls.close:
			key = ""
			if cls.resized:
				banner = (f'{Banner.draw(Term.height // 2 - 10, center=True)}{Mv.d(1)}{Mv.l(46)}{Colors.black_bg}{Colors.default}{Fx.b}← esc'
					f'{Mv.r(30)}{Fx.i}Version: {VERSION}{Fx.ui}{Fx.ub}{Term.bg}{Term.fg}')
				if UpdateChecker.version != VERSION:
					banner += f'{Mv.to(Term.height, 1)}{Fx.b}{THEME.title}New release {UpdateChecker.version} available at https://github.com/aristocratos/bpytop{Fx.ub}{Term.fg}'
				cy = 0
				for name, menu in cls.menus.items():
					ypos = Term.height // 2 - 2 + cy
					xpos = Term.width // 2 - (cls.menu_length[name] // 2)
					mouse_items[name] = { "x1" : xpos, "x2" : xpos + cls.menu_length[name] - 1, "y1" : ypos, "y2" : ypos + 2 }
					cy += 3
				redraw = True
				cls.resized = False

			if redraw:
				out = ""
				for name, menu in cls.menus.items():
					out += f'{Mv.to(mouse_items[name]["y1"], mouse_items[name]["x1"])}{menu["selected" if name == menu_current else "normal"]}'

			if skip and redraw:
				Draw.now(out)
			elif not skip:
				Draw.now(f'{cls.background}{banner}{out}')
			skip = redraw = False

			if Key.input_wait(Timer.left(), mouse=True):
				if Key.mouse_moved():
					mx, my = Key.get_mouse()
					for name, pos in mouse_items.items():
						if pos["x1"] <= mx <= pos["x2"] and pos["y1"] <= my <= pos["y2"]:
							mouse_over = True
							if name != menu_current:
								menu_current = name
								menu_index = menu_names.index(name)
								redraw = True
							break
					else:
						mouse_over = False
				else:
					key = Key.get()

				if key == "mouse_click" and not mouse_over:
					key = "M"

				if key == "q":
					clean_quit()
				elif key in ["escape", "M"]:
					cls.close = True
					break
				elif key in ["up", "mouse_scroll_up", "shift_tab"]:
					menu_index -= 1
					if menu_index < 0: menu_index = len(menu_names) - 1
					menu_current = menu_names[menu_index]
					redraw = True
				elif key in ["down", "mouse_scroll_down", "tab"]:
					menu_index += 1
					if menu_index > len(menu_names) - 1: menu_index = 0
					menu_current = menu_names[menu_index]
					redraw = True
				elif key == "enter" or (key == "mouse_click" and mouse_over):
					if menu_current == "quit":
						clean_quit()
					elif menu_current == "options":
						cls.options()
						cls.resized = True
					elif menu_current == "help":
						cls.help()
						cls.resized = True

			if Timer.not_zero() and not cls.resized:
				skip = True
			else:
				Collector.collect()
				Collector.collect_done.wait(2)
				if CONFIG.background_update: cls.background = f'{THEME.inactive_fg}' + Fx.uncolor(f'{Draw.saved_buffer()}') + f'{Term.fg}'
				Timer.stamp()


		Draw.now(f'{Draw.saved_buffer()}')
		cls.background = ""
		cls.active = False
		cls.close = False

	@classmethod
	def help(cls):
		if Term.width < 80 or Term.height < 24:
			errlog.warning(f'The menu system only works on a terminal size of 80x24 or above!')
			return
		out: str = ""
		out_misc : str = ""
		redraw: bool = True
		key: str = ""
		skip: bool = False
		main_active: bool = cls.active
		cls.active = True
		cls.resized = True
		if not cls.background:
			cls.background = f'{THEME.inactive_fg}' + Fx.uncolor(f'{Draw.saved_buffer()}') + f'{Term.fg}'
		help_items: Dict[str, str] = {
			"(Mouse 1)" : "Clicks buttons and selects in process list.",
			"Selected (Mouse 1)" : "Show detailed information for selected process.",
			"(Mouse scroll)" : "Scrolls any scrollable list/text under cursor.",
			"(Esc, shift+m)" : "Toggles main menu.",
			"(m)" : "Cycle view presets, order: full->proc->stat->user.",
			"(1)" : "Toggle CPU box.",
			"(2)" : "Toggle MEM box.",
			"(3)" : "Toggle NET box.",
			"(4)" : "Toggle PROC box.",
			"(d)" : "Toggle disks view in MEM box.",
			"(F2, o)" : "Shows options.",
			"(F1, shift+h)" : "Shows this window.",
			"(ctrl+z)" : "Sleep program and put in background.",
			"(ctrl+c, q)" : "Quits program.",
			"(+) / (-)" : "Add/Subtract 100ms to/from update timer.",
			"(Up, k) (Down, j)" : "Select in process list.",
			"(Enter)" : "Show detailed information for selected process.",
			"(Spacebar)" : "Expand/collapse the selected process in tree view.",
			"(Pg Up) (Pg Down)" : "Jump 1 page in process list.",
			"(Home) (End)" : "Jump to first or last page in process list.",
			"(Left, h) (Right, l)" : "Select previous/next sorting column.",
			"(b) (n)" : "Select previous/next network device.",
			"(s)" : "Toggle showing swap as a disk.",
			"(i)" : "Toggle disks io mode with big graphs.",
			"(z)" : "Toggle totals reset for current network device",
			"(a)" : "Toggle auto scaling for the network graphs.",
			"(y)" : "Toggle synced scaling mode for network graphs.",
			"(f)" : "Input a NON case-sensitive process filter.",
			"(shift+f)" : "Input a case-sensitive process filter.",
			"(c)" : "Toggle per-core cpu usage of processes.",
			"(r)" : "Reverse sorting order in processes box.",
			"(e)" : "Toggle processes tree view.",
			"(delete)" : "Clear any entered filter.",
			"Selected (shift+t)" : "Terminate selected process with SIGTERM - 15.",
			"Selected (shift+k)" : "Kill selected process with SIGKILL - 9.",
			"Selected (shift+i)" : "Interrupt selected process with SIGINT - 2.",
			"_1" : " ",
			"_2" : "For bug reporting and project updates, visit:",
			"_3" : "https://github.com/aristocratos/bpytop",
		}

		while not cls.close:
			key = ""
			if cls.resized:
				y = 8 if Term.height < len(help_items) + 10 else Term.height // 2 - len(help_items) // 2 + 4
				out_misc = (f'{Banner.draw(y-7, center=True)}{Mv.d(1)}{Mv.l(46)}{Colors.black_bg}{Colors.default}{Fx.b}← esc'
					f'{Mv.r(30)}{Fx.i}Version: {VERSION}{Fx.ui}{Fx.ub}{Term.bg}{Term.fg}')
				x = Term.width//2-36
				h, w = Term.height-2-y, 72
				if len(help_items) > h:
					pages = ceil(len(help_items) / h)
				else:
					h = len(help_items)
					pages = 0
				page = 1
				out_misc += create_box(x, y, w, h+3, "help", line_color=THEME.div_line)
				redraw = True
				cls.resized = False

			if redraw:
				out = ""
				cy = 0
				if pages:
					out += (f'{Mv.to(y, x+56)}{THEME.div_line(Symbol.title_left)}{Fx.b}{THEME.title("pg")}{Fx.ub}{THEME.main_fg(Symbol.up)} {Fx.b}{THEME.title}{page}/{pages} '
					f'pg{Fx.ub}{THEME.main_fg(Symbol.down)}{THEME.div_line(Symbol.title_right)}')
				out += f'{Mv.to(y+1, x+1)}{THEME.title}{Fx.b}{"Keys:":^20}Description:{THEME.main_fg}'
				for n, (keys, desc) in enumerate(help_items.items()):
					if pages and n < (page - 1) * h: continue
					out += f'{Mv.to(y+2+cy, x+1)}{Fx.b}{("" if keys.startswith("_") else keys):^20.20}{Fx.ub}{desc:50.50}'
					cy += 1
					if cy == h: break
				if cy < h:
					for i in range(h-cy):
						out += f'{Mv.to(y+2+cy+i, x+1)}{" " * (w-2)}'

			if skip and redraw:
				Draw.now(out)
			elif not skip:
				Draw.now(f'{cls.background}{out_misc}{out}')
			skip = redraw = False

			if Key.input_wait(Timer.left()):
				key = Key.get()

				if key == "mouse_click":
					mx, my = Key.get_mouse()
					if x <= mx < x + w and y <= my < y + h + 3:
						if pages and my == y and x + 56 <  mx < x + 61:
							key = "up"
						elif pages and my == y and x + 63 < mx < x + 68:
							key = "down"
					else:
						key = "escape"

				if key == "q":
					clean_quit()
				elif key in ["escape", "M", "enter", "backspace", "H", "f1"]:
					cls.close = True
					break
				elif key in ["up", "mouse_scroll_up", "page_up"] and pages:
					page -= 1
					if page < 1: page = pages
					redraw = True
				elif key in ["down", "mouse_scroll_down", "page_down"] and pages:
					page += 1
					if page > pages: page = 1
					redraw = True

			if Timer.not_zero() and not cls.resized:
				skip = True
			else:
				Collector.collect()
				Collector.collect_done.wait(2)
				if CONFIG.background_update: cls.background = f'{THEME.inactive_fg}' + Fx.uncolor(f'{Draw.saved_buffer()}') + f'{Term.fg}'
				Timer.stamp()

		if main_active:
			cls.close = False
			return
		Draw.now(f'{Draw.saved_buffer()}')
		cls.background = ""
		cls.active = False
		cls.close = False

	@classmethod
	def options(cls):
		if Term.width < 80 or Term.height < 24:
			errlog.warning(f'The menu system only works on a terminal size of 80x24 or above!')
			return
		out: str = ""
		out_misc : str = ""
		redraw: bool = True
		selected_cat: str = ""
		selected_int: int = 0
		option_items: Dict[str, List[str]] = {}
		cat_list: List[str] = []
		cat_int: int = 0
		change_cat: bool = False
		key: str = ""
		skip: bool = False
		main_active: bool = cls.active
		cls.active = True
		cls.resized = True
		d_quote: str
		inputting: bool = False
		input_val: str = ""
		Theme.refresh()
		if not cls.background:
			cls.background = f'{THEME.inactive_fg}' + Fx.uncolor(f'{Draw.saved_buffer()}') + f'{Term.fg}'
		categories: Dict[str, Dict[str, List[str]]] = {
			"system" : {
				"color_theme" : [
					'Set color theme.',
					'',
					'Choose from all theme files in',
					'"/usr/[local/]share/bpytop/themes" and',
					'"~/.config/bpytop/themes".',
					'',
					'"Default" for builtin default theme.',
					'User themes are prefixed by a plus sign "+".',
					'',
					'For theme updates see:',
					'https://github.com/aristocratos/bpytop'],
				"theme_background" : [
					'If the theme set background should be shown.',
					'',
					'Set to False if you want terminal background',
					'transparency.'],
				"truecolor" : [
					'Sets if 24-bit truecolor should be used.',
					'(Requires restart to take effect!)',
					'',
					'Will convert 24-bit colors to 256 color',
					'(6x6x6 color cube) if False.',
					'',
					'Set to False if your terminal doesn\'t have',
					'truecolor support and can\'t convert to',
					'256-color.'],
				"shown_boxes" : [
					'Manually set which boxes to show.',
					'',
					'Available values are "cpu mem net proc".',
					'Seperate values with whitespace.',
					'',
					'Toggle between presets with mode key "m".'],
				"update_ms" : [
					'Update time in milliseconds.',
					'',
					'Recommended 2000 ms or above for better sample',
					'times for graphs.',
					'',
					'Min value: 100 ms',
					'Max value: 86400000 ms = 24 hours.'],
				"draw_clock" : [
					'Draw a clock at top of screen.',
					'(Only visible if cpu box is enabled!)',
					'',
					'Formatting according to strftime, empty',
					'string to disable.',
					'',
					'Custom formatting options:',
					'"/host" = hostname',
					'"/user" = username',
					'"/uptime" = system uptime',
					'',
					'Examples of strftime formats:',
					'"%X" = locale HH:MM:SS',
					'"%H" = 24h hour, "%I" = 12h hour',
					'"%M" = minute, "%S" = second',
					'"%d" = day, "%m" = month, "%y" = year'],
				"background_update" : [
					'Update main ui when menus are showing.',
					'',
					'True or False.',
					'',
					'Set this to false if the menus is flickering',
					'too much for a comfortable experience.'],
				"show_battery" : [
					'Show battery stats.',
					'(Only visible if cpu box is enabled!)',
					'',
					'Show battery stats in the top right corner',
					'if a battery is present.'],
				"show_init" : [
					'Show init screen at startup.',
					'',
					'The init screen is purely cosmetical and',
					'slows down start to show status messages.'],
				"update_check" : [
					'Check for updates at start.',
					'',
					'Checks for latest version from:',
					'https://github.com/aristocratos/bpytop'],
				"log_level" : [
					'Set loglevel for error.log',
					'',
					'Levels are: "ERROR" "WARNING" "INFO" "DEBUG".',
					'The level set includes all lower levels,',
					'i.e. "DEBUG" will show all logging info.']
			},
			"cpu" : {
				"cpu_graph_upper" : [
					'Sets the CPU stat shown in upper half of',
					'the CPU graph.',
					'',
					'"total" = Total cpu usage.',
					'"user" = User mode cpu usage.',
					'"system" = Kernel mode cpu usage.',
					'See:',
					'https://psutil.readthedocs.io/en/latest/',
					'#psutil.cpu_times',
					'for attributes available on specific platforms.'],
				"cpu_graph_lower" : [
					'Sets the CPU stat shown in lower half of',
					'the CPU graph.',
					'',
					'"total" = Total cpu usage.',
					'"user" = User mode cpu usage.',
					'"system" = Kernel mode cpu usage.',
					'See:',
					'https://psutil.readthedocs.io/en/latest/',
					'#psutil.cpu_times',
					'for attributes available on specific platforms.'],
				"cpu_invert_lower" : [
						'Toggles orientation of the lower CPU graph.',
						'',
						'True or False.'],
				"cpu_single_graph" : [
						'Completely disable the lower CPU graph.',
						'',
						'Shows only upper CPU graph and resizes it',
						'to fit to box height.',
						'',
						'True or False.'],
				"check_temp" : [
					'Enable cpu temperature reporting.',
					'',
					'True or False.'],
				"cpu_sensor" : [
					'Cpu temperature sensor',
					'',
					'Select the sensor that corresponds to',
					'your cpu temperature.',
					'Set to "Auto" for auto detection.'],
				"show_coretemp" : [
					'Show temperatures for cpu cores.',
					'',
					'Only works if check_temp is True and',
					'the system is reporting core temps.'],

				"custom_cpu_name" : [
					'Custom cpu model name in cpu percentage box.',
					'',
					'Empty string to disable.'],
				"show_uptime" : [
					'Shows the system uptime in the CPU box.',
					'',
					'Can also be shown in the clock by using',
					'"/uptime" in the formatting.',
					'',
					'True or False.'],
			},
			"mem" : {
				"mem_graphs" : [
					'Show graphs for memory values.',
					'',
					'True or False.'],
				"show_disks" : [
					'Split memory box to also show disks.',
					'',
					'True or False.'],
				"show_io_stat" : [
					'Toggle small IO stat graphs.',
					'',
					'Toggles the small IO graphs for the regular',
					'disk usage view.',
					'',
					'True or False.'],
				"io_mode" : [
					'Toggles io mode for disks.',
					'',
					'Shows big graphs for disk read/write speeds',
					'instead of used/free percentage meters.',
					'',
					'True or False.'],
				"io_graph_combined" : [
					'Toggle combined read and write graphs.',
					'',
					'Only has effect if "io mode" is True.',
					'',
					'True or False.'],
				"io_graph_speeds" : [
					'Set top speeds for the io graphs.',
					'',
					'Manually set which speed in MiB/s that equals',
					'100 percent in the io graphs.',
					'(10 MiB/s by default).',
					'',
					'Format: "device:speed" seperate disks with a',
					'comma ",".',
					'',
					'Example: "/dev/sda:100, /dev/sdb:20".'],
				"show_swap" : [
					'If swap memory should be shown in memory box.',
					'',
					'True or False.'],
				"swap_disk" : [
					'Show swap as a disk.',
					'',
					'Ignores show_swap value above.',
					'Inserts itself after first disk.'],
				"only_physical" : [
					'Filter out non physical disks.',
					'',
					'Set this to False to include network disks,',
					'RAM disks and similar.',
					'',
					'True or False.'],
				"use_fstab" : [
					'Read disks list from /etc/fstab.',
					'(Has no effect on macOS X)',
					'',
					'This also disables only_physical.',
					'',
					'True or False.'],
				"disks_filter" : [
					'Optional filter for shown disks.',
					'',
					'Should be full path of a mountpoint,',
					'"root" replaces "/", separate multiple values',
					'with a comma ",".',
					'Begin line with "exclude=" to change to exclude',
					'filter.',
					'Oterwise defaults to "most include" filter.',
					'',
					'Example: disks_filter="exclude=/boot, /home/user"'],
			},
			"net" : {
				"net_download" : [
					'Fixed network graph download value.',
					'',
					'Default "10M" = 10 MibiBytes.',
					'Possible units:',
					'"K" (KiB), "M" (MiB), "G" (GiB).',
					'',
					'Append "bit" for bits instead of bytes,',
					'i.e "100Mbit"',
					'',
					'Can be toggled with auto button.'],
				"net_upload" : [
					'Fixed network graph upload value.',
					'',
					'Default "10M" = 10 MibiBytes.',
					'Possible units:',
					'"K" (KiB), "M" (MiB), "G" (GiB).',
					'',
					'Append "bit" for bits instead of bytes,',
					'i.e "100Mbit"',
					'',
					'Can be toggled with auto button.'],
				"net_auto" : [
					'Start in network graphs auto rescaling mode.',
					'',
					'Ignores any values set above at start and',
					'rescales down to 10KibiBytes at the lowest.',
					'',
					'True or False.'],
				"net_sync" : [
					'Network scale sync.',
					'',
					'Syncs the scaling for download and upload to',
					'whichever currently has the highest scale.',
					'',
					'True or False.'],
				"net_color_fixed" : [
					'Set network graphs color gradient to fixed.',
					'',
					'If True the network graphs color is based',
					'on the total bandwidth usage instead of',
					'the current autoscaling.',
					'',
					'The bandwidth usage is based on the',
					'"net_download" and "net_upload" values set',
					'above.'],
				"net_iface" : [
					'Network Interface.',
					'',
					'Manually set the starting Network Interface.',
					'Will otherwise automatically choose the NIC',
					'with the highest total download since boot.'],
			},
			"proc" : {
				"proc_update_mult" : [
					'Processes update multiplier.',
					'Sets how often the process list is updated as',
					'a multiplier of "update_ms".',
					'',
					'Set to 2 or higher to greatly decrease bpytop',
					'cpu usage. (Only integers)'],
				"proc_sorting" : [
					'Processes sorting option.',
					'',
					'Possible values: "pid", "program", "arguments",',
					'"threads", "user", "memory", "cpu lazy" and',
					'"cpu responsive".',
					'',
					'"cpu lazy" updates top process over time,',
					'"cpu responsive" updates top process directly.'],
				"proc_reversed" : [
					'Reverse processes sorting order.',
					'',
					'True or False.'],
				"proc_tree" : [
					'Processes tree view.',
					'',
					'Set true to show processes grouped by parents,',
					'with lines drawn between parent and child',
					'process.'],
				"tree_depth" : [
					'Process tree auto collapse depth.',
					'',
					'Sets the depth were the tree view will auto',
					'collapse processes at.'],
				"proc_colors" : [
					'Enable colors in process view.',
					'',
					'Uses the cpu graph gradient colors.'],
				"proc_gradient" : [
					'Enable process view gradient fade.',
					'',
					'Fades from top or current selection.',
					'Max fade value is equal to current themes',
					'"inactive_fg" color value.'],
				"proc_per_core" : [
					'Process usage per core.',
					'',
					'If process cpu usage should be of the core',
					'it\'s running on or usage of the total',
					'available cpu power.',
					'',
					'If true and process is multithreaded',
					'cpu usage can reach over 100%.'],
				"proc_mem_bytes" : [
					'Show memory as bytes in process list.',
					' ',
					'True or False.'],
			}
		}

		loglevel_i: int = CONFIG.log_levels.index(CONFIG.log_level)
		cpu_sensor_i: int = CONFIG.cpu_sensors.index(CONFIG.cpu_sensor)
		cpu_graph_i: Dict[str, int] = { "cpu_graph_upper" : CONFIG.cpu_percent_fields.index(CONFIG.cpu_graph_upper),
										"cpu_graph_lower" : CONFIG.cpu_percent_fields.index(CONFIG.cpu_graph_lower)}
		color_i: int
		max_opt_len: int = max([len(categories[x]) for x in categories]) * 2
		cat_list = list(categories)
		while not cls.close:
			key = ""
			if cls.resized or change_cat:
				cls.resized = change_cat = False
				selected_cat = list(categories)[cat_int]
				option_items = categories[cat_list[cat_int]]
				option_len: int = len(option_items) * 2
				y = 12 if Term.height < max_opt_len + 13 else Term.height // 2 - max_opt_len // 2 + 7
				out_misc = (f'{Banner.draw(y-10, center=True)}{Mv.d(1)}{Mv.l(46)}{Colors.black_bg}{Colors.default}{Fx.b}← esc'
					f'{Mv.r(30)}{Fx.i}Version: {VERSION}{Fx.ui}{Fx.ub}{Term.bg}{Term.fg}')
				x = Term.width//2-38
				x2 = x + 27
				h, w, w2 = min(Term.height-1-y, option_len), 26, 50
				h -= h % 2
				color_i = list(Theme.themes).index(THEME.current)
				out_misc += create_box(x, y - 3, w+w2+1, 3, f'tab{Symbol.right}', line_color=THEME.div_line)
				out_misc += create_box(x, y, w, h+2, "options", line_color=THEME.div_line)
				redraw = True

				cat_width = floor((w+w2) / len(categories))
				out_misc += f'{Fx.b}'
				for cx, cat in enumerate(categories):
					out_misc += f'{Mv.to(y-2, x + 1 + (cat_width * cx) + round(cat_width / 2 - len(cat) / 2 ))}'
					if cat == selected_cat:
						out_misc += f'{THEME.hi_fg}[{THEME.title}{Fx.u}{cat}{Fx.uu}{THEME.hi_fg}]'
					else:
						out_misc += f'{THEME.hi_fg}{SUPERSCRIPT[cx+1]}{THEME.title}{cat}'
				out_misc += f'{Fx.ub}'
				if option_len > h:
					pages = ceil(option_len / h)
				else:
					h = option_len
					pages = 0
				page = pages if selected_int == -1 and pages > 0 else 1
				selected_int = 0 if selected_int >= 0 else len(option_items) - 1
			if redraw:
				out = ""
				cy = 0

				selected = list(option_items)[selected_int]
				if pages:
					out += (f'{Mv.to(y+h+1, x+11)}{THEME.div_line(Symbol.title_left)}{Fx.b}{THEME.title("pg")}{Fx.ub}{THEME.main_fg(Symbol.up)} {Fx.b}{THEME.title}{page}/{pages} '
					f'pg{Fx.ub}{THEME.main_fg(Symbol.down)}{THEME.div_line(Symbol.title_right)}')
				#out += f'{Mv.to(y+1, x+1)}{THEME.title}{Fx.b}{"Keys:":^20}Description:{THEME.main_fg}'
				for n, opt in enumerate(option_items):
					if pages and n < (page - 1) * ceil(h / 2): continue
					value = getattr(CONFIG, opt)
					t_color = f'{THEME.selected_bg}{THEME.selected_fg}' if opt == selected else f'{THEME.title}'
					v_color	= "" if opt == selected else f'{THEME.title}'
					d_quote = '"' if isinstance(value, str) else ""
					if opt == "color_theme":
						counter = f' {color_i + 1}/{len(Theme.themes)}'
					elif opt == "proc_sorting":
						counter = f' {CONFIG.sorting_options.index(CONFIG.proc_sorting) + 1}/{len(CONFIG.sorting_options)}'
					elif opt == "log_level":
						counter = f' {loglevel_i + 1}/{len(CONFIG.log_levels)}'
					elif opt == "cpu_sensor":
						counter = f' {cpu_sensor_i + 1}/{len(CONFIG.cpu_sensors)}'
					elif opt in ["cpu_graph_upper", "cpu_graph_lower"]:
						counter = f' {cpu_graph_i[opt] + 1}/{len(CONFIG.cpu_percent_fields)}'
					else:
						counter = ""
					out += f'{Mv.to(y+1+cy, x+1)}{t_color}{Fx.b}{opt.replace("_", " ").capitalize() + counter:^24.24}{Fx.ub}{Mv.to(y+2+cy, x+1)}{v_color}'
					if opt == selected:
						if isinstance(value, bool) or opt in ["color_theme", "proc_sorting", "log_level", "cpu_sensor", "cpu_graph_upper", "cpu_graph_lower"]:
							out += f'{t_color} {Symbol.left}{v_color}{d_quote + str(value) + d_quote:^20.20}{t_color}{Symbol.right} '
						elif inputting:
							out += f'{str(input_val)[-17:] + Fx.bl + "█" + Fx.ubl + "" + Symbol.enter:^33.33}'
						else:
							out += ((f'{t_color} {Symbol.left}{v_color}' if type(value) is int else "  ") +
							f'{str(value) + " " + Symbol.enter:^20.20}' + (f'{t_color}{Symbol.right} ' if type(value) is int else "  "))
					else:
						out += f'{d_quote + str(value) + d_quote:^24.24}'
					out += f'{Term.bg}'
					if opt == selected:
						h2 = len(option_items[opt]) + 2
						y2 = y + (selected_int * 2) - ((page-1) * h)
						if y2 + h2 > Term.height: y2 = Term.height - h2
						out += f'{create_box(x2, y2, w2, h2, "description", line_color=THEME.div_line)}{THEME.main_fg}'
						for n, desc in enumerate(option_items[opt]):
							out += f'{Mv.to(y2+1+n, x2+2)}{desc:.48}'
					cy += 2
					if cy >= h: break
				if cy < h:
					for i in range(h-cy):
						out += f'{Mv.to(y+1+cy+i, x+1)}{" " * (w-2)}'


			if not skip or redraw:
				Draw.now(f'{cls.background}{out_misc}{out}')
			skip = redraw = False

			if Key.input_wait(Timer.left()):
				key = Key.get()
				redraw = True
				has_sel = False
				if key == "mouse_click" and not inputting:
					mx, my = Key.get_mouse()
					if x < mx < x + w + w2 and y - 4 < my < y:
						# if my == y - 2:
						for cx, cat in enumerate(categories):
							ccx = x + (cat_width * cx) + round(cat_width / 2 - len(cat) / 2 )
							if ccx - 2 < mx < ccx + 2 + len(cat):
								key = str(cx+1)
								break
					elif x < mx < x + w and y < my < y + h + 2:
						mouse_sel = ceil((my - y) / 2) - 1 + ceil((page-1) * (h / 2))
						if pages and my == y+h+1 and x+11 < mx < x+16:
							key = "page_up"
						elif pages and my == y+h+1 and x+19 < mx < x+24:
							key = "page_down"
						elif my == y+h+1:
							pass
						elif mouse_sel == selected_int:
							if mx < x + 6:
								key = "left"
							elif mx > x + 19:
								key = "right"
							else:
								key = "enter"
						elif mouse_sel < len(option_items):
							selected_int = mouse_sel
							has_sel = True
					else:
						key = "escape"
				if inputting:
					if key in ["escape", "mouse_click"]:
						inputting = False
					elif key == "enter":
						inputting = False
						if str(getattr(CONFIG, selected)) != input_val:
							if selected == "update_ms":
								if not input_val or int(input_val) < 100:
									CONFIG.update_ms = 100
								elif int(input_val) > 86399900:
									CONFIG.update_ms = 86399900
								else:
									CONFIG.update_ms = int(input_val)
							elif selected == "proc_update_mult":
								if not input_val or int(input_val) < 1:
									CONFIG.proc_update_mult = 1
								else:
									CONFIG.proc_update_mult = int(input_val)
								Collector.proc_counter = 1
							elif selected == "tree_depth":
								if not input_val or int(input_val) < 0:
									CONFIG.tree_depth = 0
								else:
									CONFIG.tree_depth = int(input_val)
								ProcCollector.collapsed = {}
							elif selected == "shown_boxes":
								new_boxes: List = []
								for box in input_val.split():
									if box in ["cpu", "mem", "net", "proc"]:
										new_boxes.append(box)
								CONFIG.shown_boxes = " ".join(new_boxes)
								Box.view_mode = "user"
								Box.view_modes["user"] = CONFIG.shown_boxes.split()
								Draw.clear(saved=True)
							elif isinstance(getattr(CONFIG, selected), str):
								setattr(CONFIG, selected, input_val)
								if selected.startswith("net_"):
									NetCollector.net_min = {"download" : -1, "upload" : -1}
								elif selected == "draw_clock":
									Box.clock_on = len(CONFIG.draw_clock) > 0
									if not Box.clock_on: Draw.clear("clock", saved=True)
								elif selected == "io_graph_speeds":
									MemBox.graph_speeds = {}
							Term.refresh(force=True)
							cls.resized = False
					elif key == "backspace" and len(input_val):
						input_val = input_val[:-1]
					elif key == "delete":
							input_val = ""
					elif isinstance(getattr(CONFIG, selected), str) and len(key) == 1:
						input_val += key
					elif isinstance(getattr(CONFIG, selected), int) and key.isdigit():
						input_val += key
				elif key == "q":
					clean_quit()
				elif key in ["escape", "o", "M", "f2"]:
					cls.close = True
					break
				elif key == "tab" or (key == "down" and selected_int == len(option_items) - 1 and (page == pages or pages == 0)):
					if cat_int == len(categories) - 1:
						cat_int = 0
					else:
						cat_int += 1
					change_cat = True
				elif key == "shift_tab" or (key == "up" and selected_int == 0 and page == 1):
					if cat_int == 0:
						cat_int = len(categories) - 1
					else:
						cat_int -= 1
					change_cat = True
					selected_int = -1 if key != "shift_tab" else 0
				elif key in list(map(str, range(1, len(cat_list)+1))) and key != str(cat_int + 1):
					cat_int = int(key) - 1
					change_cat = True
				elif key == "enter" and selected in ["update_ms", "disks_filter", "custom_cpu_name", "net_download",
					 "net_upload", "draw_clock", "tree_depth", "proc_update_mult", "shown_boxes", "net_iface", "io_graph_speeds"]:
					inputting = True
					input_val = str(getattr(CONFIG, selected))
				elif key == "left" and selected == "update_ms" and CONFIG.update_ms - 100 >= 100:
					CONFIG.update_ms -= 100
					Box.draw_update_ms()
				elif key == "right" and selected == "update_ms" and CONFIG.update_ms + 100 <= 86399900:
					CONFIG.update_ms += 100
					Box.draw_update_ms()
				elif key == "left" and selected == "proc_update_mult" and CONFIG.proc_update_mult > 1:
					CONFIG.proc_update_mult -= 1
					Collector.proc_counter = 1
				elif key == "right" and selected == "proc_update_mult":
					CONFIG.proc_update_mult += 1
					Collector.proc_counter = 1
				elif key == "left" and selected == "tree_depth" and CONFIG.tree_depth > 0:
					CONFIG.tree_depth -= 1
					ProcCollector.collapsed = {}
				elif key == "right" and selected == "tree_depth":
					CONFIG.tree_depth += 1
					ProcCollector.collapsed = {}
				elif key in ["left", "right"] and isinstance(getattr(CONFIG, selected), bool):
					setattr(CONFIG, selected, not getattr(CONFIG, selected))
					if selected == "check_temp":
						if CONFIG.check_temp:
							CpuCollector.get_sensors()
						else:
							CpuCollector.sensor_method = ""
							CpuCollector.got_sensors = False
					if selected in ["net_auto", "net_color_fixed", "net_sync"]:
						if selected == "net_auto": NetCollector.auto_min = CONFIG.net_auto
						NetBox.redraw = True
					if selected == "theme_background":
						Term.bg = f'{THEME.main_bg}' if CONFIG.theme_background else "\033[49m"
						Draw.now(Term.bg)
					if selected == "show_battery":
						Draw.clear("battery", saved=True)
					Term.refresh(force=True)
					cls.resized = False
				elif key in ["left", "right"] and selected == "color_theme" and len(Theme.themes) > 1:
					if key == "left":
						color_i -= 1
						if color_i < 0: color_i = len(Theme.themes) - 1
					elif key == "right":
						color_i += 1
						if color_i > len(Theme.themes) - 1: color_i = 0
					Collector.collect_idle.wait()
					CONFIG.color_theme = list(Theme.themes)[color_i]
					THEME(CONFIG.color_theme)
					Term.refresh(force=True)
					Timer.finish()
				elif key in ["left", "right"] and selected == "proc_sorting":
					ProcCollector.sorting(key)
				elif key in ["left", "right"] and selected == "log_level":
					if key == "left":
						loglevel_i -= 1
						if loglevel_i < 0: loglevel_i = len(CONFIG.log_levels) - 1
					elif key == "right":
						loglevel_i += 1
						if loglevel_i > len(CONFIG.log_levels) - 1: loglevel_i = 0
					CONFIG.log_level = CONFIG.log_levels[loglevel_i]
					errlog.setLevel(getattr(logging, CONFIG.log_level))
					errlog.info(f'Loglevel set to {CONFIG.log_level}')
				elif key in ["left", "right"] and selected in ["cpu_graph_upper", "cpu_graph_lower"]:
					if key == "left":
						cpu_graph_i[selected] -= 1
						if cpu_graph_i[selected] < 0: cpu_graph_i[selected] = len(CONFIG.cpu_percent_fields) - 1
					if key == "right":
						cpu_graph_i[selected] += 1
						if cpu_graph_i[selected] > len(CONFIG.cpu_percent_fields) - 1: cpu_graph_i[selected] = 0
					setattr(CONFIG, selected, CONFIG.cpu_percent_fields[cpu_graph_i[selected]])
					setattr(CpuCollector, selected.replace("_graph", ""), [])
					Term.refresh(force=True)
					cls.resized = False
				elif key in ["left", "right"] and selected == "cpu_sensor" and len(CONFIG.cpu_sensors) > 1:
					if key == "left":
						cpu_sensor_i -= 1
						if cpu_sensor_i < 0: cpu_sensor_i = len(CONFIG.cpu_sensors) - 1
					elif key == "right":
						cpu_sensor_i += 1
						if cpu_sensor_i > len(CONFIG.cpu_sensors) - 1: cpu_sensor_i = 0
					Collector.collect_idle.wait()
					CpuCollector.sensor_swap = True
					CONFIG.cpu_sensor = CONFIG.cpu_sensors[cpu_sensor_i]
					if CONFIG.check_temp and (CpuCollector.sensor_method != "psutil" or CONFIG.cpu_sensor == "Auto"):
						CpuCollector.get_sensors()
						Term.refresh(force=True)
						cls.resized = False
				elif key in ["up", "mouse_scroll_up"]:
					selected_int -= 1
					if selected_int < 0: selected_int = len(option_items) - 1
					page = floor(selected_int * 2 / h) + 1
				elif key in ["down", "mouse_scroll_down"]:
					selected_int += 1
					if selected_int > len(option_items) - 1: selected_int = 0
					page = floor(selected_int * 2 / h) + 1
				elif key == "page_up":
					if not pages or page == 1:
						selected_int = 0
					else:
						page -= 1
						if page < 1: page = pages
					selected_int = (page-1) * ceil(h / 2)
				elif key == "page_down":
					if not pages or page == pages:
						selected_int = len(option_items) - 1
					else:
						page += 1
						if page > pages: page = 1
						selected_int = (page-1) * ceil(h / 2)
				elif has_sel:
					pass
				else:
					redraw = False

			if Timer.not_zero() and not cls.resized:
				skip = True
			else:
				Collector.collect()
				Collector.collect_done.wait(2)
				if CONFIG.background_update: cls.background = f'{THEME.inactive_fg}' + Fx.uncolor(f'{Draw.saved_buffer()}') + f'{Term.fg}'
				Timer.stamp()

		if main_active:
			cls.close = False
			return
		Draw.now(f'{Draw.saved_buffer()}')
		cls.background = ""
		cls.active = False
		cls.close = False

class Timer:
	timestamp: float
	return_zero = False

	@classmethod
	def stamp(cls):
		cls.timestamp = time()

	@classmethod
	def not_zero(cls) -> bool:
		if cls.return_zero:
			cls.return_zero = False
			return False
		return cls.timestamp + (CONFIG.update_ms / 1000) > time()

	@classmethod
	def left(cls) -> float:
		return cls.timestamp + (CONFIG.update_ms / 1000) - time()

	@classmethod
	def finish(cls):
		cls.return_zero = True
		cls.timestamp = time() - (CONFIG.update_ms / 1000)
		Key.break_wait()

class UpdateChecker:
	version: str = VERSION
	thread: threading.Thread

	@classmethod
	def run(cls):
		cls.thread = threading.Thread(target=cls._checker)
		cls.thread.start()

	@classmethod
	def _checker(cls):
		try:
			with urllib.request.urlopen("https://github.com/aristocratos/bpytop/raw/master/bpytop.py", timeout=5) as source: # type: ignore
				for line in source:
					line = line.decode("utf-8")
					if line.startswith("VERSION: str ="):
						cls.version = line[(line.index("=")+1):].strip('" \n')
						break
		except Exception as e:
			errlog.exception(f'{e}')
		else:
			if cls.version != VERSION and which("notify-send"):
				try:
					subprocess.run(["notify-send", "-u", "normal", "BpyTop Update!",
						f'New version of BpyTop available!\nCurrent version: {VERSION}\nNew version: {cls.version}\nDownload at github.com/aristocratos/bpytop',
						"-i", "update-notifier", "-t", "10000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				except Exception as e:
					errlog.exception(f'{e}')

class Init:
	running: bool = True
	initbg_colors: List[str] = []
	initbg_data: List[int]
	initbg_up: Graph
	initbg_down: Graph
	resized = False

	@classmethod
	def start(cls):
		Draw.buffer("init", z=1)
		Draw.buffer("initbg", z=10)
		for i in range(51):
			for _ in range(2): cls.initbg_colors.append(Color.fg(i, i, i))
		Draw.buffer("banner", (f'{Banner.draw(Term.height // 2 - 10, center=True)}{Mv.d(1)}{Mv.l(11)}{Colors.black_bg}{Colors.default}'
				f'{Fx.b}{Fx.i}Version: {VERSION}{Fx.ui}{Fx.ub}{Term.bg}{Term.fg}{Color.fg("#50")}'), z=2)
		for _i in range(7):
			perc = f'{str(round((_i + 1) * 14 + 2)) + "%":>5}'
			Draw.buffer("+banner", f'{Mv.to(Term.height // 2 - 2 + _i, Term.width // 2 - 28)}{Fx.trans(perc)}{Symbol.v_line}')

		Draw.out("banner")
		Draw.buffer("+init!", f'{Color.fg("#cc")}{Fx.b}{Mv.to(Term.height // 2 - 2, Term.width // 2 - 21)}{Mv.save}')

		cls.initbg_data = [randint(0, 100) for _ in range(Term.width * 2)]
		cls.initbg_up = Graph(Term.width, Term.height // 2, cls.initbg_colors, cls.initbg_data, invert=True)
		cls.initbg_down = Graph(Term.width, Term.height // 2, cls.initbg_colors, cls.initbg_data, invert=False)

	@classmethod
	def success(cls):
		if not CONFIG.show_init or cls.resized: return
		cls.draw_bg(5)
		Draw.buffer("+init!", f'{Mv.restore}{Symbol.ok}\n{Mv.r(Term.width // 2 - 22)}{Mv.save}')

	@staticmethod
	def fail(err):
		if CONFIG.show_init:
			Draw.buffer("+init!", f'{Mv.restore}{Symbol.fail}')
			sleep(2)
		errlog.exception(f'{err}')
		clean_quit(1, errmsg=f'Error during init! See {CONFIG_DIR}/error.log for more information.')

	@classmethod
	def draw_bg(cls, times: int = 5):
		for _ in range(times):
			sleep(0.05)
			x = randint(0, 100)
			Draw.buffer("initbg", f'{Fx.ub}{Mv.to(0, 0)}{cls.initbg_up(x)}{Mv.to(Term.height // 2, 0)}{cls.initbg_down(x)}')
			Draw.out("initbg", "banner", "init")

	@classmethod
	def done(cls):
		cls.running = False
		if not CONFIG.show_init: return
		if cls.resized:
			Draw.now(Term.clear)
		else:
			cls.draw_bg(10)
		Draw.clear("initbg", "banner", "init", saved=True)
		if cls.resized: return
		del cls.initbg_up, cls.initbg_down, cls.initbg_data, cls.initbg_colors


#? Functions ------------------------------------------------------------------------------------->

def get_cpu_name() -> str:
	'''Fetch a suitable CPU identifier from the CPU model name string'''
	name: str = ""
	nlist: List = []
	command: str = ""
	cmd_out: str = ""
	rem_line: str = ""
	if SYSTEM == "Linux":
		command = "cat /proc/cpuinfo"
		rem_line = "model name"
	elif SYSTEM == "MacOS":
		command ="sysctl -n machdep.cpu.brand_string"
	elif SYSTEM == "BSD":
		command ="sysctl hw.model"
		rem_line = "hw.model"

	try:
		cmd_out = subprocess.check_output("LANG=C " + command, shell=True, universal_newlines=True)
	except:
		pass
	if rem_line:
		for line in cmd_out.split("\n"):
			if rem_line in line:
				name = re.sub( ".*" + rem_line + ".*:", "", line,1).lstrip()
	else:
		name = cmd_out
	nlist = name.split(" ")
	try:
		if "Xeon" in name and "CPU" in name:
			name = nlist[nlist.index("CPU")+(-1 if name.endswith(("CPU", "z")) else 1)]
		elif "Ryzen" in name:
			name = " ".join(nlist[nlist.index("Ryzen"):nlist.index("Ryzen")+3])
		elif "Duo" in name and "@" in name:
			name = " ".join(nlist[:nlist.index("@")])
		elif "CPU" in name and not nlist[0] == "CPU" and not nlist[nlist.index("CPU")-1].isdigit():
			name = nlist[nlist.index("CPU")-1]
	except:
		pass

	name = name.replace("Processor", "").replace("CPU", "").replace("(R)", "").replace("(TM)", "").replace("Intel", "")
	name = re.sub(r"\d?\.?\d+[mMgG][hH][zZ]", "", name)
	name = " ".join(name.split())

	return name

def get_cpu_core_mapping() -> List[int]:
	mapping: List[int] = []

	if SYSTEM == "Linux" and os.path.isfile("/proc/cpuinfo"):
		try:
			mapping = [0] * THREADS
			num = 0
			with open("/proc/cpuinfo", "r") as f:
				for line in f:
					if line.startswith("processor"):
						num = int(line.strip()[(line.index(": ")+2):])
						if num > THREADS - 1:
							break
					elif line.startswith("core id"):
						mapping[num] = int(line.strip()[(line.index(": ")+2):])
			if num < THREADS - 1:
				raise Exception
		except:
			mapping = []

	if not mapping:
		mapping = []
		for _ in range(THREADS // CORES):
			mapping.extend([x for x in range(CORES)])

	return mapping

def create_box(x: int = 0, y: int = 0, width: int = 0, height: int = 0, title: str = "", title2: str = "", line_color: Color = None, title_color: Color = None, fill: bool = True, box = None) -> str:
	'''Create a box from a box object or by given arguments'''
	out: str = f'{Term.fg}{Term.bg}'
	num: int = 0
	if not line_color: line_color = THEME.div_line
	if not title_color: title_color = THEME.title

	#* Get values from box class if given
	if box:
		x = box.x
		y = box.y
		width = box.width
		height = box.height
		title = box.name
		num = box.num
	hlines: Tuple[int, int] = (y, y + height - 1)

	out += f'{line_color}'

	#* Draw all horizontal lines
	for hpos in hlines:
		out += f'{Mv.to(hpos, x)}{Symbol.h_line * (width - 1)}'

	#* Draw all vertical lines and fill if enabled
	for hpos in range(hlines[0]+1, hlines[1]):
		out += f'{Mv.to(hpos, x)}{Symbol.v_line}{" " * (width-2) if fill else Mv.r(width-2)}{Symbol.v_line}'

	#* Draw corners
	out += f'{Mv.to(y, x)}{Symbol.left_up}\
	{Mv.to(y, x + width - 1)}{Symbol.right_up}\
	{Mv.to(y + height - 1, x)}{Symbol.left_down}\
	{Mv.to(y + height - 1, x + width - 1)}{Symbol.right_down}'

	#* Draw titles if enabled
	if title:
		numbered: str = "" if not num else f'{THEME.hi_fg(SUPERSCRIPT[num])}'
		out += f'{Mv.to(y, x + 2)}{Symbol.title_left}{Fx.b}{numbered}{title_color}{title}{Fx.ub}{line_color}{Symbol.title_right}'
	if title2:
		out += f'{Mv.to(hlines[1], x + 2)}{Symbol.title_left}{title_color}{Fx.b}{title2}{Fx.ub}{line_color}{Symbol.title_right}'

	return f'{out}{Term.fg}{Mv.to(y + 1, x + 1)}'

def now_sleeping(signum, frame):
	"""Reset terminal settings and stop background input read before putting to sleep"""
	Key.stop()
	Collector.stop()
	Draw.now(Term.clear, Term.normal_screen, Term.show_cursor, Term.mouse_off, Term.mouse_direct_off, Term.title())
	Term.echo(True)
	os.kill(os.getpid(), signal.SIGSTOP)

def now_awake(signum, frame):
	"""Set terminal settings and restart background input read"""
	Draw.now(Term.alt_screen, Term.clear, Term.hide_cursor, Term.mouse_on, Term.title("BpyTOP"))
	Term.echo(False)
	Key.start()
	Term.refresh()
	Box.calc_sizes()
	Box.draw_bg()
	Collector.start()

def quit_sigint(signum, frame):
	"""SIGINT redirection to clean_quit()"""
	clean_quit()

def clean_quit(errcode: int = 0, errmsg: str = "", thread: bool = False):
	"""Stop background input read, save current config and reset terminal settings before quitting"""
	global THREAD_ERROR
	if thread:
		THREAD_ERROR = errcode
		interrupt_main()
		return
	if THREAD_ERROR: errcode = THREAD_ERROR
	Key.stop()
	Collector.stop()
	if not errcode: CONFIG.save_config()
	Draw.now(Term.clear, Term.normal_screen, Term.show_cursor, Term.mouse_off, Term.mouse_direct_off, Term.title())
	Term.echo(True)
	if errcode == 0:
		errlog.info(f'Exiting. Runtime {timedelta(seconds=round(time() - SELF_START, 0))} \n')
	else:
		errlog.warning(f'Exiting with errorcode ({errcode}). Runtime {timedelta(seconds=round(time() - SELF_START, 0))} \n')
		if not errmsg: errmsg = f'Bpytop exited with errorcode ({errcode}). See {CONFIG_DIR}/error.log for more information!'
	if errmsg: print(errmsg)

	raise SystemExit(errcode)

def floating_humanizer(value: Union[float, int], bit: bool = False, per_second: bool = False, start: int = 0, short: bool = False) -> str:
	'''Scales up in steps of 1024 to highest possible unit and returns string with unit suffixed
	* bit=True or defaults to bytes
	* start=int to set 1024 multiplier starting unit
	* short=True always returns 0 decimals and shortens unit to 1 character
	'''
	out: str = ""
	mult: int = 8 if bit else 1
	selector: int = start
	unit: Tuple[str, ...] = UNITS["bit"] if bit else UNITS["byte"]

	if isinstance(value, float): value = round(value * 100 * mult)
	elif value > 0: value *= 100 * mult
	else: value = 0

	while len(f'{value}') > 5 and value >= 102400:
		value >>= 10
		if value < 100:
			out = f'{value}'
			break
		selector += 1
	else:
		if len(f'{value}') == 4 and selector > 0:
			out = f'{value}'[:-2] + "." + f'{value}'[-2]
		elif len(f'{value}') == 3 and selector > 0:
			out = f'{value}'[:-2] + "." + f'{value}'[-2:]
		elif len(f'{value}') >= 2:
			out = f'{value}'[:-2]
		else:
			out = f'{value}'


	if short:
		if "." in out:
			out = f'{round(float(out))}'
		if len(out) > 3:
			out = f'{int(out[0]) + 1}'
			selector += 1
	out += f'{"" if short else " "}{unit[selector][0] if short else unit[selector]}'
	if per_second: out += "ps" if bit else "/s"

	return out

def units_to_bytes(value: str) -> int:
	if not value: return 0
	out: int = 0
	mult: int = 0
	bit: bool = False
	value_i: int = 0
	units: Dict[str, int] = {"k" : 1, "m" : 2, "g" : 3}
	try:
		if value.lower().endswith("s"):
			value = value[:-1]
		if value.lower().endswith("bit"):
			bit = True
			value = value[:-3]
		elif value.lower().endswith("byte"):
			value = value[:-4]

		if value[-1].lower() in units:
			mult = units[value[-1].lower()]
			value = value[:-1]

		if "." in value and value.replace(".", "").isdigit():
			if mult > 0:
				value_i = round(float(value) * 1024)
				mult -= 1
			else:
				value_i = round(float(value))
		elif value.isdigit():
			value_i = int(value)

		out = int(value_i) << (10 * mult)
		if bit: out = round(out / 8)
	except ValueError:
		out = 0
	return out

def min_max(value: int, min_value: int=0, max_value: int=100) -> int:
	return max(min_value, min(value, max_value))

def readfile(file: str, default: str = "") -> str:
	out: Union[str, None] = None
	if os.path.isfile(file):
		try:
			with open(file, "r") as f:
				out = f.read().strip()
		except:
			pass
	return default if out is None else out

def process_keys():
	mouse_pos: Tuple[int, int] = (0, 0)
	filtered: bool = False
	box_keys = {"1" : "cpu", "2" : "mem", "3" : "net", "4" : "proc"}
	while Key.has_key():
		key = Key.get()
		found: bool = True
		if key in ["mouse_scroll_up", "mouse_scroll_down", "mouse_click"]:
			mouse_pos = Key.get_mouse()
			if mouse_pos[0] >= ProcBox.x and ProcBox.current_y + 1 <= mouse_pos[1] < ProcBox.current_y + ProcBox.current_h - 1:
				pass
			elif key == "mouse_click":
				key = "mouse_unselect"
			else:
				key = "_null"

		if ProcBox.filtering:
			if key in ["enter", "mouse_click", "mouse_unselect"]:
				ProcBox.filtering = False
				Collector.collect(ProcCollector, redraw=True, only_draw=True)
				continue
			elif key in ["escape", "delete"]:
				ProcCollector.search_filter = ""
				ProcBox.filtering = False
			elif len(key) == 1:
				ProcCollector.search_filter += key
			elif key == "backspace" and len(ProcCollector.search_filter) > 0:
				ProcCollector.search_filter = ProcCollector.search_filter[:-1]
			else:
				continue
			Collector.collect(ProcCollector, proc_interrupt=True, redraw=True)
			if filtered: Collector.collect_done.wait(0.1)
			filtered = True
			continue

		if key == "_null":
			continue
		elif key == "q":
			clean_quit()
		elif key == "+" and CONFIG.update_ms + 100 <= 86399900:
			CONFIG.update_ms += 100
			Box.draw_update_ms()
		elif key == "-" and CONFIG.update_ms - 100 >= 100:
			CONFIG.update_ms -= 100
			Box.draw_update_ms()
		elif key in ["M", "escape"]:
			Menu.main()
		elif key in ["o", "f2"]:
			Menu.options()
		elif key in ["H", "f1"]:
			Menu.help()
		elif key == "m":
			if list(Box.view_modes).index(Box.view_mode) + 1 > len(list(Box.view_modes)) - 1:
				Box.view_mode = list(Box.view_modes)[0]
			else:
				Box.view_mode = list(Box.view_modes)[(list(Box.view_modes).index(Box.view_mode) + 1)]
			CONFIG.shown_boxes = " ".join(Box.view_modes[Box.view_mode])
			Draw.clear(saved=True)
			Term.refresh(force=True)
		elif key in box_keys:
			boxes = CONFIG.shown_boxes.split()
			if box_keys[key] in boxes:
				boxes.remove(box_keys[key])
			else:
				boxes.append(box_keys[key])
			CONFIG.shown_boxes = " ".join(boxes)
			Box.view_mode = "user"
			Box.view_modes["user"] = CONFIG.shown_boxes.split()
			Draw.clear(saved=True)
			Term.refresh(force=True)
		else:
			found = False

		if found: continue

		if "proc" in Box.boxes:
			if key in ["left", "right", "h", "l"]:
				ProcCollector.sorting(key)
			elif key == " " and CONFIG.proc_tree and ProcBox.selected > 0:
				if ProcBox.selected_pid in ProcCollector.collapsed:
					ProcCollector.collapsed[ProcBox.selected_pid] = not ProcCollector.collapsed[ProcBox.selected_pid]
				Collector.collect(ProcCollector, interrupt=True, redraw=True)
			elif key == "e":
				CONFIG.proc_tree = not CONFIG.proc_tree
				Collector.collect(ProcCollector, interrupt=True, redraw=True)
			elif key == "r":
				CONFIG.proc_reversed = not CONFIG.proc_reversed
				Collector.collect(ProcCollector, interrupt=True, redraw=True)
			elif key == "c":
				CONFIG.proc_per_core = not CONFIG.proc_per_core
				Collector.collect(ProcCollector, interrupt=True, redraw=True)
			elif key in ["f", "F"]:
				ProcBox.filtering = True
				ProcCollector.case_sensitive = key == "F"
				if not ProcCollector.search_filter: ProcBox.start = 0
				Collector.collect(ProcCollector, redraw=True, only_draw=True)
			elif key in ["T", "K", "I"] and (ProcBox.selected > 0 or ProcCollector.detailed):
				pid: int = ProcBox.selected_pid if ProcBox.selected > 0 else ProcCollector.detailed_pid # type: ignore
				if psutil.pid_exists(pid):
					if key == "T": sig = signal.SIGTERM
					elif key == "K": sig = signal.SIGKILL
					elif key == "I": sig = signal.SIGINT
					try:
						os.kill(pid, sig)
					except Exception as e:
						errlog.error(f'Exception when sending signal {sig} to pid {pid}')
						errlog.exception(f'{e}')
			elif key == "delete" and ProcCollector.search_filter:
				ProcCollector.search_filter = ""
				Collector.collect(ProcCollector, proc_interrupt=True, redraw=True)
			elif key == "enter":
				if ProcBox.selected > 0 and ProcCollector.detailed_pid != ProcBox.selected_pid and psutil.pid_exists(ProcBox.selected_pid):
					ProcCollector.detailed = True
					ProcBox.last_selection = ProcBox.selected
					ProcBox.selected = 0
					ProcCollector.detailed_pid = ProcBox.selected_pid
					ProcBox.resized = True
					Collector.proc_counter = 1
				elif ProcCollector.detailed:
					ProcBox.selected = ProcBox.last_selection
					ProcBox.last_selection = 0
					ProcCollector.detailed = False
					ProcCollector.detailed_pid = None
					ProcBox.resized = True
					Collector.proc_counter = 1
				else:
					continue
				ProcCollector.details = {}
				ProcCollector.details_cpu = []
				ProcCollector.details_mem = []
				Graphs.detailed_cpu = NotImplemented
				Graphs.detailed_mem = NotImplemented
				Collector.collect(ProcCollector, proc_interrupt=True, redraw=True)
			elif key in ["up", "down", "mouse_scroll_up", "mouse_scroll_down", "page_up", "page_down", "home", "end", "mouse_click", "mouse_unselect", "j", "k"]:
				ProcBox.selector(key, mouse_pos)

		if "net" in Box.boxes:
			if key in ["b", "n"]:
				NetCollector.switch(key)
			elif key == "z":
				NetCollector.reset = not NetCollector.reset
				Collector.collect(NetCollector, redraw=True)
			elif key == "y":
				CONFIG.net_sync = not CONFIG.net_sync
				Collector.collect(NetCollector, redraw=True)
			elif key == "a":
				NetCollector.auto_min = not NetCollector.auto_min
				NetCollector.net_min = {"download" : -1, "upload" : -1}
				Collector.collect(NetCollector, redraw=True)

		if "mem" in Box.boxes:
			if key == "g":
				CONFIG.mem_graphs = not CONFIG.mem_graphs
				Collector.collect(MemCollector, interrupt=True, redraw=True)
			elif key == "s":
				Collector.collect_idle.wait()
				CONFIG.swap_disk = not CONFIG.swap_disk
				Collector.collect(MemCollector, interrupt=True, redraw=True)
			elif key == "d":
				Collector.collect_idle.wait()
				CONFIG.show_disks = not CONFIG.show_disks
				Collector.collect(MemCollector, interrupt=True, redraw=True)
			elif key == "i":
				Collector.collect_idle.wait()
				CONFIG.io_mode = not CONFIG.io_mode
				Collector.collect(MemCollector, interrupt=True, redraw=True)





#? Pre main -------------------------------------------------------------------------------------->


CPU_NAME: str = get_cpu_name()

CORE_MAP: List[int] = get_cpu_core_mapping()

THEME: Theme

def main():
	global THEME

	Term.width = os.get_terminal_size().columns
	Term.height = os.get_terminal_size().lines

	#? Init -------------------------------------------------------------------------------------->
	if DEBUG: TimeIt.start("Init")

	#? Switch to alternate screen, clear screen, hide cursor, enable mouse reporting and disable input echo
	Draw.now(Term.alt_screen, Term.clear, Term.hide_cursor, Term.mouse_on, Term.title("BpyTOP"))
	Term.echo(False)
	#Term.refresh(force=True)

	#? Start a thread checking for updates while running init
	if CONFIG.update_check: UpdateChecker.run()

	#? Draw banner and init status
	if CONFIG.show_init and not Init.resized:
		Init.start()

	#? Load theme
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Loading theme and creating colors... ")}{Mv.save}')
	try:
		THEME = Theme(CONFIG.color_theme)
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Setup boxes
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Doing some maths and drawing... ")}{Mv.save}')
	try:
		if CONFIG.check_temp: CpuCollector.get_sensors()
		Box.calc_sizes()
		Box.draw_bg(now=False)
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Setup signal handlers for SIGSTP, SIGCONT, SIGINT and SIGWINCH
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Setting up signal handlers... ")}{Mv.save}')
	try:
		signal.signal(signal.SIGTSTP, now_sleeping) #* Ctrl-Z
		signal.signal(signal.SIGCONT, now_awake)	#* Resume
		signal.signal(signal.SIGINT, quit_sigint)	#* Ctrl-C
		signal.signal(signal.SIGWINCH, Term.refresh) #* Terminal resized
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Start a separate thread for reading keyboard input
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Starting input reader thread... ")}{Mv.save}')
	try:
		if isinstance(sys.stdin, io.TextIOWrapper) and sys.version_info >= (3, 7):
			sys.stdin.reconfigure(errors="ignore")  # type: ignore
		Key.start()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Start a separate thread for data collection and drawing
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Starting data collection and drawer thread... ")}{Mv.save}')
	try:
		Collector.start()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Collect data and draw to buffer
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Collecting data and drawing... ")}{Mv.save}')
	try:
		Collector.collect(draw_now=False)
		pass
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Draw to screen
	if CONFIG.show_init:
		Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Finishing up... ")}{Mv.save}')
	try:
		Collector.collect_done.wait()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	Init.done()
	Term.refresh()
	Draw.out(clear=True)
	if CONFIG.draw_clock:
		Box.clock_on = True
	if DEBUG: TimeIt.stop("Init")

	#? Main loop ------------------------------------------------------------------------------------->

	def run():
		while not False:
			Term.refresh()
			Timer.stamp()

			while Timer.not_zero():
				if Key.input_wait(Timer.left()):
					process_keys()

			Collector.collect()

	#? Start main loop
	try:
		run()
	except Exception as e:
		errlog.exception(f'{e}')
		clean_quit(1)
	else:
		#? Quit cleanly even if false starts being true...
		clean_quit()


if __name__ == "__main__":
	main()
