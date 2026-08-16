-- MM7 install-sanity pass: loads FNT_DBCS.lua with MMVersion=7 and checks
-- that every hook/patch lands on the MM7 addresses (logic itself is covered by
-- the functional MM8 pass in harness.lua)
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
offsets = {MMVersion = 7}
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

check("mm7: hookfunctions at MM7 addresses",
	HF[0x44C54A] ~= nil and HF[0x44C794] ~= nil and HF[0x44C95F] ~= nil
	and HF[0x44CE34] ~= nil and HF[0x44CB7B] ~= nil)
check("mm7: hf stack arg counts",
	HF[0x44C794].nstack == 3 and HF[0x44C95F].nstack == 4
	and HF[0x44CE34].nstack == 7 and HF[0x44CB7B].nstack == 6 and HF[0x44C54A].nstack == 0)
check("mm7: asmpatch count 10 (3L + 5 loops + A2 + A)", #PATCHES == 10, #PATCHES)
check("mm7: asmhook count 1 (L4 at 0x44CEC4)", #ASMHOOKS == 1 and ASMHOOKS[1].p == 0x44CEC4,
	ASMHOOKS[1] and string.format("%X", ASMHOOKS[1].p))

local patched = {}
for _, p in ipairs(PATCHES) do
	patched[p.p] = p
end
for _, a in ipairs({0x44C5F6, 0x44C686, 0x44C719, 0x44CF36, 0x44CC1D, 0x44CCDD, 0x44D15E, 0x44D280, 0x44CEF7, 0x44C50A}) do
	check(string.format("mm7: patch present at %X", a), patched[a] ~= nil)
end
check("mm7: L anchors are push eax", patched[0x44C5F6].code == "push eax"
	and patched[0x44C686].code == "push eax" and patched[0x44C719].code == "push eax")
check("mm7: D patch compares al and jumps to 0x44D0CA-stub",
	patched[0x44CF36].code:find("cmp al, 161", 1, true) ~= nil
	and patched[0x44CF36].size == 7)
check("mm7: A2 accepts lead bytes toward 0x44CF14",
	patched[0x44CEF7].code:find("jae absolute " .. 0x44CF14, 1, true) ~= nil)
check("mm7: A jmp to proc", patched[0x44C50A].code:find("jmp absolute", 1, true) ~= nil
	and patched[0x44C50A].size == 9)
check("mm7: TestChar proc targets MM7 valid/invalid",
	ASMPROCS[#ASMPROCS].code:find(tostring(0x44C52A), 1, true) ~= nil
	and ASMPROCS[#ASMPROCS].code:find(tostring(0x44C513), 1, true) ~= nil)
check("mm7: 5 loop hooks", (function()
	local n = 0
	for _ in pairs(HOOKS) do n = n + 1 end
	return n == 5
end)())

print(string.format("== %d passed, %d failed ==", pass, fail))
if fail > 0 then
	os.exit(1)
end
