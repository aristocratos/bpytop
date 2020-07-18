#!/usr/bin/env python3
# pylint: disable=not-callable, no-member
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

import os, sys, threading, signal, re, subprocess, logging, logging.handlers
from time import time, sleep, strftime, localtime
from datetime import timedelta
from _thread import interrupt_main
from select import select
from distutils.util import strtobool
from string import Template
from math import ceil, floor
from random import randint
from shutil import which
from typing import List, Set, Dict, Tuple, Optional, Union, Any, Callable, ContextManager, Iterable, Type

errors: List[str] = []
try: import fcntl, termios, tty
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
	print ("ERROR!")
	for error in errors:
		print(error)
	if SYSTEM == "Other":
		print("\nUnsupported platform!\n")
	else:
		print("\nInstall required modules!\n")
	quit(1)

#? Variables ------------------------------------------------------------------------------------->

BANNER_SRC: List[Tuple[str, str, str]] = [
	("#ffa50a", "#0fd7ff", "██████╗ ██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗"),
	("#f09800", "#00bfe6", "██╔══██╗██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗"),
	("#db8b00", "#00a6c7", "██████╔╝██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝"),
	("#c27b00", "#008ca8", "██╔══██╗██╔═══╝   ╚██╔╝     ██║   ██║   ██║██╔═══╝ "),
	("#a86b00", "#006e85", "██████╔╝██║        ██║      ██║   ╚██████╔╝██║"),
	("#000000", "#000000", "╚═════╝ ╚═╝        ╚═╝      ╚═╝    ╚═════╝ ╚═╝"),
]
VERSION: str = "0.4.1"

#*?This is the template used to create the config file
DEFAULT_CONF: Template = Template(f'#? Config file for bpytop v. {VERSION}' + '''

#* Color theme, looks for a .theme file in "~/.config/bpytop/themes" and "~/.config/bpytop/user_themes", "Default" for builtin default theme
#* Corresponding folder with a trailing / needs to be appended, example: color_theme="user_themes/monokai"
color_theme="$color_theme"

#* Update time in milliseconds, increases automatically if set below internal loops processing time, recommended 2000 ms or above for better sample times for graphs.
update_ms=$update_ms

#* Processes sorting, "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive",
#* "cpu lazy" updates top process over time, "cpu responsive" updates top process directly.
proc_sorting="$proc_sorting"

#* Reverse sorting order, True or False.
proc_reversed=$proc_reversed

#* Show processes as a tree
proc_tree=$proc_tree

#* Check cpu temperature, needs "vcgencmd" on Raspberry Pi and "osx-cpu-temp" on MacOS X.
check_temp=$check_temp

#* Draw a clock at top of screen, formatting according to strftime, empty string to disable.
draw_clock="$draw_clock"

#* Update main ui in background when menus are showing, set this to false if the menus is flickering too much for comfort.
background_update=$background_update

#* Custom cpu model name, empty string to disable.
custom_cpu_name="$custom_cpu_name"

#* Show color gradient in process list, True or False.
proc_gradient=$proc_gradient

#* If process cpu usage should be of the core it's running on or usage of the total available cpu power.
proc_per_core=$proc_per_core

#* Optional filter for shown disks, should be last folder in path of a mountpoint, "root" replaces "/", separate multiple values with comma.
#* Begin line with "exclude=" to change to exclude filter, oterwise defaults to "most include" filter. Example: disks_filter="exclude=boot, home"
disks_filter="$disks_filter"

#* Show graphs instead of meters for memory values.
mem_graphs=$mem_graphs

#* If swap memory should be shown in memory box.
show_swap=$show_swap

#* Show swap as a disk, ignores show_swap value above, inserts itself after first disk.
swap_disk=$swap_disk

#* If mem box should be split to also show disks info.
show_disks=$show_disks

#* Enable check for new version from github.com/aristocratos/bpytop at start.
update_check=$update_check

#* Set loglevel for "~/.config/bpytop/error.log" levels are: "CRITICAL" "ERROR" "WARNING" "INFO" "DEBUG".
#* The level set includes all lower levels, i.e. "DEBUG" will show all logging info.
log_level="$log_level"
''')

CONFIG_DIR: str = f'{os.path.expanduser("~")}/.config/bpytop'
if not os.path.isdir(CONFIG_DIR):
	try:
		os.makedirs(CONFIG_DIR)
		os.mkdir(f'{CONFIG_DIR}/themes')
		os.mkdir(f'{CONFIG_DIR}/user_themes')
	except PermissionError:
		print(f'ERROR!\nNo permission to write to "{CONFIG_DIR}" directory!')
		quit(1)
CONFIG_FILE: str = f'{CONFIG_DIR}/bpytop.conf'
THEME_DIR: str = f'{CONFIG_DIR}/themes'
USER_THEME_DIR: str = f'{CONFIG_DIR}/user_themes'

CORES: int = psutil.cpu_count(logical=False) or 1
THREADS: int = psutil.cpu_count(logical=True) or 1

THREAD_ERROR: int = 0

DEFAULT_THEME: Dict[str, str] = {
	"main_bg" : "",
	"main_fg" : "#cc",
	"title" : "#ee",
	"hi_fg" : "#90",
	"selected_bg" : "#7e2626",
	"selected_fg" : "#ee",
	"inactive_fg" : "#40",
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
	"upload_end" : "#dcafde"
}

#? Units for floating_humanizer function
UNITS: Dict[str, Tuple[str, ...]] = {
	"bit" : ("bit", "Kib", "Mib", "Gib", "Tib", "Pib", "Eib", "Zib", "Yib", "Bib", "GEb"),
	"byte" : ("Byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB", "BiB", "GEB")
}

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
	quit(1)

#! Timers, remove ----------------------------------------------------------------------->

class Timer:
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

def timerd(func):
	def timed(*args, **kw):
		ts = time()
		out = func(*args, **kw)
		te = time()
		errlog.debug(f'{func.__name__} completed in {te - ts:.6f} seconds')
		return out
	return timed

#! Timers, remove -----------------------------------------------------------------------<

#? Set up config class and load config ------------------------------------------------>

class Config:
	'''Holds all config variables and functions for loading from and saving to disk'''
	keys: List[str] = ["color_theme", "update_ms", "proc_sorting", "proc_reversed", "proc_tree", "check_temp", "draw_clock", "background_update", "custom_cpu_name", "proc_gradient", "proc_per_core", "disks_filter", "update_check", "log_level", "mem_graphs", "show_swap", "swap_disk", "show_disks"]
	conf_dict: Dict[str, Union[str, int, bool]] = {}
	color_theme: str = "Default"
	update_ms: int = 2500
	proc_sorting: str = "cpu lazy"
	proc_reversed: bool = False
	proc_tree: bool = False
	check_temp: bool = True
	draw_clock: str = "%X"
	background_update: bool = True
	custom_cpu_name: str = ""
	proc_gradient: bool = True
	proc_per_core: bool = False
	disks_filter: str = ""
	update_check: bool = True
	mem_graphs: bool = True
	show_swap: bool = False
	swap_disk: bool = True
	show_disks: bool = True
	log_level: str = "WARNING"

	warnings: List[str] = []

	sorting_options: List[str] = ["pid", "program", "arguments", "threads", "user", "memory", "cpu lazy", "cpu responsive"]
	log_levels: List[str] = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

	changed: bool = False
	recreate: bool = False
	config_file: str = ""

	_initialized: bool = False

	def __init__(self, path: str):
		self.config_file = path
		conf: Dict[str, Union[str, int, bool]] = self.load_config()
		if not "version" in conf.keys():
			self.recreate = True
			self.warnings.append(f'Config file malformatted or missing, will be recreated on exit!')
		elif conf["version"] != VERSION:
			self.recreate = True
			self.warnings.append(f'Config file version and bpytop version missmatch, will be recreated on exit!')
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
		if not os.path.isfile(self.config_file): return new_config
		try:
			with open(self.config_file, "r") as f:
				for line in f:
					line = line.strip()
					if line.startswith("#? Config"):
						new_config["version"] = line[line.find("v. ") + 3:]
					for key in self.keys:
						if line.startswith(key):
							line = line.lstrip(key + "=")
							if line.startswith('"'):
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
	errlog.setLevel(getattr(logging, CONFIG.log_level))
	errlog.info(f'New instance of bpytop version {VERSION} started with pid {os.getpid()}')
	errlog.debug(f'Loglevel set to {CONFIG.log_level}')
	if CONFIG.warnings:
		for warning in CONFIG.warnings:
			errlog.warning(warning)
		CONFIG.warnings = []
except Exception as e:
	errlog.exception(f'{e}')
	quit(1)


#? Classes --------------------------------------------------------------------------------------->

