-- This script makes Might and Magic 6/7/8's program name localizable.
-- It reads program_name from the [Settings] section of Data/LocalizeConf.ini.
-- program_name is stored in UTF-8. For the engine's ANSI name buffer it is
-- converted to the SYSTEM codepage (GetACP; 65001 = system UTF-8 passes
-- through; DBCS codepages go through Data/DBCSFonts/<enc>.tbl, cp1252 is
-- mapped directly), and once the game window exists the title is re-set
-- with SetWindowTextW in real Unicode, so it displays right on ANY locale.
-- A value that is not valid UTF-8 is used as raw bytes (legacy format).

-- WARNING:
-- MM8 (or MMMerge) and MM7 have a max limit of 23 characters (23 single-byte characters or 11.5 double-byte characters)
-- MM6 (or MMMerge) has a max limit of 19 characters (19 single-byte characters or 9.5 double-byte characters)


local mmver = offsets.MMVersion
local function mmv(...)
	return select(mmver - 5, ...)
end

-- keys only count inside their [section]
local function parseIni(content)
	local sections = {}
	local cur
	for line in content:gmatch("[^\r\n]+") do
		if not line:match("^%s*[;#]") then
			local sec = line:match("^%s*%[([^%]]+)%]")
			if sec then
				cur = sections[sec] or {}
				sections[sec] = cur
			elseif cur then
				local k, v = line:match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
				if k then
					cur[k] = v
				end
			end
		end
	end
	return sections
end

-- byte ranges of the DBCS encodings; must mirror tools/gen_dbcstbl.py, which
-- generates the .tbl files these tables index into
local encRanges = {
	gb2312    = {hi = {{0xA1, 0xA9}, {0xB0, 0xF7}}, lo = {{0xA0, 0xFE}}},
	gbk       = {hi = {{0x81, 0xFE}},               lo = {{0x40, 0x7E}, {0x80, 0xFE}}},
	big5      = {hi = {{0xA1, 0xC7}, {0xC9, 0xF9}}, lo = {{0x40, 0x7E}, {0xA0, 0xFE}}},
	shift_jis = {hi = {{0x81, 0x9F}, {0xE0, 0xFC}}, lo = {{0x40, 0x7E}, {0x80, 0xFC}}},
	euc_kr    = {hi = {{0xA1, 0xAC}, {0xB0, 0xC8}, {0xCA, 0xFD}}, lo = {{0xA0, 0xFE}}},
}

-- cp1252's 0x80-0x9F block (the rest matches Unicode 0xA0-0xFF directly)
local cp1252Specials = {
	[0x20AC] = 0x80, [0x201A] = 0x82, [0x0192] = 0x83, [0x201E] = 0x84,
	[0x2026] = 0x85, [0x2020] = 0x86, [0x2021] = 0x87, [0x02C6] = 0x88,
	[0x2030] = 0x89, [0x0160] = 0x8A, [0x2039] = 0x8B, [0x0152] = 0x8C,
	[0x017D] = 0x8E, [0x2018] = 0x91, [0x2019] = 0x92, [0x201C] = 0x93,
	[0x201D] = 0x94, [0x2022] = 0x95, [0x2013] = 0x96, [0x2014] = 0x97,
	[0x02DC] = 0x98, [0x2122] = 0x99, [0x0161] = 0x9A, [0x203A] = 0x9B,
	[0x0153] = 0x9C, [0x017E] = 0x9E, [0x0178] = 0x9F,
}

