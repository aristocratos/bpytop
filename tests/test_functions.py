from more_itertools import divide

import bpytop
from bpytop import (CORES, SYSTEM, THREADS, Fx, create_box, floating_humanizer,
                    get_cpu_core_mapping, get_cpu_name, units_to_bytes)


def test_get_cpu_name():
	assert isinstance(get_cpu_name(), str)

def test_get_cpu_core_mapping():
	cpu_core_mapping = get_cpu_core_mapping()
	assert isinstance(cpu_core_mapping, list)
	# Assert cpu submappings are sequential
	for submapping in divide(THREADS//CORES, cpu_core_mapping):
		submapping = list(submapping)
		for a, b in zip(submapping[:-1], submapping[1:]):
			assert b - a == 1

def test_create_box():
	assert len(create_box(x=1, y=1, width=10, height=10, title="", title2="", line_color=None, title_color=None, fill=True, box=None)) > 1

def test_floating_humanizer():
	assert floating_humanizer(100) == "100 Byte"
	assert floating_humanizer(100<<10) == "100 KiB"
	assert floating_humanizer(100<<20, bit=True) == "800 Mib"
	assert floating_humanizer(100<<20, start=1) == "100 GiB"
	assert floating_humanizer(100<<40, short=True) == "100T"
	assert floating_humanizer(100<<50, per_second=True) == "100 PiB/s"

def test_units_to_bytes():
	assert units_to_bytes("10kbits") == 1280
	assert units_to_bytes("100Mbytes") == 104857600
	assert units_to_bytes("1gbit") == 134217728