class Term:
	"""Terminal info and commands"""
	width: int = os.get_terminal_size().columns	#* Current terminal width in columns
	height: int = os.get_terminal_size().lines	#* Current terminal height in lines
	resized: bool = False
	_w : int = 0
	_h : int = 0
	fg: str = "" 								#* Default foreground color
	bg: str = "" 								#* Default background color
	hide_cursor 		= "\033[?25l"			#* Hide terminal cursor
	show_cursor 		= "\033[?25h"			#* Show terminal cursor
	alt_screen 			= "\033[?1049h"			#* Switch to alternate screen
	normal_screen 		= "\033[?1049l"			#* Switch to normal screen
	clear				= "\033[2J\033[0;0f"	#* Clear screen and set cursor to position 0,0

	@classmethod
	def refresh(cls, *args):
		"""Update width, height and set resized flag if terminal has been resized"""
		if cls.resized == True: return
		cls._w, cls._h = os.get_terminal_size()
		while (cls._w, cls._h) != (cls.width, cls.height):
			cls.resized = True
			Collector.collect_interrupt = True
			cls.width, cls.height = cls._w, cls._h
			Draw.now(Term.clear)
			Draw.now(f'{create_box(cls._w // 2 - 25, cls._h // 2 - 2, 50, 3, "resizing")}{THEME.main_fg}{Fx.b}{Mv.r(12)}Width : {cls._w}   Height: {cls._h}')
			while cls._w < 80 or cls._h < 24:
				Draw.now(Term.clear)
				Draw.now(f'{create_box(cls._w // 2 - 25, cls._h // 2 - 2, 50, 4, "warning")}{THEME.main_fg}{Fx.b}{Mv.r(12)}Width: {cls._w}   Height: {cls._h}\
					{Mv.to(cls._h // 2, cls._w // 2 - 23)}Width and Height needs to be at least 80x24!')
				sleep(0.3)
				cls._w, cls._h = os.get_terminal_size()
			sleep(0.3)
			cls._w, cls._h = os.get_terminal_size()
		cls.resized = False
		Box.calc_sizes()
		Box.draw_bg(now=True if not Init.running else False)


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

class Fx:
	"""Text effects
	* trans(string: str): Replace whitespace with escape move right to not paint background in whitespace.
	* uncolor(string: str) : Removes all color and returns string with THEME.inactive_fg color."""
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

	color_re = re.compile(r"\033\[\d+;\d?;?\d*;?\d*;?\d*m")

	@staticmethod
	def trans(string: str):
		return string.replace(" ", "\033[1C")

	@classmethod
	def uncolor(cls, string: str) -> str:
		return f'{THEME.inactive_fg}{cls.color_re.sub("", string)}{Term.fg}'

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
	"""Handles the threaded input reader"""
	list: List[str] = []
	new = threading.Event()
	idle = threading.Event()
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
	def has_key(cls) -> bool:
		if cls.list: return True
		else: return False

	@classmethod
	def clear(cls):
		cls.list = []

	@classmethod
	def input_wait(cls, sec: float = 0.0) -> bool:
		'''Returns True if key is detected else waits out timer and returns False'''
		cls.new.wait(sec if sec > 0 else 0.0)
		if cls.new.is_set():
			cls.new.clear()
			return True
		else:
			return False

	@classmethod
	def _get_key(cls):
		"""Get a single key from stdin, convert to readable format and save to keys list. Meant to be run in it's own thread."""
		input_key: str = ""
		clean_key: str = ""
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

		try:
			while not cls.stopping:
				with Raw(sys.stdin):
					if not select([sys.stdin], [], [], 0.1)[0]: #* Wait 100ms for input on stdin then restart loop to check for stop flag
						continue
					cls.idle.clear() #* Report IO block in progress to prevent Draw functions to get IO Block error
					input_key += sys.stdin.read(1)
					if input_key == "\033": #* If first character is a escape sequence read 5 more keys
						Draw.idle.wait() #* Wait for Draw function to finish if busy
						with Nonblocking(sys.stdin): #* Set non blocking to prevent read stall if less than 5 characters
							input_key += sys.stdin.read(5)
					if input_key == "\033":	clean_key = "escape" #* Key is escape if only containing \033
					elif input_key == "\\": clean_key = "\\" #* Clean up "\" to not return escaped
					else:
						for code in escape.keys(): #* Go trough dict of escape codes to get the cleaned key name
							if input_key.lstrip("\033").startswith(code):
								clean_key = escape[code]
								break
						else: #* If not found in escape dict and length of key is 1, assume regular character
							if len(input_key) == 1:
								clean_key = input_key
					if testing: errlog.debug(f'Input key: {repr(input_key)} Clean key: {clean_key}') #! Remove
					if clean_key:
						cls.list.append(clean_key)		#* Store up to 10 keys in input queue for later processing
						if len(cls.list) > 10: del cls.list[0]
						clean_key = ""
						cls.new.set()					#* Set threading event to interrupt main thread sleep
					input_key = ""
					cls.idle.set() #* Report IO blocking done

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
	last: Dict[str, str] = {}
	idle = threading.Event()
	idle.set()

	@classmethod
	def now(cls, *args):
		'''Wait for input reader to be idle then print to screen'''
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
	def buffer(cls, name: str, *args: str, append: bool = False, now: bool = False, z: int = 100, save: bool = False, uncolor: bool = False):
		string: str = ""
		if name.startswith("+"):
			name = name.lstrip("+")
			append = True
		if name.endswith("!"):
			name = name.rstrip("!")
			now = True
		if not name in cls.z_order or z != 100: cls.z_order[name] = z
		if args: string = "".join(args)
		if uncolor: string = Fx.uncolor(string)
		if name not in cls.strings or not append: cls.strings[name] = ""
		if save:
			if name not in cls.last or not append: cls.last[name] = ""
			cls.last[name] = string
		else:
			cls.strings[name] += string
		if now: cls.now(string)

	@classmethod
	def out(cls, *names: str, clear = False):
		out: str = ""
		if not cls.strings: return
		if names:
			for name in sorted(cls.z_order, key=cls.z_order.get, reverse=True):
				if name in names:
					out += cls.strings[name]
					cls.last[name] = out
					if clear:
						del cls.strings[name]
						del cls.z_order[name]
			cls.now(out)
		else:
			for name in sorted(cls.z_order, key=cls.z_order.get, reverse=True):
				if name in cls.strings:
					out += cls.strings[name]
					cls.last[name] = out
			if clear: cls.strings = {}
			cls.now(out)

	@classmethod
	def last_buffer(cls) -> str:
		out: str = ""
		for name in sorted(cls.z_order, key=cls.z_order.get, reverse=True):
			if name in cls.last:
				out += cls.last[name]
		return out


	@classmethod
	def clear(cls, *names, last: bool = False):
		if names:
			for name in names:
				if name in cls.strings:
					del cls.strings[name]
					if last:
						del cls.z_order[name]
						if name in cls.last: del cls.last[name]
		else:
			cls.strings = {}
			if last: cls.last = {}

