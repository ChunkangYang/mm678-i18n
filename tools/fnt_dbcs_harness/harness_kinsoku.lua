-- pass 5: kinsoku tables for big5 / shift_jis (run.py sets the ENCODING
-- global and chdirs into kinsokutest/<enc>/ so the matching ini is read).
-- Minimal clone of harness.lua's fake environment driving only WordWrap.
unpack = unpack or table.unpack

-- ===== fake flat memory =====
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

local HF = {}

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
	copy = function(dest, s)
		for k = 1, #s do
			MEM[dest + k - 1] = s:byte(k)
		end
	end,
	call = function() return 0 end,
	hook = function() end,
	asmproc = function()
		NEXTPROC = (NEXTPROC or 0x10000000) + 0x100
		return NEXTPROC
	end,
	asmpatch = function(p, code)
		local n = code:match("^db (%d+)$")
		if n then
			wr(p, 1, tonumber(n)) -- apply single-byte pokes (lineSpacing test)
		end
	end,
	asmhook = function() end,
	hookfunction = function(p, nreg, nstack, f)
		HF[p] = {nreg = nreg, nstack = nstack, f = f}
	end,
	StaticAlloc = function(n)
		NEXTALLOC = (NEXTALLOC or 0x20000000) + 0x1000
		return NEXTALLOC
	end,
}

-- ===== fake fonts =====
local NEXTF = 0x01000000
local function makeFont(minC, maxC, h, defW, spaceW, sb, sa)
	local f = NEXTF
	NEXTF = NEXTF + 0x20000
	wr(f, 1, minC); wr(f + 1, 1, maxC); wr(f + 5, 1, h)
	wr(f + 0xC, 4, 0xAB0000 + h)
	for c = 0, 255 do
		local base = f + 0x20 + 12 * c
		wr(base, 4, sb)
		wr(base + 4, 4, (c == 32) and spaceW or defW)
		wr(base + 8, 4, sa)
		wr(f + 0xC20 + 4 * c, 4, 0x1000 + c * 4)
	end
	return f
end

local FONT16 = makeFont(0x20, 0xFF, 16, 6, 4, 0, 1)

local pagesMade = {}
Game = setmetatable({}, {__index = function(_, k)
	if k == "LoadDataFileFromLod" then
		return function(name)
			if pagesMade[name] then
				return pagesMade[name]
			end
			local tag, hi = name:match("^DBCS_(%w+)_(%x+)%.fnt$")
			assert(tag, "unexpected lod load: " .. tostring(name))
			local h = tonumber(tag:match("%d+"))
			local f = makeFont(0, 255, h, h, h, 0, 0)
			pagesMade[name] = f
			return f
		end
	elseif k == "CanLoadFileFromLod" then
		return function() return true end
	elseif k:match("_fnt$") then
		return 0
	end
	return nil
end})

events = setmetatable({}, {__newindex = function(t, k, v)
	local list = rawget(t, "_" .. k) or {}
	list[#list + 1] = v
	rawset(t, "_" .. k, list)
end})
Message = function(s) LASTMSG = s end
offsets = {MMVersion = 8}
Party = {}

-- seed the MM8 "fontHeight-3" immediates so the big5 pass (its ini sets
-- lineSpacing=2) can verify the S line-spacing pokes
local LINELEA = {0x449D8B, 0x449E20, 0x449EAB, 0x44A4C3, 0x44A4CA, 0x44A737, 0x44A754}
local LINESUB = {0x449D20, 0x449DAC, 0x44AAC2}
for _, a in ipairs(LINELEA) do
	wr(a, 1, 0xFD)
end
for _, a in ipairs(LINESUB) do
	wr(a, 1, 0x03)
end

-- ===== load the real file =====
dofile(SCRIPT_UNDER_TEST)

-- ===== test framework =====
local pass, fail = 0, 0
local function check(name, cond, extra)
	name = ENCODING .. " " .. name
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

local DLG = 0x04000000
local WRAPBUF = 0x5DC8E0
local WordWrap = 0x449ECA

local function def() return 4242 end

local function wrap(s, W)
	wr(DLG + 8, 4, W)
	local p = HF[WordWrap].f(nil, def, putStr(s), FONT16, DLG, 0, 0)
	return mem.string(p)
end

-- test characters per encoding (all verified against the python codecs):
--   big5:      你=A741 好=A66E ，=A141 (noStart) 《=A16D (noEnd)
--   shift_jis: あ=82A0 い=82A2 、=8141 (noStart) 「=8175 (noEnd) っ=82C1 (small kana, noStart)
local T = {
	big5      = {NI = "\167\65",  HAO = "\166\110", COMMA = "\161\65", LQUO = "\161\109"},
	shift_jis = {NI = "\130\160", HAO = "\130\162", COMMA = "\129\65", LQUO = "\129\117",
	             SMALL = "\130\193"},
}
local t = assert(T[ENCODING], "unknown ENCODING: " .. tostring(ENCODING))
local NI, HAO, COMMA, LQUO = t.NI, t.HAO, t.COMMA, t.LQUO

check("install: WordWrap hooked (encoding activated)", HF[WordWrap] ~= nil)

local out = wrap(NI .. HAO .. NI .. HAO .. NI .. HAO .. NI .. HAO .. NI .. HAO, 50)
check("wrap lines of 3+3+3+1 on pair boundary",
	out == NI .. HAO .. NI .. "\n" .. HAO .. NI .. HAO .. "\n" .. NI .. HAO .. NI .. "\n" .. HAO,
	(out:gsub("[^\10]", "x")))

out = wrap(NI .. HAO .. NI .. COMMA .. HAO .. HAO, 50)
check("kinsoku: noStart punctuation hangs at line end",
	out:match("^" .. NI .. HAO .. NI .. COMMA .. "\n") ~= nil, out:gsub("\n", "|"))

out = wrap(NI .. HAO .. NI .. LQUO .. HAO .. HAO, 50)
check("kinsoku: noEnd open bracket pushed to next line",
	out:match("\n" .. LQUO) ~= nil, out:gsub("\n", "|"))

if t.SMALL then
	out = wrap(NI .. HAO .. NI .. t.SMALL .. HAO .. HAO, 50)
	check("kinsoku: small kana hangs at line end",
		out:match("^" .. NI .. HAO .. NI .. t.SMALL .. "\n") ~= nil, out:gsub("\n", "|"))
end

if ENCODING == "big5" then -- this pass's ini sets lineSpacing=2
	local leaOk, subOk = true, true
	for _, a in ipairs(LINELEA) do
		if MEM[a] ~= 0xFF then -- 0xFD + 2
			leaOk = false
		end
	end
	for _, a in ipairs(LINESUB) do
		if MEM[a] ~= 0x01 then -- 3 - 2
			subOk = false
		end
	end
	check("lineSpacing: all -3 immediates patched to -1", leaOk and subOk,
		(leaOk and "lea ok" or "lea BAD") .. "/" .. (subOk and "sub ok" or "sub BAD"))
end

print(string.format("== %d passed, %d failed ==", pass, fail))
if fail > 0 then os.exit(1) end
