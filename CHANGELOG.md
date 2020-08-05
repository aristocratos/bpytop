# Changelog

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
