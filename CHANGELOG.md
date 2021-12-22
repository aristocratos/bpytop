# Changelog

## v1.0.68

* Fixed: typos discovered by codespell, by @cclauss
* Added: search processes using vim keybinds, by @jedi2610
* Fixed: Removed a simple consider-using-in pitfall case, by @NaelsonDouglas
* Added: New theme gruvbox_dark_v2, by @pietryszak
* Fixed: Implement strtobool over distutils strtobool, by @RCristiano

## v1.0.67

* Fixed: Removed not needed escape character replacements
* Fixed: Themes missing when installing with pip3
* Fixed: Color in-range check, by @GerbenWelter

## v1.0.66

* Fixed: Program not stalling when system time is changed and regular update of current timezone
* Fixed: NetBox not redrawing when network interface is removed, by @UmarJ
* Fixed: Some typos

## v1.0.65

* Fixed: Removed degrees symbol from Kelvin scale, by @jrbergen
* Fixed: Mouse buttons not working in netbox when changing interface
* Fixed: q key not working when terminal size warning is showed
* Fixed: Cleanup of unused libraries and other small fixes

## v1.0.64

* Changed: Init screen not shown by default
* Fixed: Broken cleanup in ProcBox class
* Fixed: cpu frequency type change in psutil 5.8.1
* Added: Option to toggle CPU frequency
* Fixed: Check for config in /usr/local/etc instead of /etc on BSD

## v1.0.63

* Added: Options for choosing temperature scale and re-added support for negative celsius temps
* Changed: Cpu values above 0 will always register on the graphs

## v1.0.62

* Fixed: Support cpus with non-sequential core ids, patch by @ErwinJunge
* Added: New theme Adapta, by @olokelo
* Changed: Net graphs will now round up any value above 0 to register on graph

## v1.0.61

* Added: Vim keys (h, j, k, l) for browsing and moved help to shift+h
* Changed: Size constraints now adapts to currently shown boxes

## v1.0.60

* Added: Ignore input unicode decode errors
* Fixed: Wrong letter in "io" highlighted
* Fixed: Crash on missing psutil.disk_usage
* Added: Toggle for IO graphs in regular disk usage mode
* Added: Toggle for uptime and uptime added as a option for the clock formatting
* Added: Ability choose cpu graph attributes and split up upper and lower part
* Added: Ability to toggle one big CPU graph instead of two combined graphs
* Added: IP address to net box

## v1.0.59

* Fixed: Crash on missing disks
* Fixed: IO stats text transparency

## v1.0.58

* Added: Disks io stat graphs and a dedicated io mode for disks box
* Fixed: Better detection for disk io stats including multiple disks for OsX
* Changed: Terminate, Kill, Interrupt shortcuts now only uses uppercase T, K, I
* Changed: Process filtering changed to non case-sensitive, patch by @UmarJ
	* Case-sensitive proc filtering using uppercase F
* Changed: Get CPU load average from psutil module instead of os module, patch by @araczkowski
* Fixed: Misc bugs

## v1.0.57

* Fixed: proc_sorting option counter not updating in menu, by @UmarJ
* Added: Support for non truecolor terminals through 24-bit to 256-color conversion
	* Activate by setting "truecolor" variable to False or starting with "-lc/--low-color" argument

## v1.0.56

* Fixed: units_to_bytes returning 0 if input value <10 and in bits
* Added: Testing for some functions and classes
* Added: net_iface variable to set startup network interface, by @raTmole
* Added: use_fstab variable to get the disk list from /etc/fstab, by @BrHal
* Added: Categories in Options menu and only_physical option for disks

## v1.0.55

* Fixed: Disks usage and free meters not updating unless resized
* Changed: All boxes are now toggeable with key 1-4, start argument -b/--boxes and config variable shown_boxes.
* Changed: Moved testing from Travis CI to Github workflow

## v1.0.54

* Fixed: Added nullfs filesystem to auto exclude from disks list
* Fixed: Process box not updating on window resize

## v1.0.53

* Added: Process update multiplier (only update processes every X times) to reduce cpu usage (set to 2 by default)
* Changed: Patch for faster loading of config file, by @rohithill
* Added: Network interface list now updates automatically, by @UmarJ
* Notice: Bumped minimum python version to 3.7 because of unicode issues in 3.6
* Added: pylint disable=unsubscriptable-object because of python 3.9 issue
* Changed: Default theme now has a black background
* Fixed: Crash if bpytop.conf exists but don't have update_ms variable set

## v1.0.52

* Fixed: Removed "/sys/class/power_supply" check for FreeBSD and OsX

