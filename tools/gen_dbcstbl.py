# Generates the <encoding>.tbl files used by FNT_DBCS2.lua's BDF font mode:
# a flat little-endian u16 array of Unicode code points (0 = unmapped) indexed
# by (hiIndex * loCount + loIndex), where hi/lo indexes number the valid lead
# and trail bytes in range order. The ranges MUST mirror encProps in
# FNT_DBCS2.lua exactly.
#
#   python tools/gen_dbcstbl.py gb2312 assets/font/gb2312.tbl
import struct
import sys

RANGES = {
	'gb2312':    {'hi': [(0xA1, 0xA9), (0xB0, 0xF7)], 'lo': [(0xA0, 0xFE)]},
	'gbk':       {'hi': [(0x81, 0xFE)], 'lo': [(0x40, 0x7E), (0x80, 0xFE)]},
	'big5':      {'hi': [(0xA1, 0xC7), (0xC9, 0xF9)], 'lo': [(0x40, 0x7E), (0xA0, 0xFE)]},
	'shift_jis': {'hi': [(0x81, 0x9F), (0xE0, 0xFC)], 'lo': [(0x40, 0x7E), (0x80, 0xFC)]},
	'euc_kr':    {'hi': [(0xA1, 0xAC), (0xB0, 0xC8), (0xCA, 0xFD)], 'lo': [(0xA0, 0xFE)]},
}

# decode with the MS superset where one exists (cp932 covers NEC/IBM
# extensions that plain shift_jis rejects; harmless for the mapping table)
CODECS = {'shift_jis': 'cp932', 'euc_kr': 'cp949'}


def expand(ranges):
	out = []
	for lo, hi in ranges:
		out.extend(range(lo, hi + 1))
	return out


def build(encoding):
	r = RANGES[encoding]
	codec = CODECS.get(encoding, encoding)
	his, los = expand(r['hi']), expand(r['lo'])
	out = bytearray()
	mapped = 0
	for h in his:
		for l in los:
			try:
				u = ord(bytes([h, l]).decode(codec))
				if u > 0xFFFF:
					u = 0
			except (UnicodeDecodeError, TypeError):
				u = 0
			if u:
				mapped += 1
			out += struct.pack('<H', u)
	return bytes(out), mapped, len(his), len(los)


if __name__ == '__main__':
	enc, outPath = sys.argv[1], sys.argv[2]
	data, mapped, nh, nl = build(enc)
	with open(outPath, 'wb') as f:
		f.write(data)
	print(f'{outPath}: {nh}x{nl} cells, {mapped} mapped, {len(data)} bytes')
