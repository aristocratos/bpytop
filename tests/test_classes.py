import bpytop, pytest
from bpytop import Box, SubBox, CpuBox, MemBox, NetBox, ProcBox, Term, Draw
from bpytop import Graph, Fx, Meter, Color, Banner
from bpytop import Collector, CpuCollector, MemCollector, NetCollector, ProcCollector
bpytop.Term.width, bpytop.Term.height = 80, 25

def test_Fx_uncolor():
	assert Fx.uncolor("\x1b[38;2;102;238;142mTEST\x1b[48;2;0;0;0m") == "TEST"

def test_Color():
	assert Color.fg("#00ff00") == "\x1b[38;2;0;255;0m"
	assert Color.bg("#cc00cc") == "\x1b[48;2;204;0;204m"
	assert Color.fg(255, 255, 255) == "\x1b[38;2;255;255;255m"

def test_Theme():
	bpytop.THEME = bpytop.Theme("Default")
	assert str(bpytop.THEME.main_fg) == "\x1b[38;2;204;204;204m"
	assert list(bpytop.THEME.main_fg) == [204, 204, 204]
	assert len(bpytop.THEME.gradient["cpu"]) == 101

def test_Box_calc_sizes():
	Box.calc_sizes()
	assert CpuBox.width == MemBox.width + ProcBox.width == NetBox.width + ProcBox.width == 80
	assert CpuBox.height + ProcBox.height == CpuBox.height + MemBox.height + NetBox.height == 25

def test_Graph():
	test_graph = Graph(width=20, height=10, color=None, data=[x for x in range(20)], invert=False, max_value=0, offset=0, color_max_value=None)
	assert len(str(test_graph)) > 1
	assert str(test_graph).endswith("⣀⣤⣴⣾⣿⣿⣿⣿⣿")
	assert test_graph(5).endswith("⣧")

def test_Meter():
	test_meter = Meter(value=100, width=20, gradient_name="cpu", invert=False)
	assert Fx.uncolor(str(test_meter)) == "■■■■■■■■■■■■■■■■■■■■"

def test_Banner():
	assert len(Banner.draw(line=1, col=1, center=False, now=False)) == 2477

def test_CpuCollector_collect():
	bpytop.CONFIG.check_temp = False
	CpuCollector._collect()
	assert len(CpuCollector.cpu_usage) == bpytop.THREADS + 1
	assert isinstance(CpuCollector.cpu_usage[0][0], int)
	assert isinstance(CpuCollector.load_avg, list)
	assert isinstance(CpuCollector.uptime, str)

def test_CpuCollector_get_sensors():
	bpytop.CONFIG.check_temp = True
	bpytop.CONFIG.cpu_sensor = "Auto"
	CpuCollector.get_sensors()
	if CpuCollector.got_sensors:
		assert CpuCollector.sensor_method != ""
	else:
		assert CpuCollector.sensor_method == ""

def test_CpuCollector_collect_temps():
	if not CpuCollector.got_sensors:
		pytest.skip("Not testing temperature collection if no sensors was detected!")
	CpuCollector._collect_temps()
	assert len(CpuCollector.cpu_temp) == bpytop.THREADS + 1
	for temp_instance in CpuCollector.cpu_temp:
		assert temp_instance
		assert isinstance(temp_instance[0], int)
	assert isinstance(CpuCollector.cpu_temp_high, int)
	assert isinstance(CpuCollector.cpu_temp_crit, int)

def test_MemCollector_collect():
	MemBox.width = 20
	bpytop.CONFIG.show_swap = True
	bpytop.CONFIG.show_disks = True
	bpytop.CONFIG.disks_filter = ""
	bpytop.CONFIG.swap_disk = True
	MemCollector._collect()
	assert isinstance(MemCollector.string["total"], str) and MemCollector.string["total"] != ""
	assert isinstance(MemCollector.values["used"], int)
	assert isinstance(MemCollector.percent["free"], int)
	if MemBox.swap_on:
		assert len(MemCollector.disks) > 1
		assert "__swap" in MemCollector.disks
	else:
		assert len(MemCollector.disks) > 0

def test_NetCollector_get_nics():
	NetCollector._get_nics()
	if NetCollector.nic == "":
		pytest.skip("No nic found, skipping tests!")
	assert NetCollector.nic in NetCollector.nics

def test_NetCollector_collect():
	if NetCollector.nic == "":
		pytest.skip("No nic found, skipping tests!")
	NetBox.width = 20
	NetCollector._collect()
	assert isinstance(NetCollector.strings[NetCollector.nic]["download"]["total"], str)
	assert isinstance(NetCollector.stats[NetCollector.nic]["upload"]["total"], int)

def test_ProcCollector_collect():
	bpytop.CONFIG.proc_tree = False
	bpytop.CONFIG.proc_mem_bytes = True
	bpytop.Box.boxes = ["proc"]
	ProcCollector._collect()
	assert len(ProcCollector.processes) > 0
	bpytop.CONFIG.proc_tree = True
	ProcCollector.processes = {}
	ProcCollector._collect()
	assert len(ProcCollector.processes) > 0

def test_CpuBox_draw():
	Box.calc_sizes()
	assert len(CpuBox._draw_bg()) > 1
	CpuBox._draw_fg()
	assert "cpu" in Draw.strings

def test_MemBox_draw():
	bpytop.CONFIG.show_disks = True
	Box.calc_sizes()
	assert len(MemBox._draw_bg()) > 1
	MemBox._draw_fg()
	assert "mem" in Draw.strings

def test_NetBox_draw():
	Box.calc_sizes()
	assert len(NetBox._draw_bg()) > 1
	NetBox._draw_fg()
	assert "net" in Draw.strings

def test_ProcBox_draw():
	Box.calc_sizes()
	assert len(ProcBox._draw_bg()) > 1
	ProcBox._draw_fg()
	assert "proc" in Draw.strings