## v1.0.51

* Fixed: Text argument in subprocess not working on python 3.6
* Changed: Disks filtering now uses full mountpoint path for better accuracy
* Fixed: Disable battery detection if /sys/class/power_supply is missing to avoid exception is psutil
* Fixed: Catch faulty temperature readings instead of crashing
* Changed: psutil update to 5.8.0 in pypi package (fixes errors on apple silicon cpus)

## v1.0.50

* Fixed: Correction for missing coretemp values
* Fixed: Cpu temp calculation from cores if missing and better multi cpu temp support
* Added: New theme dusklight, by @drazil100

## v1.0.49

* Fixed: Missing default values for cpu temp high and crit

## v1.0.48

* Added: Sync clock to timer if timer = 1000ms
* Fixed: Wrong coretemp mapping when missing package id 0
* Fixed: Sizing when coretemp is hidden
* Added: Link to Terminess Powerline with included braille symbols in README.md

## v1.0.47

* Added: Testing, by @ErwinJunge
* Added: Theme matcha-dark-sea, by @TheCynicalLiger
* Fixed: New type errors for mypy v 0.790
* Added: pylint and mypy test with tox, by @ErwinJunge

## v1.0.46

* Changed: psutil update to 5.7.3 in pypi package
* Fixed: Better sensor and temperature detection

## v1.0.45

* Fixed: Missing temps if high or crit is None, by @TheComputerGuy96
* Changed: Some refactoring by @dpshelio
* Added: Proper mapping for correct coretemp display and added toggle for coretemp
* Fixed: Cleanup of escaped characters in process argument string

## v1.0.44

* Added: Spread CPUs across columns evenly if possible, by @ErwinJunge
* Added: Additional crash fixes for graph and swap toggles

## v1.0.43

* Fixed: Battery meter not clearing properly when disabled
* Fixed: Correction for broken cpu high and cpu critical temps
* Fixed: get_cpu_name() function for some Xeon cpus
* Fixed: Additional error handling to prevent crashes from graph and swap toggles

## v1.0.42

* Fixed: Battery status not using same sensors as psutil
* Added: Stripping of .local from /host clock format
* Fixed: Battery clear if removed

## v1.0.41

* Skipped due to pypi - github versioning error

## v1.0.40

* Fixed: Title leading whitespace
* Fixed: Battery meter crash on non Linux systems

## v1.0.39

* Fixed: Manual sensor selection screen refresh
* Fixed: Rare swap toggle crash
* Fixed: Clock and battery placement and sizing

## v1.0.38

* Fixed: Cpu sensor check when changing from manual sensor to Auto
* Fixed: Menu collection timeout and menu background update stall
* Added: Custom options for clock formatting: hostname and username

## v1.0.37

* Fixed: Swap toggle rare crash
* Fixed: Cpu sensor option to trigger temp toggle if check temp is true

## v1.0.36

* Added: Rounding for floating_humanizer() short option
* Fixed: Cpu temp not showing when manually selected and not auto detected
* Fixed Crash during theme change

## v1.0.35

* Fixed: Decimal placement in floating_humanizer() function

## v1.0.34

* Changed: Improvement on cpu name detection
* Added: Option to choose cpu temperature sensor
* Fixed: Battery meter adaptation

## v1.0.33

* Changed: Improvement on osx cpu temperature collection with coretemp
* Fixed: Battery stats crash and better battery status detection
* README: coretemp install instructions by @hacker1024
* README: Added notice about font problems and possible solutions

## v1.0.32

* Added: Symbol for battery inactive
* Fixed: Cpu model name exception for certain xeon cpus
* Fixed: Exception when sending signal using uppercase T, K, I
* Fixed: Battery meter placement calculation correction
* Added: Support for OSX cpu core temperatures via coretemp program

## v1.0.31

* Fixed: Battery meter redraw after terminal resize
* Fixed: Battery meter additional fixes
* Fixed: Cpu temp color wrong on small sizes

## v1.0.30

* Changed: Argument parsing using argparse
* Fixed: Hide battery time when not known

## v1.0.29

* Fixed: Battery percent converted to integer and battery time hidden at 100% level

## v1.0.28

* Fixed: Battery meter causing crash when connecting/disconnecting battery
* README: Added more repositories

## v1.0.27

* Added: kyli0x theme by @kyli0x
* Added: Battery meter and stats
* Added: Option to change the tree view auto collapse depth

## v1.0.26

* Fixed: Cpu temp color index crash
* Fixed: Start from virtualenv crash

## v1.0.25