class Color:
	'''Holds representations for a 24-bit color value
	__init__(color, depth="fg", default=False)
	-- color accepts 6 digit hexadecimal: string "#RRGGBB", 2 digit hexadecimal: string "#FF" or decimal RGB "255 255 255" as a string.
	-- depth accepts "fg" or "bg"
	__call__(*args) converts arguments to a string and apply color
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
					raise ValueError(f'Incorrectly formatted hexadeciaml rgb string: {self.hexa}')

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

	def __str__(self) -> str:
		return self.escape

	def __repr__(self) -> str:
		return repr(self.escape)

	def __iter__(self) -> Iterable:
		for c in self.dec: yield c

	def __call__(self, *args: str) -> str:
		if len(args) == 0: return ""
		return f'{self.escape}{"".join(args)}{getattr(Term, self.depth)}'

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
					color = f'\033[{dint};2;{c};{c};{c}m'
				elif len(hexa) == 7:
					color = f'\033[{dint};2;{int(hexa[1:3], base=16)};{int(hexa[3:5], base=16)};{int(hexa[5:7], base=16)}m'
			except ValueError as e:
				errlog.exception(f'{e}')
		else:
			color = f'\033[{dint};2;{r};{g};{b}m'
		return color

	@classmethod
	def fg(cls, *args) -> str:
		if len(args) > 1: return cls.escape_color(r=args[0], g=args[1], b=args[2], depth="fg")
		else: return cls.escape_color(hexa=args[0], depth="fg")

	@classmethod
	def bg(cls, *args) -> str:
		if len(args) > 1: return cls.escape_color(r=args[0], g=args[1], b=args[2], depth="bg")
		else: return cls.escape_color(hexa=args[0], depth="bg")

class Theme:
	'''__init__ accepts a dict containing { "color_element" : "color" }'''

	themes: Dict[str, str] = {}
	cached: Dict[str, Dict[str, str]] = { "Default" : DEFAULT_THEME }
	current: str = ""

	main_bg = main_fg = title = hi_fg = selected_bg = selected_fg = inactive_fg = proc_misc = cpu_box = mem_box = net_box = proc_box = div_line = temp_start = temp_mid = temp_end = cpu_start = cpu_mid = cpu_end = free_start = free_mid = free_end = cached_start = cached_mid = cached_end = available_start = available_mid = available_end = used_start = used_mid = used_end = download_start = download_mid = download_end = upload_start = upload_mid = upload_end = NotImplemented

	gradient: Dict[str, List[str]] = {
		"temp" : [],
		"cpu" : [],
		"free" : [],
		"cached" : [],
		"available" : [],
		"used" : [],
		"download" : [],
		"upload" : []
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
		#* Get key names from DEFAULT_THEME dict to not leave any color unset if missing from theme dict
		for item, value in DEFAULT_THEME.items():
			default = False if item not in ["main_fg", "main_bg"] else True
			depth = "fg" if item not in ["main_bg", "selected_bg"] else "bg"
			if item in tdict.keys():
				setattr(self, item, Color(tdict[item], depth=depth, default=default))
			else:
				setattr(self, item, Color(value, depth=depth, default=default))
		#* Create color gradients from one, two or three colors, 101 values indexed 0-100
		rgb: Dict[str, Tuple[int, int, int]]
		colors: List[List[int]] = []
		for name in self.gradient.keys():
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
				for _ in range(100):
					self.gradient[name] += [c]
		#* Set terminal colors
		Term.fg, Term.bg = self.main_fg, self.main_bg
		Draw.now(self.main_fg, self.main_bg)

	def refresh(self):
		'''Sets themes dict with names and paths to all found themes'''
		self.themes = { "Default" : "Default" }
		try:
			for d in (THEME_DIR, USER_THEME_DIR):
				for f in os.listdir(d):
					if f.endswith(".theme"):
						self.themes[f'{f[:-6] if d == THEME_DIR else f[:-6] + "*"}'] = f'{d}/{f}'
		except Exception as e:
			errlog.exception(str(e))

	@staticmethod
	def _load_file(path: str) -> Dict[str, str]:
		'''Load a bashtop formatted theme file and return a dict'''
		new_theme: Dict[str, str] = {}
		try:
			with open(path) as f:
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
					if n > 5 and n < 25: c_color = line_color2
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
	offset: int
	current: bool
	last: int
	symbol: Dict[float, str]

	def __init__(self, width: int, height: int, color: Union[List[str], Color, None], data: List[int], invert: bool = False, max_value: int = 0, offset: int = 0):
		self.graphs: Dict[bool, List[str]] = {False : [], True : []}
		self.current: bool = True
		self.colors: List[str] = []
		if isinstance(color, list) and height > 1:
			for i in range(1, height + 1): self.colors.insert(0, color[i * 100 // height]) #* Calculate colors of graph
			if invert: self.colors.reverse()
		elif isinstance(color, Color) and height > 1:
			self.colors = [ f'{color}' for _ in range(height) ]
		else:
			if isinstance(color, list): self.colors = color
			elif isinstance(color, Color): self.colors = [ f'{color}' for _ in range(101) ]
		self.width = width
		self.height = height
		self.invert = invert
		self.offset = offset
		if not data: data = [0]
		if max_value:
			self.max_value = max_value
			data = [ (v + offset) * 100 // (max_value + offset) if v < max_value else 100 for v in data ] #* Convert values to percentage values of max_value with max_value as ceiling
		else:
			self.max_value = 0
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
		if len(data) % 2 == 1: data.insert(0, 0)
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
				if new: self.last = data[v]
				self.graphs[self.current][h] += self.symbol[float(value["left"] + value["right"] / 10)]
		if data: self.last = data[-1]
		self.out = ""

		if self.height == 1:
			self.out += f'{"" if not self.colors else self.colors[self.last]}{self.graphs[self.current][0]}'
		elif self.height > 1:
			for h in range(self.height):
				if h > 0: self.out += f'{Mv.d(1)}{Mv.l(self.width)}'
				self.out += f'{"" if not self.colors else self.colors[h]}{self.graphs[self.current][h if not self.invert else (self.height - 1) - h]}'
		if self.colors: self.out += f'{Term.fg}'

	def add(self, value: int) -> str:
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

	def __call__(self, value: int) -> str:
		return self.add(value)

	def __str__(self):
		return self.out

	def __repr__(self):
		return repr(self.out)


class Graphs:
	'''Holds all graphs and lists of graphs for dynamically created graphs'''
	cpu: Dict[str, Graph] = {}
	cores: List[Graph] = [NotImplemented] * THREADS
	temps: List[Graph] = [NotImplemented] * (THREADS + 1)
	net: Graph
	detailed_cpu: Graph
	detailed_mem: Graph
	pid_cpu: Dict[int, Graph] = {}

class Meter:
	'''Creates a percentage meter
	__init__(value, width, theme, gradient_name) to create new meter
	__call__(value) to set value and return meter as a string
	__str__ returns last set meter as a string
	'''
	out: str
	color_gradient: List[str]
	color_inactive: Color
	width: int
	saved: Dict[int, str]

	def __init__(self, value: int, width: int, gradient_name: str):
		self.color_gradient = THEME.gradient[gradient_name]
		self.color_inactive = THEME.inactive_fg
		self.width = width
		self.out = self._create(value)
		self.saved = { value : self.out }

	def __call__(self, value: int):
		if value in self.saved.keys():
			self.out = self.saved[value]
		else:
			self.out = self._create(value)
			self.saved[value] = self.out
		return self.out

	def __str__(self):
		return self.out

	def __repr__(self):
		return repr(self.out)

	def _create(self, value: int):
		if value > 100: value = 100
		elif value < 0: value = 100
		out: str = ""
		for i in range(1, self.width + 1):
			if value >= round(i * 100 / self.width):
				out += f'{self.color_gradient[round(i * 100 / self.width)]}{Symbol.meter}'
			else:
				out += self.color_inactive(Symbol.meter * (self.width + 1 - i))
				break
		else:
			out += f'{Term.fg}'
		return out

class Meters:
	cpu: Meter
	mem: Dict[str, Union[Meter, Graph]] = {}
	swap: Dict[str, Union[Meter, Graph]] = {}
	disks_used: Dict[str, Meter] = {}
	disks_free: Dict[str, Meter] = {}

class Box:
	'''Box class with all needed attributes for create_box() function'''
	name: str
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
	resized: bool = False

	@classmethod
	def calc_sizes(cls):
		'''Calculate sizes of boxes'''
		for sub in cls.__subclasses__():
			sub._calc_size() # type: ignore
			sub.resized = True # type: ignore

	@classmethod
	def draw_update_ms(cls, now: bool = True):
		Draw.buffer("update_ms!" if now and not Menu.active else "update_ms", f'{Mv.to(CpuBox.y - 1, CpuBox.x + CpuBox.width - len(str(CONFIG.update_ms)) - 7)}{THEME.cpu_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg("+")} '
			f'{THEME.title(str(CONFIG.update_ms))} {THEME.hi_fg("+")}{Fx.ub}{THEME.cpu_box(Symbol.title_right)}', save=True if Menu.active else False)
		if now and not Menu.active: Draw.clear("update_ms")

	@classmethod
	def draw_bg(cls, now: bool = True):
		'''Draw all boxes outlines and titles'''
		Draw.buffer("bg!" if now and not Menu.active else "bg", "".join(sub._draw_bg() for sub in cls.__subclasses__()), z=1000, save=True if Menu.active else False) # type: ignore
		if now and not Menu.active: Draw.clear("bg")
		cls.draw_update_ms(now=now)

class SubBox:
	box_x: int = 0
	box_y: int = 0
	box_width: int = 0
	box_height: int = 0
	box_columns: int = 0
	column_size: int = 0

class CpuBox(Box, SubBox):
	name = "cpu"
	x = 1
	y = 1
	height_p = 32
	width_p = 100
	resized: bool = True
	buffer: str = "cpu"
	Box.buffers.append(buffer)

	@classmethod
	def _calc_size(cls):
		cls.width = round(Term.width * cls.width_p / 100)
		cls.height = round(Term.height * cls.height_p / 100)
		Box._b_cpu_h = cls.height
		#THREADS = 64
		cls.box_columns = ceil((THREADS + 1) / (cls.height - 5))
		if cls.box_columns * (24 + 13 if CONFIG.check_temp else 24) < cls.width - (cls.width // 4): cls.column_size = 2
		elif cls.box_columns * (19 + 6 if CONFIG.check_temp else 19) < cls.width - (cls.width // 4): cls.column_size = 1
		elif cls.box_columns * (10 + 6 if CONFIG.check_temp else 10) < cls.width - (cls.width // 4): cls.column_size = 0
		else: cls.box_columns = (cls.width - cls.width // 4) // (10 + 6 if CONFIG.check_temp else 10); cls.column_size = 0

		if cls.column_size == 2: cls.box_width = (24 + 13 if CONFIG.check_temp else 24) * cls.box_columns - ((cls.box_columns - 1) * 1)
		elif cls.column_size == 1: cls.box_width = (19 + 6 if CONFIG.check_temp else 19) * cls.box_columns - ((cls.box_columns - 1) * 1)
		else: cls.box_width = (11 + 6 if CONFIG.check_temp else 11) * cls.box_columns + 1
		cls.box_height = ceil(THREADS / cls.box_columns) + 4

		if cls.box_height > cls.height - 2: cls.box_height = cls.height - 2
		cls.box_x = (cls.width - 1) - cls.box_width
		cls.box_y = cls.y + ceil((cls.height - 2) / 2) - ceil(cls.box_height / 2) + 1

	@classmethod
	def _draw_bg(cls) -> str:
		return (f'{create_box(box=cls, line_color=THEME.cpu_box)}'
		f'{Mv.to(cls.y, cls.x + 10)}{THEME.cpu_box(Symbol.title_left)}{Fx.b}{THEME.hi_fg("m")}{THEME.title("enu")}{Fx.ub}{THEME.cpu_box(Symbol.title_right)}'
		f'{create_box(x=cls.box_x, y=cls.box_y, width=cls.box_width, height=cls.box_height, line_color=THEME.div_line, fill=False, title=CPU_NAME[:18 if CONFIG.check_temp else 9])}')

	@classmethod
	def _draw_fg(cls):
		cpu = CpuCollector
		out: str = ""
		lavg: str = ""
		x, y, w, h = cls.x + 1, cls.y + 1, cls.width - 2, cls.height - 2
		bx, by, bw, bh = cls.box_x + 1, cls.box_y + 1, cls.box_width - 2, cls.box_height - 2
		hh: int = ceil(h / 2)

		if cls.resized:
			Graphs.cpu["up"] = Graph(w - bw - 3, hh, THEME.gradient["cpu"], cpu.cpu_usage[0])
			Graphs.cpu["down"] = Graph(w - bw - 3, h - hh, THEME.gradient["cpu"], cpu.cpu_usage[0], invert=True)
			Meters.cpu = Meter(cpu.cpu_usage[0][-1], (bw - 9 - 13 if CONFIG.check_temp else bw - 9), "cpu")
			if cls.column_size > 0:
				for n in range(THREADS):
					Graphs.cores[n] = Graph(5 * cls.column_size, 1, None, cpu.cpu_usage[n + 1])
			if CONFIG.check_temp:
				Graphs.temps[0] = Graph(5, 1, None, cpu.cpu_temp[0], max_value=cpu.cpu_temp_crit, offset=-23)
				if cls.column_size > 1:
					for n in range(1, THREADS + 1):
						Graphs.temps[n] = Graph(5, 1, None, cpu.cpu_temp[n], max_value=cpu.cpu_temp_crit, offset=-23)

		cx = cy = cc = 0
		ccw = (bw + 1) // cls.box_columns
		freq: str = f'{cpu.cpu_freq} Mhz' if cpu.cpu_freq < 1000 else f'{float(cpu.cpu_freq / 1000):.1f} GHz'
		out += (f'{Mv.to(by - 1, bx + bw - 9)}{THEME.div_line(Symbol.title_left)}{Fx.b}{THEME.title(freq)}{Fx.ub}{THEME.div_line(Symbol.title_right)}'
				f'{Mv.to(y, x)}{Graphs.cpu["up"](cpu.cpu_usage[0][-1])}{Mv.to(y + hh, x)}{Graphs.cpu["down"](cpu.cpu_usage[0][-1])}'
				f'{THEME.main_fg}{Mv.to(by + cy, bx + cx)}{"CPU "}{Meters.cpu(cpu.cpu_usage[0][-1])}'
				f'{THEME.gradient["cpu"][cpu.cpu_usage[0][-1]]}{cpu.cpu_usage[0][-1]:>4}{THEME.main_fg}%')
		if CONFIG.check_temp:
				out += (f'{THEME.inactive_fg}  ⡀⡀⡀⡀⡀{Mv.l(5)}{THEME.gradient["temp"][cpu.cpu_temp[0][-1]]}{Graphs.temps[0](cpu.cpu_temp[0][-1])}'
						f'{cpu.cpu_temp[0][-1]:>4}{THEME.main_fg}°C')

		cy += 1

		for n in range(1, THREADS + 1):
			out += f'{THEME.main_fg}{Mv.to(by + cy, bx + cx)}{"Core" + str(n):<{7 if cls.column_size > 0 else 5}}'
			if cls.column_size > 0:
				out += f'{THEME.inactive_fg}{"⡀" * (5 * cls.column_size)}{Mv.l(5 * cls.column_size)}{THEME.gradient["cpu"][cpu.cpu_usage[n][-1]]}{Graphs.cores[n-1](cpu.cpu_usage[n][-1])}'
			else:
				out += f'{THEME.gradient["cpu"][cpu.cpu_usage[n][-1]]}'
			out += f'{cpu.cpu_usage[n][-1]:>4}{THEME.main_fg}%'
			if CONFIG.check_temp:
				if cls.column_size > 1:
					out += f'{THEME.inactive_fg}  ⡀⡀⡀⡀⡀{Mv.l(5)}{THEME.gradient["temp"][cpu.cpu_temp[n][-1]]}{Graphs.temps[n](cpu.cpu_temp[n][-1])}'
				else:
					out += f'{THEME.gradient["temp"][cpu.cpu_temp[n][-1]]}'
				out += f'{cpu.cpu_temp[n][-1]:>4}{THEME.main_fg}°C'
			cy += 1
			if cy == bh:
				cc += 1; cy = 1; cx = ccw * cc
				if cc == cls.box_columns: break

		if cy < bh - 1: cy = bh - 1

		if cls.column_size == 2 and CONFIG.check_temp:
			lavg = f'Load Average:  {"   ".join(str(l) for l in cpu.load_avg):^18.18}'
		elif cls.column_size == 2 or (cls.column_size == 1 and CONFIG.check_temp):
			lavg = f'L-AVG: {" ".join(str(l) for l in cpu.load_avg):^14.14}'
		else:
			lavg = f'{" ".join(str(round(l, 1)) for l in cpu.load_avg):^11.11}'
		out += f'{Mv.to(by + cy, bx + cx)}{THEME.main_fg}{lavg}'

		out += f'{Mv.to(y + h - 1, x + 1)}{THEME.inactive_fg}up {cpu.uptime}'


		Draw.buffer(cls.buffer, f'{out}{Term.fg}', save=Menu.active)
		cls.resized = False




class MemBox(Box):
	name = "mem"
	height_p = 40
	width_p = 45
	x = 1
	y = 1
	mem_meter: int = 0
	mem_size: int = 0
	disk_meter: int = 0
	divider: int = 0
	mem_width: int = 0
	disks_width: int = 0
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
		cls.width = round(Term.width * cls.width_p / 100)
		cls.height = round(Term.height * cls.height_p / 100) + 1
		Box._b_mem_h = cls.height
		cls.y = Box._b_cpu_h + 1
		if CONFIG.show_disks:
			cls.mem_width = ceil((cls.width - 3) / 2)
			cls.disks_width = cls.width - cls.mem_width - 3
			if cls.mem_width + cls.disks_width < cls.width - 2: cls.mem_width += 1
			cls.divider = cls.x + cls.mem_width
		else:
			cls.mem_width = cls.width - 1

		if cls.height - (3 if cls.swap_on and not CONFIG.swap_disk else 2) > 2 * (6 if cls.swap_on and not CONFIG.swap_disk else 4): cls.mem_size = 3
		elif cls.mem_width > 25: cls.mem_size = 2
		else: cls.mem_size = 1

		cls.mem_meter = cls.width - (cls.disks_width if CONFIG.show_disks else 0) - (9 if cls.mem_size > 2 else 20)
		if cls.mem_size == 1: cls.mem_meter += 6
		if cls.mem_meter < 1: cls.mem_meter = 0

		if CONFIG.mem_graphs:
			cls.graph_height = round(((cls.height - (2 if cls.swap_on and not CONFIG.swap_disk else 1)) - (2 if cls.mem_size == 3 else 1) * (6 if cls.swap_on and not CONFIG.swap_disk else 4)) / (6 if cls.swap_on and not CONFIG.swap_disk else 4))
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
		out: str = ""
		out += f'{create_box(box=cls, line_color=THEME.mem_box)}'
		if CONFIG.show_disks:
			out += (f'{Mv.to(cls.y, cls.divider + 2)}{THEME.mem_box(Symbol.title_left)}{Fx.b}{THEME.title("disks")}{Fx.ub}{THEME.mem_box(Symbol.title_right)}'
					f'{Mv.to(cls.y, cls.divider)}{THEME.mem_box(Symbol.div_up)}'
					f'{Mv.to(cls.y + cls.height - 1, cls.divider)}{THEME.mem_box(Symbol.div_down)}{THEME.div_line}'
					f'{"".join(f"{Mv.to(cls.y + i, cls.divider)}{Symbol.v_line}" for i in range(1, cls.height - 1))}')
		return out

	@classmethod
	def _draw_fg(cls):
		mem = MemCollector
		out: str = ""
		gbg: str = ""
		gmv: str = ""
		gli: str = ""
		x, y, h = cls.x + 1, cls.y + 1, cls.height - 2
		if cls.resized:
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
						if CONFIG.mem_graphs and not CONFIG.swap_disk:
							Meters.swap[name] = Graph(cls.mem_meter, cls.graph_height, THEME.gradient[name], mem.swap_vlist[name])
						elif CONFIG.swap_disk:
							Meters.disks_used["__swap"] = Meter(mem.swap_percent["used"], cls.disk_meter, "used")
							if len(mem.disks) * 3 <= h + 1:
								Meters.disks_free["__swap"] = Meter(mem.swap_percent["free"], cls.disk_meter, "free")
							break
						else:
							Meters.swap[name] = Meter(mem.swap_percent[name], cls.mem_meter, name)
			if cls.disk_meter > 0:
				for name in mem.disks.keys():
					Meters.disks_used[name] = Meter(mem.disks[name]["used_percent"], cls.disk_meter, "used")
					if len(mem.disks) * 3 <= h + 1:
						Meters.disks_free[name] = Meter(mem.disks[name]["free_percent"], cls.disk_meter, "free")
		#* Mem
		out += f'{Mv.to(y, x+1)}{THEME.title}{Fx.b}Total:{mem.string["total"]:>{cls.mem_width - 9}}{Fx.ub}{THEME.main_fg}'
		cx = 1; cy = 1
		# if cls.graph_height == 1:
		# 	gbg = f'{THEME.inactive_fg}{"⡀" * cls.mem_meter}{Mv.l(cls.mem_meter)}{THEME.main_fg}'
		if cls.graph_height > 0:
			gli = f'{Mv.l(2)}{THEME.mem_box(Symbol.title_right)}{THEME.div_line}{Symbol.h_line * (cls.mem_width - 1)}{"" if CONFIG.show_disks else THEME.mem_box}{Symbol.title_left}{Mv.l(cls.mem_width - 1)}{THEME.title}'
		if cls.graph_height >= 2:
			gbg = f'{Mv.l(1)}'
			gmv = f'{Mv.l(cls.mem_width - 2)}{Mv.u(cls.graph_height - 1)}'



		for name in cls.mem_names:
			if cls.mem_size > 2:
				out += (f'{Mv.to(y+cy, x+cx)}{gli}{name.capitalize()[:None if cls.mem_width > 21 else 5]+":":<{1 if cls.mem_width > 21 else 6.6}}{Mv.to(y+cy, x+cx + cls.mem_width - 3 - (len(mem.string[name])))}{mem.string[name]}'
						f'{Mv.to(y+cy+1, x+cx)}{gbg}{Meters.mem[name](mem.percent[name])}{gmv}{str(mem.percent[name])+"%":>4}'); cy += 2 if not cls.graph_height else cls.graph_height + 1
			else:
				out += f'{Mv.to(y+cy, x+cx)}{name.capitalize():{5.5 if cls.mem_size > 1 else 1.1}} {gbg}{Meters.mem[name](mem.percent[name])}{mem.string[name][:None if cls.mem_size > 1 else -2]:>{9 if cls.mem_size > 1 else 7}}'; cy += 1 if not cls.graph_height else cls.graph_height
		#* Swap
		if cls.swap_on and CONFIG.show_swap and not CONFIG.swap_disk:
			if h - cy > 5:
				if cls.graph_height > 0: out += f'{Mv.to(y+cy, x+cx)}{gli}'
				cy += 1
			out += f'{Mv.to(y+cy, x+cx)}{THEME.title}{Fx.b}Swap:{mem.swap_string["total"]:>{cls.mem_width - 8}}{Fx.ub}{THEME.main_fg}'; cy += 1
			for name in cls.swap_names:
				if cls.mem_size > 2:
					out += (f'{Mv.to(y+cy, x+cx)}{gli}{name.capitalize()[:None if cls.mem_width > 21 else 5]+":":<{1 if cls.mem_width > 21 else 6.6}}{Mv.to(y+cy, x+cx + cls.mem_width - 3 - (len(mem.swap_string[name])))}{mem.swap_string[name]}'
							f'{Mv.to(y+cy+1, x+cx)}{gbg}{Meters.swap[name](mem.swap_percent[name])}{gmv}{str(mem.swap_percent[name])+"%":>4}'); cy += 2 if not cls.graph_height else cls.graph_height + 1
				else:
					out += f'{Mv.to(y+cy, x+cx)}{name.capitalize():{5.5 if cls.mem_size > 1 else 1.1}} {gbg}{Meters.swap[name](mem.swap_percent[name])}{mem.swap_string[name][:None if cls.mem_size > 1 else -2]:>{9 if cls.mem_size > 1 else 7}}'; cy += 1 if not cls.graph_height else cls.graph_height

		if cls.graph_height > 0 and not cy == h: out += f'{Mv.to(y+cy, x+cx)}{gli}'

		#* Disks
		if CONFIG.show_disks:
			cx = x + cls.mem_width - 1; cy = 0
			for name, item in mem.disks.items():
				if cy > h - 2: break
				out += (f'{Mv.to(y+cy, x+cx)}{THEME.title}{Fx.b}{item["name"]:{cls.disks_width - 2}.12}{Mv.to(y+cy, x + cx + cls.disks_width - 11)}{item["total"][:None if cls.disks_width >= 25 else -2]:>9}'
						f'{Mv.to(y+cy, x + cx + (cls.disks_width // 2) - (len(item["io"]) // 2) - 2)}{Fx.ub}{THEME.main_fg}{item["io"]}{Fx.ub}{THEME.main_fg}{Mv.to(y+cy+1, x+cx)}')
				out += f'Used:{str(item["used_percent"]) + "%":>4} ' if cls.disks_width >= 25 else "U "
				out += f'{Meters.disks_used[name]}{item["used"][:None if cls.disks_width >= 25 else -2]:>{9 if cls.disks_width >= 25 else 7}}'; cy += 2

				if len(mem.disks) * 3 <= h + 1:
					if cy > h - 1: break
					out += Mv.to(y+cy, x+cx)
					out += f'Free:{str(item["free_percent"]) + "%":>4} ' if cls.disks_width >= 25 else f'{"F "}'
					out += f'{Meters.disks_free[name]}{item["free"][:None if cls.disks_width >= 25 else -2]:>{9 if cls.disks_width >= 25 else 7}}'; cy += 1
					if len(mem.disks) * 4 <= h + 1: cy += 1

		Draw.buffer(cls.buffer, f'{out}{Term.fg}', save=Menu.active)
		cls.resized = False

class NetBox(Box, SubBox):
	name = "net"
	height_p = 28
	width_p = 45
	x = 1
	y = 1
	redraw: bool = True
	buffer: str = "net"
	Box.buffers.append(buffer)

	@classmethod
	def _calc_size(cls):
		cls.width = round(Term.width * cls.width_p / 100)
		cls.height = Term.height - Box._b_cpu_h - Box._b_mem_h
		cls.y = Term.height - cls.height + 1
		cls.box_width = 24
		cls.box_height = 9 if cls.height > 12 else cls.height - 2
		cls.box_x = cls.width - cls.box_width - 2
		cls.box_y = cls.y + ((cls.height - 2) // 2) - cls.box_height // 2 + 1
		cls.redraw_all = True

	@classmethod
	def _draw_bg(cls) -> str:
		return f'{create_box(box=cls, line_color=THEME.net_box)}\
		{create_box(x=cls.box_x, y=cls.box_y, width=cls.box_width, height=cls.box_height, line_color=THEME.div_line, fill=False, title="Download", title2="Upload")}'

class ProcBox(Box):
	name = "proc"
	height_p = 68
	width_p = 55
	x = 1
	y = 1
	detailed: bool = False
	detailed_x: int = 0
	detailed_y: int = 0
	detailed_width: int = 0
	detailed_height: int = 8
	redraw: bool = True
	buffer: str = "proc"
	Box.buffers.append(buffer)

	@classmethod
	def _calc_size(cls):
		cls.width = round(Term.width * cls.width_p / 100)
		cls.height = round(Term.height * cls.height_p / 100)
		cls.x = Term.width - cls.width + 1
		cls.y = Box._b_cpu_h + 1
		cls.detailed_x = cls.x
		cls.detailed_y = cls.y
		cls.detailed_height = 8
		cls.detailed_width = cls.width
		cls.redraw_all = True

	@classmethod
	def _draw_bg(cls) -> str:
		return create_box(box=cls, line_color=THEME.proc_box)

class Collector:
	'''Data collector master class
	* .start(): Starts collector thread
	* .stop(): Stops collector thread
	* .collect(*collectors: Collector, draw_now: bool = True, interrupt: bool = False): queues up collectors to run'''
	stopping: bool = False
	started: bool = False
	draw_now: bool = False
	thread: threading.Thread
	collect_run = threading.Event()
	collect_idle = threading.Event()
	collect_idle.set()
	collect_done = threading.Event()
	collect_queue: List = []
	collect_interrupt: bool = False

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
		try:
			while not cls.stopping:
				cls.collect_run.wait(0.1)
				if not cls.collect_run.is_set():
					continue
				draw_buffers = []
				#if cls.collect_interrupt and bkp_queue:
				#	for q in bkp_queue:
				#		if q not in cls.collect_queue: cls.collect_queue.append(q)
				#bkp_queue = []
				cls.collect_interrupt = False
				cls.collect_run.clear()
				cls.collect_idle.clear()
				while cls.collect_queue:
					collector = cls.collect_queue.pop()
					collector._collect()
					collector._draw()
					#bkp_queue.append(collector)
					draw_buffers.append(collector.buffer)
					if cls.collect_interrupt: break
				if cls.draw_now and not Menu.active and not cls.collect_interrupt:
					Draw.out(*draw_buffers)
				cls.collect_idle.set()
				cls.collect_done.set()
		except Exception as e:
			errlog.exception(f'Data collection thread failed with exception: {e}')
			cls.collect_done.set()
			clean_quit(1, thread=True)

	@classmethod
	def collect(cls, *collectors, draw_now: bool = True, interrupt: bool = False):
		'''Setup collect queue for _runner'''
		#* Set interrupt flag if True to stop _runner prematurely
		cls.collect_interrupt = interrupt
		#* Wait for _runner to finish
		cls.collect_idle.wait()
		#* Reset interrupt flag
		cls.collect_interrupt = False
		#* Set draw_now flag if True to draw to screen instead of buffer
		cls.draw_now = draw_now
		#* Append any collector given as argument to _runner queue
		if collectors:
			cls.collect_queue = [*collectors]

		#* Add all collectors to _runner queue if no collectors in argument
		else:
			cls.collect_queue = list(cls.__subclasses__())

		#* Set run flag to start _runner
		cls.collect_run.set()


class CpuCollector(Collector):
	'''Collects cpu usage for cpu and cores, cpu frequency, load_avg, uptime and cpu temps'''
	cpu_usage: List[List[int]] = []
	cpu_temp: List[List[int]] = []
	cpu_temp_high: int = 0
	cpu_temp_crit: int = 0
	for _ in range(THREADS + 1):
		cpu_usage.append([])
		cpu_temp.append([])
	cpu_freq: int = 0
	load_avg: List[float] = []
	uptime: str = ""
	buffer: str = CpuBox.buffer

	@staticmethod
	def _get_sensors() -> str:
		'''Check if we can get cpu temps and return method of getting temps'''
		if SYSTEM == "MacOS":
			try:
				if which("osx-cpu-temp") and subprocess.check_output("osx-cpu-temp", text=True).rstrip().endswith("°C"):
					return "osx-cpu-temp"
			except: pass
		elif hasattr(psutil, "sensors_temperatures"):
			try:
				temps = psutil.sensors_temperatures()
				if temps:
					for _, entries in temps.items():
						for entry in entries:
							if entry.label.startswith(("Package", "Core 0", "Tdie")):
								return "psutil"
			except: pass
		try:
			if SYSTEM == "Linux" and which("vcgencmd") and subprocess.check_output("vcgencmd measure_temp", text=True).rstrip().endswith("'C"):
				return "vcgencmd"
		except: pass
		return ""

	sensor_method: str = _get_sensors.__func__() # type: ignore
	got_sensors: bool = True if sensor_method else False

	@classmethod
	def _collect(cls):
		cls.cpu_usage[0].append(round(psutil.cpu_percent(percpu=False)))

		for n, thread in enumerate(psutil.cpu_percent(percpu=True), start=1):
			cls.cpu_usage[n].append(round(thread))
			if len(cls.cpu_usage[n]) > Term.width * 2:
				del cls.cpu_usage[n][0]

		cls.cpu_freq = round(psutil.cpu_freq().current)
		cls.load_avg = [round(lavg, 2) for lavg in os.getloadavg()]
		cls.uptime = str(timedelta(seconds=round(time()-psutil.boot_time(),0)))[:-3]

		if CONFIG.check_temp and cls.got_sensors:
			cls._collect_temps()

	@classmethod
	def _collect_temps(cls):
		temp: int
		cores: List[int] = []
		cpu_type: str = ""
		if cls.sensor_method == "psutil":
			for _, entries in psutil.sensors_temperatures().items():
				for entry in entries:
					if entry.label.startswith(("Package", "Tdie")):
						cpu_type = "ryzen" if entry.label.startswith("Package") else "ryzen"
						if not cls.cpu_temp_high:
							cls.cpu_temp_high, cls.cpu_temp_crit = round(entry.high), round(entry.critical)
						temp = round(entry.current)
					elif entry.label.startswith(("Core", "Tccd")):
						if not cpu_type:
							cpu_type = "other"
							if not cls.cpu_temp_high:
								cls.cpu_temp_high, cls.cpu_temp_crit = round(entry.high), round(entry.critical)
							temp = round(entry.current)
						cores.append(round(entry.current))
			if len(cores) < THREADS:
				if cpu_type == "intel" or (cpu_type == "other" and len(cores) == THREADS // 2):
					cls.cpu_temp[0].append(temp)
					for n, t in enumerate(cores, start=1):
						cls.cpu_temp[n].append(t)
						cls.cpu_temp[THREADS // 2 + n].append(t)
				elif cpu_type == "ryzen" or cpu_type == "other":
					cls.cpu_temp[0].append(temp)
					if len(cores) < 1: cores.append(temp)
					z = 1
					for t in cores:
						for i in range(THREADS // len(cores)):
							cls.cpu_temp[z + i].append(t)
						z += i
			else:
				cores.insert(0, temp)
				for n, t in enumerate(cores):
					cls.cpu_temp[n].append(t)

		else:
			try:
				if cls.sensor_method == "osx-cpu-temp":
					temp = round(float(subprocess.check_output("osx-cpu-temp", text=True).rstrip().rstrip("°C")))
				elif cls.sensor_method == "vcgencmd":
					temp = round(float(subprocess.check_output("vcgencmd measure_temp", text=True).rstrip().rstrip("'C")))
			except Exception as e:
					errlog.exception(f'{e}')
					cls.got_sensors = False
					CONFIG.check_temp = False
					CpuBox._calc_size()
			else:
				for n in range(THREADS + 1):
					cls.cpu_temp[n].append(temp)

		if len(cls.cpu_temp[0]) > 5:
			for n in range(len(cls.cpu_temp)):
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

	excludes: List[str] = ["squashfs"]
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

			MemBox.swap_on = bool(swap.total)
			if swap.total:
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
				MemBox.swap_on = False
		else:
			MemBox.swap_on = False


		if not CONFIG.show_disks: return
		#* Collect disks usage
		disk_read: int = 0
		disk_write: int = 0
		dev_name: str
		disk_name: str
		filtering: Tuple = ()
		filter_exclude: bool = False
		io_string: str
		u_percent: int
		disk_list: List[str] = []
		cls.disks = {}

		if CONFIG.disks_filter:
			if CONFIG.disks_filter.startswith("exclude="):
				filter_exclude = True
				filtering = tuple(v.strip() for v in CONFIG.disks_filter.replace("exclude=", "").strip().split(","))
			else:
				filtering = tuple(v.strip() for v in CONFIG.disks_filter.strip().split(","))

		io_counters = psutil.disk_io_counters(perdisk=True if SYSTEM == "Linux" else False, nowrap=True)

		for disk in psutil.disk_partitions():
			disk_io = None
			io_string = ""
			disk_name = disk.mountpoint.rsplit('/', 1)[-1] if not disk.mountpoint == "/" else "root"
			while disk_name in disk_list: disk_name += "_"
			disk_list += [disk_name]
			if cls.excludes and disk.fstype in cls.excludes:
				continue
			if filtering and ((not filter_exclude and not disk_name.endswith(filtering)) or (filter_exclude and disk_name.endswith(filtering))):
				continue
			#elif filtering and disk_name.endswith(filtering)
			if SYSTEM == "MacOS" and disk.mountpoint == "/private/var/vm":
				continue
			try:
				disk_u = psutil.disk_usage(disk.mountpoint)
			except:
				pass

			u_percent = round(disk_u.percent)
			cls.disks[disk.device] = {}
			cls.disks[disk.device]["name"] = disk_name
			cls.disks[disk.device]["used_percent"] = u_percent
			cls.disks[disk.device]["free_percent"] = 100 - u_percent
			for name in ["total", "used", "free"]:
				cls.disks[disk.device][name] = floating_humanizer(getattr(disk_u, name, 0))

			#* Collect disk io
			try:
				if SYSTEM == "Linux":
					dev_name = os.path.realpath(disk.device).rsplit('/', 1)[-1]
					if dev_name.startswith("md"):
						try:
							dev_name = dev_name[:dev_name.index("p")]
						except:
							pass
					disk_io = io_counters[dev_name]
				elif disk.mountpoint == "/":
					disk_io = io_counters
				else:
					raise Exception
				disk_read = disk_io.read_bytes - cls.disk_hist[disk.device][0]
				disk_write = disk_io.write_bytes - cls.disk_hist[disk.device][1]
			except:
				pass
				disk_read = disk_write = 0

			if disk_io:
				cls.disk_hist[disk.device] = (disk_io.read_bytes, disk_io.write_bytes)
				if MemBox.disks_width > 30:
					if disk_read > 0:
						io_string += f'▲{floating_humanizer(disk_read, short=True)} '
					if disk_write > 0:
						io_string += f'▼{floating_humanizer(disk_write, short=True)}'
				elif disk_read + disk_write > 0:
					io_string += f'▼▲{floating_humanizer(disk_read + disk_write, short=True)}'

			cls.disks[disk.device]["io"] = io_string

		if CONFIG.swap_disk:
			cls.disks["__swap"] = {}
			cls.disks["__swap"]["name"] = "swap"
			cls.disks["__swap"]["used_percent"] = cls.swap_percent["used"]
			cls.disks["__swap"]["free_percent"] = cls.swap_percent["free"]
			for name in ["total", "used", "free"]:
				cls.disks["__swap"][name] = cls.swap_string[name]
			cls.disks["__swap"]["io"] = ""
			if len(cls.disks) > 2:
				try:
					new = { list(cls.disks)[0] : cls.disks.pop(list(cls.disks)[0])}
					new["__swap"] = cls.disks.pop("__swap")
					new.update(cls.disks)
					cls.disks = new
				except:
					pass


	@classmethod
	def _draw(cls):
		MemBox._draw_fg()

#class ProcCollector(Collector): #! add interrupt on _collect and _draw

@timerd
def testing_collectors():

	# CONFIG.check_temp = True
	# Box.calc_sizes()
	Box.draw_bg()

	#for _ in range(1000):
	while True:
		Collector.collect()
		Collector.collect_done.wait()
		Draw.now(Mv.to(1, 1))
		sleep(1)

	Draw.now(Mv.to(Term.height - 5, 1))
	#Draw.now(f'Cpu usage: {CpuCollector.cpu_usage}\nCpu freq: {CpuCollector.cpu_freq}\nLoad avg: {CpuCollector.load_avg}\n\
	#	Temps: {CpuCollector.cpu_temp}\n')


class Menu:
	'''Holds the main menu and all submenus'''
	active: bool = False

	#Draw.buffer("menubg", Draw.last_buffer, z=1000, uncolor=True)
	#Draw.clear("menubg", last=True)




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
	if "Xeon" in name:
		name = nlist[nlist.index("CPU")+1]
	elif "Ryzen" in name:
		name = " ".join(nlist[nlist.index("Ryzen"):nlist.index("Ryzen")+3])
	elif "CPU" in name:
		name = nlist[nlist.index("CPU")-1]

	return name

def create_box(x: int = 0, y: int = 0, width: int = 0, height: int = 0, title: str = "", title2: str = "", line_color: Color = None, fill: bool = True, box = None) -> str:
	'''Create a box from a box object or by given arguments'''
	out: str = f'{Term.fg}{Term.bg}'
	if not line_color: line_color = THEME.div_line

	#* Get values from box class if given
	if box:
		x = box.x
		y = box.y
		width = box.width
		height =box.height
		title = box.name
	vlines: Tuple[int, int] = (x, x + width - 1)
	hlines: Tuple[int, int] = (y, y + height - 1)

	#* Fill box if enabled
	if fill:
		for i in range(y + 1, y + height - 1):
			out += f'{Mv.to(i, x)}{" " * (width - 1)}'

	out += f'{line_color}'

	#* Draw all horizontal lines
	for hpos in hlines:
		out += f'{Mv.to(hpos, x)}{Symbol.h_line * (width - 1)}'

	#* Draw all vertical lines
	for vpos in vlines:
		for hpos in range(y, y + height - 1):
			out += f'{Mv.to(hpos, vpos)}{Symbol.v_line}'

	#* Draw corners
	out += f'{Mv.to(y, x)}{Symbol.left_up}\
	{Mv.to(y, x + width - 1)}{Symbol.right_up}\
	{Mv.to(y + height - 1, x)}{Symbol.left_down}\
	{Mv.to(y + height - 1, x + width - 1)}{Symbol.right_down}'

	#* Draw titles if enabled
	if title:
		out += f'{Mv.to(y, x + 2)}{Symbol.title_left}{THEME.title}{Fx.b}{title}{Fx.ub}{line_color}{Symbol.title_right}'
	if title2:
		out += f'{Mv.to(y + height - 1, x + 2)}{Symbol.title_left}{THEME.title}{Fx.b}{title2}{Fx.ub}{line_color}{Symbol.title_right}'

	return f'{out}{Term.fg}{Mv.to(y + 1, x + 1)}'

def now_sleeping(signum, frame):
	"""Reset terminal settings and stop background input read before putting to sleep"""
	Key.stop()
	Collector.stop()
	Draw.now(Term.clear, Term.normal_screen, Term.show_cursor)
	Term.echo(True)
	os.kill(os.getpid(), signal.SIGSTOP)

def now_awake(signum, frame):
	"""Set terminal settings and restart background input read"""
	Draw.now(Term.alt_screen, Term.clear, Term.hide_cursor)
	Term.echo(False)
	Key.start()
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
	if not testing: Draw.now(Term.clear, Term.normal_screen, Term.show_cursor) #! Enable
	else: Draw.now(Term.show_cursor) #! Remove
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
	unit: Tuple[str, ...] = UNITS["bit"] if bit else UNITS["byte"]
	selector: int = start if start else 0
	mult: int = 8 if bit else 1
	if value <= 0: value = 0

	if isinstance(value, float): value = round(value * 100 * mult)
	elif value > 0: value *= 100 * mult

	while len(f'{value}') > 5 and value >= 102400:
		value >>= 10
		if value < 100:
			out = f'{value}'
			break
		selector += 1
	else:
		if len(f'{value}') < 5 and len(f'{value}') >= 2 and selector > 0:
			decimals = 5 - len(f'{value}')
			out = f'{value}'[:-2] + "." + f'{value}'[-decimals:]
		elif len(f'{value}') >= 2:
			out = f'{value}'[:-2]


	if short: out = out.split(".")[0]
	out += f'{"" if short else " "}{unit[selector][0] if short else unit[selector]}'
	if per_second: out += "/s" if bit else "ps"

	return out


#? Main function --------------------------------------------------------------------------------->

def main():
	clean_quit()


#? Pre main -------------------------------------------------------------------------------------->


CPU_NAME: str = get_cpu_name()

testing = True #! Remove

#! For testing ------------------------------------------------------------------------------->



def waitone(t: float = 0.0):
	if t > 0.0: Key.new.wait(t)
	else: Key.new.wait()
	Key.new.clear()
	Draw.clear()
	Draw.now(Term.clear)

@timerd
def testing_gradients():
	# for theme in THEME.themes.keys():
		# THEME(theme)
		# timer = time()

	for key in THEME.gradient.keys():
		Draw.now(f'{Term.fg}{key}:\n{"█".join(THEME.gradient[key])}\n')
	Draw.now(f'{Term.fg}')
		# Draw.now(f'Theme creation of {CONFIG.color_theme} took {time() - timer:.5f} seconds\n\n')
	Draw.now("\n")
	# THEME("Default")

@timerd
def testing_humanizer():
	for i in range(1, 101, 3):
		for n in range(1, 6):
			Draw.now(floating_humanizer(i * (1050 * n) * (n << 10 ), bit=False, per_second=False, short=False), "  ")
		Draw.now("\n")
	for i in range(1, 30):
		for n in range(1, 8):
			Draw.now(floating_humanizer((995 + i) << (n * 10), bit=False), "  ")
		Draw.now("\n")


@timerd
def testing_colors():
	for item, _ in DEFAULT_THEME.items():
		Draw.buffer("+testing", Fx.b, getattr(THEME, item)(f'{item:<20}'), Fx.ub, f'{"hex=" + getattr(THEME, item).hexa:<20} dec={getattr(THEME, item).dec}\n')

	Draw.out()

@timerd
def testing_boxes():
	#Box.calc_sizes()
	Box.draw_bg()
	Draw.now(Mv.to(Term.height - 3, 1))
	#Draw.now(create_box(20, 20, 15, 10, "Hej"))
	#waitone()
	#Draw.now(Term.normal_screen, Term.show_cursor)

@timerd
def testing_banner():
	Draw.buffer("banner", Banner.draw(18, center=True))
	Draw.out()

	Draw.now(Mv.to(35, 1))

@timerd
def testing_meter():
	Draw.clear("meters")
	for _ in range(10):
		Draw.buffer("+meters", "1234567890")
	Draw.buffer("+meters", "\n")

	stamp = time()
	test_meter = Meter(0, Term.width, "cpu")

	for i in range(0,101, 2):
		Draw.buffer("+meters", test_meter(i), "\n")

	Draw.buffer("+meter", f'{time() - stamp}')
	Draw.out()

def testing_keyinput():
	line: str = ""
	this_key: str = ""
	count: int = 0
	while True:
		count += 1
		Draw.now(f'{Mv.to(1,1)}{Fx.b}{THEME.temp_start("Count:")} {count}  {THEME.cached_mid("Time:")} {strftime("%H:%M:%S", localtime())}',
		f'{Color.fg("#ff")}  Width: {Term.width}  Height: {Term.height}  Resized: {Term.resized}')
		if Key.input_wait(1):
			while Key.list:
				#Key.new.clear()
				this_key = Key.list.pop()
				Draw.now(f'{Mv.to(2,1)}{Color.fg("#ff9050")}{Fx.b}Last key= {Term.fg}{Fx.ub}{repr(this_key):14}{"  "}')
				if this_key == "backspace":
					line = line[:-1]
				elif this_key == "escape":
					line = ""
				elif this_key == "Q":
					clean_quit()
				elif this_key == "R":
					raise Exception("Test ERROR")
				elif len(this_key) == 1:
					line += this_key
				Draw.now(f'{Color.fg("#90ff50")}{Fx.b}Command= {Term.fg}{Fx.ub}{line}{Fx.bl}| {Fx.ubl}\033[0K\n')
				if this_key == "enter":
					try:
						exec(line)
					except:
						pass
					Draw.clear()

def testing_graphs():
	my_data = [x for x in range(0, 101)]
	my_data += [x for x in range(100, -1, -1)]


	my_graph = Graph(100, 1, THEME.main_fg, my_data)
	Draw.now(f'{Fx.ub}{Mv.to(0, 0)}{my_graph}')

	return

	my_data100 = [randint(0, 100) for _ in range(Term.width * 2)]

	my_data2 = my_data[-90:]
	my_data3 = my_data[:86]

	my_colors = []
	for i in range(51):
		for _ in range(2): my_colors.append(Color.fg(i, i, i))
	#my_colors.reverse()


	my_graph = Graph(Term.width, Term.height // 2, my_colors, my_data100, invert=True)
	my_graph2 = Graph(Term.width, Term.height // 2, my_colors, my_data100, invert=False)

	# my_graph3 = Graph(100 // 3 + 10, 1, THEME.proc_misc, my_data2)
	# my_graph4 = Graph(100 // 3 + 10, 1, THEME.proc_misc, my_data3)
	# my_graph5 = Graph(100, Term.height // 3, THEME.inactive_fg, my_data)

	#pause = re.compile(r"\033\[\d+;\d?;?\d*;?\d*;?\d*m{1}")
	#repl = "\033[0;37m"

	banner = Banner.draw(Term.height // 3 - 2, center=True)

	Draw.now(f'{Fx.ub}{Mv.to(0, 0)}{my_graph}\
	{Mv.to(Term.height // 2, 0)}{my_graph2}\
	{banner}')

	# {Mv.to(Term.height - (Term.height // 3), Term.width // 2 - 50)}{my_graph5}\
	# {Mv.to(Term.height - (Term.height // 3) - 1, Term.width // 2 - 50)}{my_graph3}\
	# {Mv.to(Term.height - (Term.height // 3) - 1, Term.width // 2 + 7)}{my_graph4}\

	#t = 1
	x = 0
	for _ in range(200):
		sleep(0.05)
		x = randint(0, 100)
		# x += 1 if t == 1 else -1
		# if x == 100: t = 0
		# if x == 0: t = 1
		Draw.now(f'{Fx.ub}{Mv.to(0, 0)}{my_graph.add(x)}\
		{Mv.to(Term.height // 2, 0)}{my_graph2.add(x)}\
		{banner}')

		# 		Draw.now(f'{Mv.to(Term.height - (Term.height // 3), Term.width // 2 - 50)}{my_graph5.add(x)}')
		# Draw.now(f'{Mv.to(Term.height - (Term.height // 3) - 1, Term.width // 2 - 50)}{my_graph3.add(x)}')
		# Draw.now(f'{Mv.to(Term.height - (Term.height // 3) - 1, Term.width // 2 + 7)}{my_graph4.add(x)}')

	Draw.now(Mv.to(Term.height -4, 0))

#! Remove ------------------------------------------------------------------------------------<

if __name__ == "__main__":

	#? Init -------------------------------------------------------------------------------------->
	Timer.start("Init")

	class Init:
		running: bool = True
		initbg_colors: List[str] = []
		initbg_data: List[int]
		initbg_up: Graph
		initbg_down: Graph

		@staticmethod
		def fail(err):
			Draw.buffer("+init!", f'{Mv.restore}{Symbol.fail}')
			errlog.exception(f'{err}')
			sleep(2)
			clean_quit(1, errmsg=f'Error during init! See {CONFIG_DIR}/error.log for more information.')

		@classmethod
		def success(cls, start: bool = False):
			if start:
				Draw.buffer("initbg", z=10)
				Draw.buffer("init", z=1)
				for i in range(51):
					for _ in range(2): cls.initbg_colors.append(Color.fg(i, i, i))
				Draw.buffer("banner", f'{Banner.draw(Term.height // 2 - 10, center=True)}{Color.fg("#50")}\n', z=2)
				for _i in range(10):
					perc = f'{str((_i + 1) * 10) + "%":>5}'
					Draw.buffer("+banner", f'{Mv.to(Term.height // 2 - 3 + _i, Term.width // 2 - 28)}{Fx.trans(perc)}{Symbol.v_line}')
				Draw.out("banner")
				Draw.buffer("+init!", f'{Color.fg("#cc")}{Fx.b}{Mv.to(Term.height // 2 - 3, Term.width // 2 - 21)}{Mv.save}')

			if start or Term.resized:
				cls.initbg_data = [randint(0, 100) for _ in range(Term.width * 2)]
				cls.initbg_up = Graph(Term.width, Term.height // 2, cls.initbg_colors, cls.initbg_data, invert=True)
				cls.initbg_down = Graph(Term.width, Term.height // 2, cls.initbg_colors, cls.initbg_data, invert=False)

			if start: return

			if not testing:
				cls.draw_bg(10)
			Draw.buffer("+init!", f'{Mv.restore}{Symbol.ok}\n{Mv.r(Term.width // 2 - 22)}{Mv.save}')

		@classmethod
		def draw_bg(cls, times: int = 10):
			for _ in range(times):
				sleep(0.05)
				x = randint(0, 100)
				Draw.buffer("initbg", f'{Fx.ub}{Mv.to(0, 0)}{cls.initbg_up.add(x)}{Mv.to(Term.height // 2, 0)}{cls.initbg_down.add(x)}')
				Draw.out("initbg", "banner", "init")

		@classmethod
		def done(cls):
			cls.draw_bg(20)
			Draw.clear("initbg", "banner", "init")
			cls.running = False
			del cls.initbg_up, cls.initbg_down, cls.initbg_data, cls.initbg_colors


	#? Switch to alternate screen, clear screen, hide cursor and disable input echo
	if not testing: Draw.now(Term.alt_screen, Term.clear, Term.hide_cursor) #! Enable
	else: Draw.now(Term.clear, Term.hide_cursor) #! Disable
	Term.echo(False)

	#? Draw banner and init status
	if not testing: Init.success(start=True)

	#? Load theme
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Loading theme and creating colors... ")}{Mv.save}')
	try:
		THEME: Theme = Theme(CONFIG.color_theme)
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Setup boxes
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Doing some maths and drawing... ")}{Mv.save}')
	try:
		Box.calc_sizes()
		Box.draw_bg(now=False)
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Setup signal handlers for SIGSTP, SIGCONT, SIGINT and SIGWINCH
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
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Starting input reader thread... ")}{Mv.save}')
	try:
		Key.start()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Start a separate thread for data collection and drawing
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Starting data collection and drawer thread... ")}{Mv.save}')
	try:
		Collector.start()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Collect data and draw to buffer
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Collecting data and drawing... ")}{Mv.save}')
	try:
		#Collector.collect(draw_now=False)
		pass
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Collecting nuclear launch codes... ")}{Mv.save}')
	Init.success()
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Launching missiles... ")}{Mv.save}')
	Init.success()
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Alien invasion... ")}{Mv.save}')
	Init.success()

	#? Draw to screen
	Draw.buffer("+init!", f'{Mv.restore}{Fx.trans("Finishing up... ")}{Mv.save}')
	try:
		#Collector.collect_done.wait()
		pass
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()


	if not testing: Init.done() #! Remove if
	if not testing: Draw.out(clear=True) #! Remove if
	else: Draw.clear(); Draw.now(Term.clear); Init.running = False #! Remove
	Timer.stop("Init")


	#! For testing ------------------------------------------------------------------------------->
	if testing:
		try:
			#testing_graphs()
			testing_collectors()
			#testing_humanizer()
			# waitone(1)
			#testing_keyinput()
			#testing_banner()
			# waitone(1)
			#testing_colors()
			# waitone(1)
			#testing_gradients()
			# waitone(1)
			#testing_boxes()
			# waitone(1)
			#testing_meter()
			# Draw.idle.clear()
			#Draw.now(f'{Mv.to(Term.height - 5, 1)}Any key to exit!')
			#waitone()
			# Draw.idle.set()
			#sleep(2)
		except Exception as e:
			errlog.exception(f'{e}')
			clean_quit(1)

		clean_quit()
	#! Remove ------------------------------------------------------------------------------------<

	#? Start main loop
	while not False:
		try:
			main()
		except Exception as e:
			errlog.exception(f'{e}')
			clean_quit(1)
	else:
		#? Quit cleanly even if false starts being true...
		clean_quit()