-- strictly decode a UTF-8 string into code points (BMP is enough here);
-- nil = not valid UTF-8, i.e. a legacy raw-bytes program_name
local function utf8Decode(s)
	local function cont(b)
		return b ~= nil and b >= 0x80 and b < 0xC0
	end
	local cps = {}
	local i, n = 1, #s
	while i <= n do
		local b = s:byte(i)
		if b < 0x80 then
			cps[#cps + 1] = b
			i = i + 1
		elseif b >= 0xC2 and b < 0xE0 and cont(s:byte(i + 1)) then
			cps[#cps + 1] = (b % 0x20) * 0x40 + s:byte(i + 1) % 0x40
			i = i + 2
		elseif b >= 0xE0 and b < 0xF0 and cont(s:byte(i + 1)) and cont(s:byte(i + 2)) then
			cps[#cps + 1] = (b % 0x10) * 0x1000 + (s:byte(i + 1) % 0x40) * 0x40
				+ s:byte(i + 2) % 0x40
			i = i + 3
		elseif b >= 0xF0 and b < 0xF5 and cont(s:byte(i + 1)) and cont(s:byte(i + 2))
				and cont(s:byte(i + 3)) then
			cps[#cps + 1] = 0x3F -- outside the BMP (and the .tbl): "?"
			i = i + 4
		else
			return nil
		end
	end
	return cps
end

-- build code point -> DBCS pair from the encoding's .tbl (flat LE u16 array
-- over the valid hi/lo byte ranges, same layout the font renderer reads)
local function loadReverseTbl(enc)
	local r = encRanges[enc]
	if not r then
		return nil
	end
	local f = io.open("Data/DBCSFonts/" .. enc .. ".tbl", "rb")
	if not f and enc == "gbk" then -- gb2312 covers gbk-encodable names
		f = io.open("Data/DBCSFonts/gb2312.tbl", "rb")
		r = encRanges.gb2312
	end
	if not f then
		return nil
	end
	local data = f:read("*all")
	f:close()
	local los = {}
	for _, range in ipairs(r.lo) do
		for b = range[1], range[2] do
			los[#los + 1] = b
		end
	end
	local rev = {}
	local idx = 0
	for _, range in ipairs(r.hi) do
		for hi = range[1], range[2] do
			for _, lo in ipairs(los) do
				local p = idx * 2
				if p + 2 <= #data then
					local cp = data:byte(p + 1) + data:byte(p + 2) * 256
					if cp ~= 0 and not rev[cp] then
						rev[cp] = string.char(hi, lo)
					end
				end
				idx = idx + 1
			end
		end
	end
	return rev
end

-- encode code points into the target encoding; unmappable characters -> "?"
local function encodeCps(cps, enc)
	local rev = encRanges[enc] and loadReverseTbl(enc)
	local out = {}
	for _, cp in ipairs(cps) do
		if cp < 0x80 then
			out[#out + 1] = string.char(cp)
		elseif rev then
			out[#out + 1] = rev[cp] or "?"
		elseif enc == "cp1252" then
			if cp >= 0xA0 and cp <= 0xFF then
				out[#out + 1] = string.char(cp)
			else
				out[#out + 1] = cp1252Specials[cp] and string.char(cp1252Specials[cp]) or "?"
			end
		else
			out[#out + 1] = "?"
		end
	end
	return table.concat(out)
end

-- trim to a byte budget without cutting a DBCS pair in half
local function fitBytes(s, limit, enc)
	if #s <= limit then
		return s
	end
	local r = encRanges[enc]
	if not r then
		-- passthrough bytes are UTF-8: don't leave a torn sequence at the end
		local cut = s:sub(1, limit)
		while #cut > 0 do
			local b = cut:byte(#cut)
			if b >= 0x80 and b < 0xC0 then
				cut = cut:sub(1, #cut - 1) -- continuation byte
			elseif b >= 0xC0 then
				cut = cut:sub(1, #cut - 1) -- dangling lead byte
				break
			else
				break
			end
		end
		return cut
	end
	local leadMin = 0x100
	for _, range in ipairs(r.hi) do
		if range[1] < leadMin then
			leadMin = range[1]
		end
	end
	local i = 1
	local fit = 0
	while i <= #s do
		local step = (s:byte(i) >= leadMin and i < #s) and 2 or 1
		if fit + step > limit then
			break
		end
		fit = fit + step
		i = i + step
	end
	return s:sub(1, fit)
end

-- system codepage -> the encoding name our converter understands
local acpNames = {
	[936] = "gbk", [950] = "big5", [932] = "shift_jis", [949] = "euc_kr",
	[1252] = "cp1252",
}

local function systemTarget()
	local ok, acp = pcall(function()
		return mem.dll.kernel32.GetACP()
	end)
	if not ok or not acp or acp == 65001 then
		return nil -- unknown system or system UTF-8: pass the bytes through
	end
	return acpNames[acp] -- unmapped codepages pass through too
end

-- UTF-16LE bytes (+ terminator) for SetWindowTextW
local function utf16(cps)
	local out = {}
	for _, cp in ipairs(cps) do
		out[#out + 1] = string.char(cp % 256, math.floor(cp / 256))
	end
	out[#out + 1] = "\0\0"
	return table.concat(out)
end

local fs = io.open("Data/LocalizeConf.ini", "r")
if fs then
	local content = fs:read("*all")
	fs:close()
	local st = parseIni(content).Settings or {}
	local ProgramName = st.program_name
	if ProgramName and ProgramName ~= "" then
		local limit = mmv(19, 23, 23)
		local cps = utf8Decode(ProgramName)
		local bytes, target
		if cps then
			target = systemTarget()
			bytes = target and encodeCps(cps, target) or ProgramName
			bytes = fitBytes(bytes, limit, target)
		else
			bytes = ProgramName:sub(1, limit) -- legacy raw bytes: cut as before
		end
		mem.copy(mmv(0x4C083C, 0x4E9FCC, 0x4F9D28), bytes .. "\0")
		if cps then
			-- set the title in real Unicode so it displays correctly whatever
			-- the system locale is. Re-applied a few times because the engine
			-- may reset the ANSI title during startup; the window handle
			-- comes from the Game struct or, failing that, GetActiveWindow.
			local logOn = st.nativelog == "1"
			local function dlog(msg)
				if not logOn then
					return
				end
				local f = io.open("FNT_DBCS.log", "a")
				if f then
					f:write(os.date("%H:%M:%S "), "ProgramName: ", msg, "\n")
					f:close()
				end
			end
			local okAcp, acp = pcall(function()
				return mem.dll.kernel32.GetACP()
			end)
			dlog(string.format("acp=%s target=%s ansi-bytes=%d",
				okAcp and tostring(acp) or "?", tostring(target), #bytes))
			local wide = utf16(cps)
			local buf
			local loggedNoWnd = false
			local loggedApply = false
			local function applyW()
				local hwnd = 0
				pcall(function()
					hwnd = Game.WindowHandle or 0
				end)
				if hwnd == 0 then
					local ok, h = pcall(function()
						return mem.dll.user32.GetActiveWindow()
					end)
					hwnd = ok and h or 0
				end
				if hwnd == 0 then
					if not loggedNoWnd then
						loggedNoWnd = true
						dlog("no window handle yet (retrying every message)")
					end
					return false
				end
				local ok, err = pcall(function()
					if not buf then
						buf = mem.StaticAlloc(#wide)
						mem.copy(buf, wide)
					end
					-- the game's window procedure swallows WM_SETTEXT (a
					-- SetWindowTextW call "succeeds" but nothing changes), so
					-- go straight to DefWindowProcW: it stores the caption in
					-- the system's internal (always-Unicode) storage and
					-- repaints, no matter what the window proc does
					local WM_SETTEXT, WM_GETTEXT = 0x000C, 0x000D
					local r = mem.dll.user32.DefWindowProcW(hwnd, WM_SETTEXT, 0, buf)
					local rb = mem.StaticAlloc(64)
					local n = mem.dll.user32.DefWindowProcW(hwnd, WM_GETTEXT, 30, rb)
					local back = {}
					for i = 0, math.min(n or 0, 12) * 2 - 1 do
						back[#back + 1] = string.format("%02x", mem.u1[rb + i])
					end
					if not loggedApply then
						loggedApply = true
						dlog(string.format("DefWindowProcW settext ret=%s (hwnd %X) readback[%s]=%s",
							tostring(r), hwnd, tostring(n), table.concat(back)))
					end
				end)
				if not ok then
					dlog("DefWindowProcW settext FAILED: " .. tostring(err))
				end
				return ok
			end
			-- the window doesn't exist yet while scripts load, and Tick may
			-- only start once a map is entered - so hook WindowMessage, which
			-- pumps as soon as the window is up (main menu included): retry
			-- every message until the first success, then re-apply twice in
			-- case the engine resets the title during startup
			-- keep re-applying periodically forever: GrayFace options (e.g.
			-- an FPS readout) and the engine itself may keep rewriting the
			-- title from the ANSI buffer; one API call every ~2000 messages
			-- is free
			local done = false
			local wmOk = pcall(function()
				local n = 0
				function events.WindowMessage()
					n = n + 1
					if not done then
						done = applyW()
					elseif n % 2000 == 0 then
						applyW()
					end
				end
			end)
			local tickOk = pcall(function()
				local t = 0
				function events.Tick()
					t = t + 1
					if (not done and t % 10 == 1) or t % 300 == 0 then
						done = applyW() or done
					end
				end
			end)
			dlog(string.format("handlers registered: WindowMessage=%s Tick=%s",
				tostring(wmOk), tostring(tickOk)))
		end
	end
end
