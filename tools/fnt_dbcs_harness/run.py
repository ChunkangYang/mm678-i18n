# Offline test harness for FNT_DBCS.lua (the native DBCS renderer).
# Fakes mem/Game/events and font structures, loads the real script, and drives
# its hook functions directly. Requires: pip install lupa
#
#   python tools/fnt_dbcs_harness/run.py
import os

import lupa

here = os.path.dirname(os.path.abspath(__file__))
target = os.path.abspath(os.path.join(
	here, '..', '..', 'assets', 'scripts_datatables', '_common', '_all',
	'Scripts', 'General', 'FNT_DBCS.lua'))
os.chdir(here)  # harness reads Data/LocalizeConf.ini relative to cwd

# pass 1: functional tests against the MM8 engine table
lua = lupa.LuaRuntime()
lua.globals().SCRIPT_UNDER_TEST = target
with open(os.path.join(here, 'harness.lua'), 'rb') as f:
	lua.execute(f.read().decode('latin-1'))

# pass 2: install sanity against the MM7 engine table
lua7 = lupa.LuaRuntime()
lua7.globals().SCRIPT_UNDER_TEST = target
with open(os.path.join(here, 'harness7.lua'), 'rb') as f:
	lua7.execute(f.read().decode('latin-1'))

# pass 3: install sanity against the MM6 engine table
lua6 = lupa.LuaRuntime()
lua6.globals().SCRIPT_UNDER_TEST = target
with open(os.path.join(here, 'harness6.lua'), 'rb') as f:
	lua6.execute(f.read().decode('latin-1'))

# pass 4: BDF font mode (bdftest/ has its own LocalizeConf.ini + DBCSFonts)
import shutil
bdftest = os.path.join(here, 'bdftest')
shutil.copy(
	os.path.join(here, '..', '..', 'assets', 'font', 'gb2312.tbl'),
	os.path.join(bdftest, 'Data', 'DBCSFonts', 'gb2312.tbl'))
os.chdir(bdftest)
luab = lupa.LuaRuntime()
luab.globals().SCRIPT_UNDER_TEST = target
with open(os.path.join(here, 'harness_bdf.lua'), 'rb') as f:
	luab.execute(f.read().decode('latin-1'))
os.chdir(here)

# pass 5: kinsoku tables of the other DBCS encodings (big5, shift_jis)
for enc in ('big5', 'shift_jis'):
	os.chdir(os.path.join(here, 'kinsokutest', enc))
	luak = lupa.LuaRuntime()
	luak.globals().SCRIPT_UNDER_TEST = target
	luak.globals().ENCODING = enc
	with open(os.path.join(here, 'harness_kinsoku.lua'), 'rb') as f:
		luak.execute(f.read().decode('latin-1'))
	os.chdir(here)
