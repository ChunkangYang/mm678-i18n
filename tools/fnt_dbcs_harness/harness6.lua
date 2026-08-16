-- MM6 install-sanity pass: loads FNT_DBCS.lua with MMVersion=6 and checks
-- that hooks/patches land on the MM6 addresses (no TestChar patch, no
-- WordWrap2, 4 loops, MM6 argument counts)
unpack = unpack or table.unpack

CALLS, HOOKS, HF, PATCHES, ASMPROCS, ASMHOOKS = {}, {}, {}, {}, {}, {}
local MEM = {}
local function wr(a, n, v)
	v = v % (2 ^ (8 * n))
	for k = 0, n - 1 do
		MEM[a + k] = v % 256
		v = math.floor(v / 256)
	end
end
mem = {
	u1 = setmetatable({}, {__index = function(_, a) return MEM[a] or 0 end,
		__newindex = function(_, a, v) wr(a, 1, v) end}),
	u2 = setmetatable({}, {__index = function(_, a) return 0 end, __newindex = function() end}),
	i4 = setmetatable({}, {__index = function(_, a) return 0 end, __newindex = function() end}),
	string = function(p) return "" end,
	copy = function() end,
	call = function() return 0 end,
	hook = function(p, f) HOOKS[p] = f end,
	asmproc = function(code)
		local p = 0x10000000 + #ASMPROCS * 0x100
		ASMPROCS[#ASMPROCS + 1] = {p = p, code = code}
		return p
	end,
	asmpatch = function(p, code, size) PATCHES[#PATCHES + 1] = {p = p, code = code, size = size} end,
	asmhook = function(p, code) ASMHOOKS[#ASMHOOKS + 1] = {p = p, code = code} end,
	hookfunction = function(p, nreg, nstack, f) HF[p] = {nreg = nreg, nstack = nstack, f = f} end,
	StaticAlloc = function(n) return 0x20000000 end,
}
Game = setmetatable({}, {__index = function() return nil end})
events = setmetatable({}, {__newindex = function(t, k, v) rawset(t, "_" .. k, v) end})
Message = function() end
offsets = {MMVersion = 6}
Party = {}

dofile(SCRIPT_UNDER_TEST)

local pass, fail = 0, 0
local function check(name, cond, extra)
	if cond then
		pass = pass + 1
		print("PASS " .. name)
	else
		fail = fail + 1
		print("FAIL " .. name .. (extra and ("  -> " .. tostring(extra)) or ""))
	end
end

check("mm6: hookfunctions at MM6 addresses",
	HF[0x442DD0] ~= nil and HF[0x442F50] ~= nil and HF[0x4435F0] ~= nil and HF[0x443210] ~= nil)
check("mm6: no WordWrap2 hook", HF[0x44C95F] == nil and HF[0x44A058] == nil)
check("mm6: hf stack arg counts (wrap 2, draw 4, ltd 6, width 0)",
	HF[0x442F50].nstack == 2 and HF[0x4435F0].nstack == 4
	and HF[0x443210].nstack == 6 and HF[0x442DD0].nstack == 0)
check("mm6: asmpatch count 5 (L1 + 4 loops, no A)", #PATCHES == 5, #PATCHES)
check("mm6: asmhook count 1 (L4 at 0x44368D)", #ASMHOOKS == 1 and ASMHOOKS[1].p == 0x44368D,
	ASMHOOKS[1] and string.format("%X", ASMHOOKS[1].p))
check("mm6: L4 uses inline scasb", ASMHOOKS[1].code:find("scasb", 1, true) ~= nil)

local patched = {}
for _, p in ipairs(PATCHES) do
	patched[p.p] = p
end
for _, a in ipairs({0x442EC0, 0x4436D6, 0x44330B, 0x4433ED, 0x44393B}) do
	check(string.format("mm6: patch present at %X", a), patched[a] ~= nil)
end
check("mm6: L1 redirects strlen to wrap result",
	patched[0x442EC0].code:find("mov edi, eax", 1, true) ~= nil and patched[0x442EC0].size == 5)
check("mm6: D diverts on al before inline test",
	patched[0x4436D6].code:find("cmp al, 161", 1, true) ~= nil and patched[0x4436D6].size == 7)
check("mm6: no TestChar patch", patched[0x443053] == nil and patched[0x44C50A] == nil and patched[0x449C3B] == nil)
check("mm6: 4 loop hooks", (function()
	local n = 0
	for _ in pairs(HOOKS) do n = n + 1 end
	return n == 4
end)())

print(string.format("== %d passed, %d failed ==", pass, fail))
if fail > 0 then
	os.exit(1)
end
