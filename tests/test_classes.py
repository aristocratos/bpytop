import bpytop
from bpytop import Box, SubBox, CpuBox, MemBox, NetBox, ProcBox, Term
from bpytop import Graph, Fx, Meter, Color, Banner

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
	Term.width, Term.height = 80, 25
	Box.calc_sizes()
	assert CpuBox.width == MemBox.width + ProcBox.width == NetBox.width + ProcBox.width == 80
	assert CpuBox.height + ProcBox.height == CpuBox.height + MemBox.height + NetBox.height == 25

def test_Graph():
	test_graph = Graph(width=20, height=10, color=None, data=[x for x in range(20)], invert=False, max_value=0, offset=0, color_max_value=None)
	assert len(str(test_graph)) == 281
	assert str(test_graph).endswith("⣀⣤⣴⣾⣿⣿⣿⣿⣿")
	assert test_graph(5).endswith("⣧")

def test_Meter():
	test_meter = Meter(value=100, width=20, gradient_name="cpu", invert=False)
	assert Fx.uncolor(str(test_meter)) == "■■■■■■■■■■■■■■■■■■■■"

def test_Banner():
	assert len(Banner.draw(line=1, col=1, center=False, now=False)) == 2477
