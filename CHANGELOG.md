# Changelog

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

* Release bump to fix pypi and source version missmatch

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
