-- We have to watch the whole introductory movie after a fresh new installation of MM6, 7 or 8 (including MMMerge).
-- With this script, you can close the movie with Esc key.

local mmver = offsets.MMVersion
if mmver == 8 then
    mem.nop(0x463EF0, 2)
elseif mmver == 6 then
    mem.nop(0x457BA4, 2)
end
