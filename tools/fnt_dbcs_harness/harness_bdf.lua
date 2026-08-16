-- BDF font mode functional pass: cwd is bdftest/ whose LocalizeConf.ini maps
-- dbcsFont_Default to a synthetic 2-glyph BDF; drives the width path and the
-- MM8 D draw handler and checks the converted glyph (255 body / 1 shadow).
unpack = unpack or table.unpack

CALLS, HOOKS, HF, PATCHES, ASMPROCS, ASMHOOKS = {}, {}, {}, {}, {}, {}
local MEM = {}
local function rd(a, n)
	local v = 0
	for k = n - 1, 0, -1 do
		v = v * 256 + (MEM[a + k] or 0)
	end
	return v
end
local function wr(a, n, v)
	v = v % (2 ^ (8 * n))
	for k = 0, n - 1 do
		MEM[a + k] = v % 256
		v = math.floor(v / 256)
	end
end
local NEXTALLOC = 0x20000000
mem = {
	u1 = setmetatable({}, {__index = function(_, a) return MEM[a] or 0 end,
		__newindex = function(_, a, v) wr(a, 1, v) end}),
	u2 = setmetatable({}, {__index = function(_, a) return rd(a, 2) end,
		__newindex = function(_, a, v) wr(a, 2, v) end}),
	i4 = setmetatable({}, {__index = function(_, a)
			local v = rd(a, 4)
			if v >= 2 ^ 31 then v = v - 2 ^ 32 end
			return v
		end,
		__newindex = function(_, a, v) wr(a, 4, v) end}),
	string = function(p)
		local out, a = {}, p
		while (MEM[a] or 0) ~= 0 do
			out[#out + 1] = string.char(MEM[a])
			a = a + 1
		end
		return table.concat(out)
	end,
	copy = function(dest, s, n)
		if type(s) == "string" then
			for k = 1, #s do
				MEM[dest + k - 1] = s:byte(k)
			end
		else -- pointer copy (used by the per-font line-spacing repad)
			for k = 0, (n or 0) - 1 do
				MEM[dest + k] = MEM[s + k] or 0
			end
		end
	end,
	call = function(...)
		CALLS[#CALLS + 1] = {...}
		return 0
	end,
	hook = function(p, f) HOOKS[p] = f end,
	asmproc = function(code)
		local p = 0x10000000 + #ASMPROCS * 0x100
		ASMPROCS[#ASMPROCS + 1] = {p = p, code = code}
		return p
	end,
	asmpatch = function(p, code, size) PATCHES[#PATCHES + 1] = {p = p, code = code, size = size} end,
	asmhook = function(p, code) ASMHOOKS[#ASMHOOKS + 1] = {p = p, code = code} end,
	hookfunction = function(p, nreg, nstack, f) HF[p] = {nreg = nreg, nstack = nstack, f = f} end,
	StaticAlloc = function(n)
		local p = NEXTALLOC
		NEXTALLOC = NEXTALLOC + n + 16
		return p
	end,
}

local NEXTF = 0x01000000
local function makeFont(minC, maxC, h)
	local f = NEXTF
	NEXTF = NEXTF + 0x40000
	wr(f, 1, minC); wr(f + 1, 1, maxC); wr(f + 5, 1, h)
	wr(f + 0xC, 4, 0xAB0000 + h)
	for c = 0, 255 do
		wr(f + 0x20 + 12 * c, 4, 0)
		wr(f + 0x24 + 12 * c, 4, 6)
		wr(f + 0x28 + 12 * c, 4, 1)
		-- glyph offsets (style/padding detection reads these); spaced so the
		-- per-char glyph areas don't overlap and stay independently fillable
		wr(f + 0xC20 + 4 * c, 4, 0x2000 + c * 0x100)
	end
	return f
end
-- give a fake host font real glyph pixels so style auto-detection has
-- something to sample (val 1 = black-style host, 255 = plain-style host);
-- fillH < font height leaves blank bottom rows = the host's bottom padding
local function fillGlyphs(f, fillH, val)
	for c = 0x41, 0x48 do
		local g = f + 0x2000 + c * 0x100 + 0x1020
		for i = 0, 6 * fillH - 1 do
			wr(g + i, 1, val)
		end
	end
end

FONT16 = makeFont(0x20, 0xFF, 16) -- no glyph data: detection falls back to shadow
FONT13 = makeFont(0x20, 0xFF, 13) -- Autonote host, black-style glyphs (auto-detect)
fillGlyphs(FONT13, 13, 1)
FONT14 = makeFont(0x20, 0xFF, 14) -- unnamed: Default list must size-pick test13
FONT15 = makeFont(0x20, 0xFF, 15) -- Lucida host, plain-style glyphs (auto-detect)
fillGlyphs(FONT15, 15, 255)
FONT17 = makeFont(0x20, 0xFF, 17) -- Smallnum host, black-style glyphs but the
fillGlyphs(FONT17, 15, 1)         -- mapping forces ",shadow" (override test);
                                  -- ink stops 2 rows early -> auto bottom gap 2

Game = setmetatable({}, {__index = function(_, k)
	if k == "LoadDataFileFromLod" or k == "CanLoadFileFromLod" then
		error("page font path must not be used in BDF mode: " .. tostring(k))
	end
	if k == "Autonote_fnt" then
		return FONT13
	end
	if k == "Lucida_fnt" then
		return FONT15
	end
	if k == "Smallnum_fnt" then
		return FONT17
	end
	return nil
end})
events = setmetatable({}, {__newindex = function(t, k, v) rawset(t, "_" .. k, v) end})
Message = function() end
offsets = {MMVersion = 8}
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

local NEXTS = 0x03000000
local function putStr(s)
	local p = NEXTS
	NEXTS = NEXTS + 0x1000
	mem.copy(p, s .. "\0")
	return p
end

local NI, HAO = "\196\227", "\186\195"
local function def()
	return 4242
end

-- width path: two 16px BDF glyphs, a=0 c=0
local r = HF[0x449C7B].f(nil, def, FONT16, putStr(NI .. HAO))
check("bdf: width of 2 glyphs = 32", r == 32, r)

-- D draw handler blits a converted glyph
local dproc = ASMPROCS[1].p
local EBP = 0x02000000
local sptr = putStr(NI .. HAO)
mem.i4[EBP - 4] = sptr
mem.i4[EBP + 0x14] = 0
mem.i4[EBP - 0xC] = 4
mem.u2[EBP + 0x10] = 0x1234
mem.u2[EBP + 0x20] = 7
mem.i4[EBP + 0x18] = 0
CALLS = {}
local d = {cl = 0xC4, ebx = FONT16, esi = 100, edi = 50, ebp = EBP}
HOOKS[dproc](d)
local c = CALLS[#CALLS]
check("bdf: shadow blit called", c ~= nil and c[1] == 0x4A4E9F, c and c[1])
check("bdf: glyph w,h = 16,15 (ink band 2-16 auto-cropped)", c and c[7] == 16 and c[8] == 15,
	c and (tostring(c[7]) .. "x" .. tostring(c[8])))
check("bdf: pen advanced by 16", d.esi == 116, d.esi)
check("bdf: pair consumed", mem.i4[EBP + 0x14] == 1)

local glyph = c and c[6]
local n255, n1, toprow = 0, 0, 0
if glyph then
	for i = 0, 16 * 15 - 1 do
		local v = mem.u1[glyph + i]
		if v == 255 then n255 = n255 + 1 end
		if v == 1 then n1 = n1 + 1 end
		if i < 16 and v ~= 0 then toprow = toprow + 1 end
	end
end
check("bdf: body pixels (255) present", n255 > 20, n255)
check("bdf: shadow pixels (1) synthesized", n1 > 10, n1)
check("crop: first emitted row carries ink (blank rows cropped)", toprow > 0, toprow)

-- second glyph comes from the cache (same address on repeat)
CALLS = {}
mem.i4[EBP + 0x14] = 0
d = {cl = 0xC4, ebx = FONT16, esi = 0, edi = 0, ebp = EBP}
HOOKS[dproc](d)
check("bdf: cached glyph pointer reused", CALLS[#CALLS] and CALLS[#CALLS][6] == glyph)

-- unmapped char (gb2312 pair with no glyph in the 2-glyph font) -> tofu advance
mem.copy(sptr, "\214\208\0") -- zhong1, not in test16.bdf
mem.i4[EBP + 0x14] = 0
mem.i4[EBP - 0xC] = 2
CALLS = {}
d = {cl = 0xD6, ebx = FONT16, esi = 0, edi = 0, ebp = EBP}
HOOKS[dproc](d)
check("bdf: missing glyph = no blit, tofu advance", #CALLS == 0 and d.esi == 16, d.esi)

-- named mapping with black style: FONT13 is Autonote -> test13.bdf,black
r = HF[0x449C7B].f(nil, def, FONT13, putStr(NI))
check("bdf: named 13px font width = 13", r == 13, r)
mem.copy(sptr, NI .. "\0")
mem.i4[EBP + 0x14] = 0
mem.i4[EBP - 0xC] = 2
CALLS = {}
d = {cl = 0xC4, ebx = FONT13, esi = 0, edi = 0, ebp = EBP}
HOOKS[dproc](d)
c = CALLS[#CALLS]
check("bdf: black glyph 13x12 (ink band 1-12)", c and c[7] == 13 and c[8] == 12,
	c and (tostring(c[7]) .. "x" .. tostring(c[8])))
check("gap: black 13px sits at y=1 (13-0-12)", c and c[5] == 1, c and c[5])
local b255, b1 = 0, 0
if c then
	for i = 0, 13 * 12 - 1 do
		local v = mem.u1[c[6] + i]
		if v == 255 then b255 = b255 + 1 end
		if v == 1 then b1 = b1 + 1 end
	end
end
check("bdf: black style = body value 1, no 255, no shadow", b255 == 0 and b1 > 15,
	b255 .. "/" .. b1)

-- unnamed 14px font: Default list picks the 13px BDF (largest that fits);
-- shadow style adds one row under the 12-row band -> drawn height 13
mem.i4[EBP + 0x14] = 0
CALLS = {}
d = {cl = 0xC4, ebx = FONT14, esi = 0, edi = 0, ebp = EBP}
HOOKS[dproc](d)
c = CALLS[#CALLS]
check("bdf: 14px font size-picks the 13px BDF (band 12 + shadow row)", c and c[8] == 13, c and c[8])
check("gap: bottom-anchored at y=1 (14-0-13)", c and c[5] == 1, c and c[5])

-- per-font line spacing flag: Lucida (15px host) maps test16.bdf,2 -> the
-- host font is heightened 15->17 with its glyphs relocated+padded; the CJK
-- glyph stays baseline-anchored: baseline 14, gap 1, y = 17-1-14 = 2
mem.i4[EBP + 0x14] = 0
CALLS = {}
d = {cl = 0xC4, ebx = FONT15, esi = 0, edi = 0, ebp = EBP}
HOOKS[dproc](d)
c = CALLS[#CALLS]
check("pad: host font heightened 15 -> 17", mem.u1[FONT15 + 5] == 17, mem.u1[FONT15 + 5])
local goff = mem.i4[FONT15 + 0xC20 + 4 * 0x41]
local gptr = FONT15 + goff + 0x1020
check("pad: glyph relocated, data kept + 2 blank rows", goff ~= 0x2000 + 0x41 * 0x100
	and mem.u1[gptr] == 255 and mem.u1[gptr + 6 * 15] == 0
	and mem.u1[gptr + 6 * 17 - 1] == 0, goff)
check("gap: drawn height = ink band 14", c and c[8] == 14, c and c[8])
check("pad: CJK stays baseline-anchored (y=2: 17-1-14)", c and c[5] == 2, c and c[5])
check("gap: width unchanged (DWIDTH 16)", c and c[7] == 16, c and c[7])
local a255 = 0
if c then
	for i = 0, 16 * 14 - 1 do
		if mem.u1[c[6] + i] == 255 then a255 = a255 + 1 end
	end
end
check("crop: glyph body survives the band crop", a255 > 20, a255)
check("gap: pen advance still DWIDTH", d.esi == 16, d.esi)
local a1 = 0
if c then
	for i = 0, 16 * 14 - 1 do
		if mem.u1[c[6] + i] == 1 then a1 = a1 + 1 end
	end
end
check("detect: plain host -> no shadow pixels", a1 == 0, a1)

-- explicit ",shadow" flag beats the black host detection (Smallnum/FONT17);
-- FONT17's own ink stops 2 rows early -> auto bottom gap 2 -> y = 17-2-15
mem.i4[EBP + 0x14] = 0
CALLS = {}
d = {cl = 0xC4, ebx = FONT17, esi = 0, edi = 0, ebp = EBP}
HOOKS[dproc](d)
c = CALLS[#CALLS]
local s255, s1 = 0, 0
if c then
	for i = 0, 16 * 15 - 1 do
		local v = mem.u1[c[6] + i]
		if v == 255 then s255 = s255 + 1 end
		if v == 1 then s1 = s1 + 1 end
	end
end
check("override: ,shadow beats black detection", s255 > 20 and s1 > 10,
	s255 .. "/" .. s1)
check("gap: auto = baseline+1 (y=1: 17-1-15)", c and c[5] == 1, c and c[5])

-- bad metrics: a glyph descending deeper than the declared baseline allows
-- (BBX by -4, base 14, 16-canvas -> bottom overflow) must be shifted up to
-- fit instead of getting its bottom rows clipped (zhenggedianhei-class bug)
local rec = DBCS.getCJK(FONT17, 0xC1, 0xCB) -- gb2312 C1CB -> U+4E86
local bot = 0
if rec then
	for cc = 0, rec.w - 1 do
		if mem.u1[rec.glyph + (rec.h - 1) * rec.w + cc] ~= 0 then
			bot = bot + 1
		end
	end
end
check("fit: overflowing glyph keeps its bottom row", rec ~= nil and bot > 0,
	rec and bot or "nil")

print(string.format("== %d passed, %d failed ==", pass, fail))
if fail > 0 then
	os.exit(1)
end