* Added: More sizing adaptation for processes
* Fixed: Clock centering

## v1.0.24

* Fixed: "view_mode" option entry format
* Fixed: Help menu entries

## v1.0.23

* Added: View mode toggle with 3 presets, "full", "proc" and "stat"
* Added: Rescaling of net stat box width on smaller terminal sizes
* Changed: Net box height slight increase, mem/disks box height slight decrease
* Fixed: Some element placement fixes by @RedBearAK
* Fixed: "delete" and "filter" mouse click area misaligned
* Added: Option to sync network scaling between download and upload

## v1.0.22

* Some refactoring and cleanup
* README: Info for debian package
* Added: Theme search path for snap install
* README: Updated snap install info


## v1.0.21

* Fixed: Clean excess whitespace from CPU model name, by @RedBearAK
* Changed: README.md absolute paths to work on PyPi

## v1.0.20

* Release bump to fix pypi and source version mismatch

## v1.0.19

* Changed: net_auto variable now default to True
* Fixed: Sorting out negative cpu temperature values from bad sensors

## v1.0.18

* Fixed: Init screen and error log level when starting from pip installation

## v1.0.17

* Added: Option to toggle theme background color
* Added: Dracula theme by @AethanFoot
* Added: PyPi theme install and path detection
* Added: PyPi packaging with poetry by @cjolowicz
* Added: Error checking for net_download and net_upload config values
* Added: psutil outdated warning message
* Changed: Expanded cpu name detection

## v1.0.16

* Fixed: net_upload variable not working
* Added: Ability to expand/collapse processes in the tree view

## v1.0.15

* Added: Network graph color gradient bandwidth option by @drazil100
* Added: cpu_thermal sensor detection for raspberri pi cpu temp
* Fixed: Single color graphs crash

## v1.0.14

* Added: New theme values "graph_text", "meter_bg", "process_start", "process_mid" and "process_end", see default_black.theme for reference.
* Updated: default_black.theme with new values
* Updated: monokai.theme and gruvbox_dark.theme with "graph_text" value.

## v1.0.13

* Fixed: Cpu usage bug when showing tree and memory in percent
* Fixed: Check for minimum terminal size at start when init screen is enabled

## v1.0.12

* Fixed: Cpu high and cpu crit for osx and raspberry pi

## v1.0.11

* Fixed: getsensors detection of vcgencmd
* Fixed: Load AVG being drawn outside box on small sizes
* Fixed: Slowdown when showing memory in percent instead of bytes
* Fixed: Cpu temperature colors not converted to percent of cpu critical temp
* Fixed: Crash on sorting change when lacking permissions

## v1.0.10

* Fixed: Raspberry pi cpu temps, actually fixed this time...

## v1.0.9

* Fixed: Raspberry pi cpu temp, again.

## v1.0.8

* Added: Set terminal title at start
* Added: Update checker, can be toggled off in options menu
* Added: Option to show memory in bytes for processes, enabled by default
* Added: Options to set custom network graphs minimum scaling values and a "auto" button to toggle manual and default values.
* Fixed: Failure to detect cpu temp on raspberry pi
* Changed: Layout changes to cpu box

## v1.0.7

* Changed: Info box now restores last selection on close
* Fixed: Crash when starting with show_disks=False

## v1.0.6

* Fixed: Cpu temps index error on uneven temp collection
* Fixed: No cpu percent in info box when filtering

## v1.0.5

* Fixed: Attribute typo in detailed process collection

## v1.0.4

* Fixed: Crash when filtering and showing info box
* Added: Improved cpu temperature detection
* Fixed: Broken cpu box layout on high core count and change to default layout
* Changed: Selection now returns to last selection when pressing down from info box

## v1.0.3

* Fixed: Crash on detailed info when showing tree
* Fixed: Incorrect sorting for memory
* FIxed: Removed unsupported osx psutil values
* Changed: Removed shift modifiers for some keys and removed redundant toggles

## v1.0.2

* Added: IndexError catch for cpu temperature collection
* Fixed: net_io_counters() not iterating over itself
* Fixed: Clear mouse queue to avoid accidental character interpretation
* Added: "/etc/bpytop.conf" as default seed for config file creation if it exists.
* Added: Error handling for exception in psutil.cpu_freq()

## v1.0.1

* Fixed: Bad assumption of cpu model name string contents.
* Added: Exception catch for psutil io_counters error caused by psutil < 5.7.0 and Linux kernel >= 5
* Added: Error handling for psutil.net_io_counters() errors.

## v1.0.0

* First release
* Missing update checker
