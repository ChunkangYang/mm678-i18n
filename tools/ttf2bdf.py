# Rasterize a TTF/OTF into a bitmap BDF at a fixed pixel size, restricted to
# the code points of one or more encoding .tbl files (see gen_dbcstbl.py) so
# the output only carries the glyphs the game can ever request.
#
#   python tools/ttf2bdf.py <font.ttf|otf> <px> <out.bdf> <charset.tbl>[,more.tbl]
#
# Requires: pip install freetype-py
import os
import struct
import sys

import freetype


def tbl_codepoints(paths):
	cps = set()
	for p in paths:
		data = open(p, 'rb').read()
		for i in range(0, len(data), 2):
			u = struct.unpack_from('<H', data, i)[0]
			if u:
				cps.add(u)
	return cps


def main():
	src, px, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
	cps = sorted(tbl_codepoints(sys.argv[4].split(',')))

	face = freetype.Face(src)
	face.set_pixel_sizes(0, px)
	asc = round(face.size.ascender / 64)
	if asc < 1 or asc > px:
		asc = px - max(1, px // 8)
	desc = px - asc  # rows below the baseline in our fixed-height canvas

	flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO
	glyphs = []
	for cp in cps:
		if face.get_char_index(cp) == 0:
			continue  # not in the font: stays a missing glyph at runtime
		face.load_char(cp, flags)
		g = face.glyph
		bmp = g.bitmap
		dx = round(g.advance.x / 64)
		if dx < 1:
			dx = px
		bw, bh = bmp.width, bmp.rows
		bx, by = g.bitmap_left, g.bitmap_top - bmp.rows
		rows = []
		if bw == 0 or bh == 0:
			# blank glyph (e.g. U+3000): keep a 1x1 empty bitmap so the
			# runtime still gets a record with the right advance
			bw, bh, bx, by = 1, 1, 0, 0
			rows = ['00']
		else:
			nbytes = (bw + 7) // 8
			buf = bmp.buffer
			for r in range(bh):
				row = bytes(buf[r * bmp.pitch: r * bmp.pitch + nbytes])
				rows.append(row.hex().upper())
		glyphs.append((cp, dx, bw, bh, bx, by, rows))

	name = os.path.splitext(os.path.basename(src))[0]
	with open(out, 'w', newline='\n') as f:
		f.write('STARTFONT 2.1\n')
		f.write('FONT -mm678-%s-medium-r-normal--%d-%d0-75-75-c-%d0-iso10646-1\n'
			% (name, px, px, px))
		f.write('SIZE %d 75 75\n' % px)
		f.write('FONTBOUNDINGBOX %d %d 0 %d\n' % (px, px, -desc))
		f.write('STARTPROPERTIES 2\nFONT_ASCENT %d\nFONT_DESCENT %d\nENDPROPERTIES\n'
			% (asc, desc))
		f.write('CHARS %d\n' % len(glyphs))
		for cp, dx, bw, bh, bx, by, rows in glyphs:
			f.write('STARTCHAR uni%04X\n' % cp)
			f.write('ENCODING %d\n' % cp)
			f.write('SWIDTH 500 0\nDWIDTH %d 0\n' % dx)
			f.write('BBX %d %d %d %d\n' % (bw, bh, bx, by))
			f.write('BITMAP\n')
			for r in rows:
				f.write(r + '\n')
			f.write('ENDCHAR\n')
		f.write('ENDFONT\n')
	print('%s: %d glyphs @%dpx, ascent %d, %d KB'
		% (out, len(glyphs), px, asc, os.path.getsize(out) // 1024))


if __name__ == '__main__':
	main()
