import tempfile
import unittest
from pathlib import Path

import polib

from mm678i18n import pocheck


def buildPo(pairs):
	po = polib.POFile()
	po.metadata = {'Content-Type': 'text/plain; charset=UTF-8'}
	for ctxt, msgid, msgstr in pairs:
		po.append(polib.POEntry(msgctxt = ctxt, msgid = msgid, msgstr = msgstr))
	return po


class TestExtractTokens(unittest.TestCase):

	def testFindsPrintfForms(self):
		self.assertEqual(
			pocheck.extractTokens('Become %s in %s for %lu gold'),
			['%s', '%s', '%lu'])

	def testFindsNumberedTokens(self):
		self.assertEqual(
			pocheck.extractTokens('%07 %02, well met'),
			['%07', '%02'])

	def testIgnoresLiteralPercentInProse(self):
		# a general printf grammar would read these as '% b', '% c', '% p'
		for s in ('they see as less than 100% behind their leader',
				'encryption integrity at 2.064%.  Warning',
				'a 10% chance per point of skill',
				'Converts item to 40% gold value'):
			self.assertEqual(pocheck.extractTokens(s), [], s)

	def testClassifiesFamilies(self):
		self.assertTrue(pocheck.isPrintf('%s'))
		self.assertTrue(pocheck.isPrintf('%lu'))
		self.assertFalse(pocheck.isPrintf('%01'))
		self.assertFalse(pocheck.isPrintf('%31'))


class TestCheckPlaceholders(unittest.TestCase):

	def findingChecks(self, msgid, msgstr):
		return [f.check for f in pocheck.checkPlaceholders(msgid, msgstr)]

	def testIdenticalPassesClean(self):
		self.assertEqual(self.findingChecks(
			'It will take %d day to cross to %s.',
			'Il faudra %d jour pour rejoindre %s.'), [])

	def testDroppedTokenIsSetFailure(self):
		self.assertEqual(self.findingChecks(
			'%31 met %32 and %33 today',
			'%31 met %33 today'), ['placeholder-set'])

	def testSwappedFamilyIsSetFailure(self):
		self.assertEqual(self.findingChecks(
			'you have %s gold', 'you have %01 gold'), ['placeholder-set'])

	def testReorderedPrintfIsOrderFailure(self):
		# real defect found in translations/it: the engine feeds the day
		# count into %s and the destination string into %d
		self.assertEqual(self.findingChecks(
			'It will take %d day to cross to %s.',
			'La traversata fino a %s durerà %d giorno/i.'),
			['placeholder-order'])

	def testReorderedNumberedTokensArePermitted(self):
		# modelled on a real, legitimate case from translations/de: same set,
		# swapped order, and %11/%12 each identify themselves
		self.assertEqual(self.findingChecks(
			'Your reputation is only %12! Every %11 knows it.',
			'Dein Ruf ist %11! Das weiß jeder %12.'), [])

	def testPrintfOrderIgnoresInterleavedNumberedTokens(self):
		self.assertEqual(self.findingChecks(
			'%s of %01 owes %lu', '%s %01 %lu'), [])

	def testFindingsAreFailLevel(self):
		findings = pocheck.checkPlaceholders('%s here', 'nothing here')
		self.assertEqual([f.level for f in findings], [pocheck.FAIL])


class TestCheckControlChars(unittest.TestCase):

	def findingChecks(self, msgstr):
		return [f.check for f in pocheck.checkControlChars(msgstr)]

	def testCleanStringPasses(self):
		self.assertEqual(self.findingChecks('a normal translation'), [])

	def testRealNewlineIsPermitted(self):
		# the gettext escape '\n' in the .po file parses to a real LF, and
		# that is the canonical soft line break
		self.assertEqual(self.findingChecks('first line\nsecond line'), [])

	def testBareTabIsReported(self):
		self.assertEqual(self.findingChecks('name\tvalue'), ['tab'])

	def testCarriageReturnIsReported(self):
		self.assertEqual(self.findingChecks('line\r\nline'), ['cr'])

	def testLiteralBackslashNIsReported(self):
		self.assertEqual(self.findingChecks('first' + chr(92) + 'nsecond'),
			['literal-slash-n'])

	def testAllThreeAreFailLevel(self):
		findings = pocheck.checkControlChars('a\tb\rc' + chr(92) + 'nd')
		self.assertEqual(sorted(f.check for f in findings),
			['cr', 'literal-slash-n', 'tab'])
		self.assertEqual({f.level for f in findings}, {pocheck.FAIL})


class TestDirectionalRules(unittest.TestCase):

	def wsChecks(self, msgid, msgstr):
		return [f.check for f in pocheck.checkWhitespace(msgid, msgstr)]

	def nlChecks(self, msgid, msgstr):
		return [f.check for f in pocheck.checkNewlines(msgid, msgstr)]

	def testSpaceCounters(self):
		self.assertEqual(pocheck.leadingSpaces('   a'), 3)
		self.assertEqual(pocheck.trailingSpaces('a   '), 3)
		self.assertEqual(pocheck.trailingSpaces('a\n'), 0)  # LF is not a space

	def testDroppedTrailingSpaceIsExempt(self):
		# real case: source pads the cell, the translation drops the padding
		self.assertEqual(self.wsChecks('Brand ', '布兰德'), [])

	def testAddedTrailingSpaceIsReported(self):
		# real case from translations/zh_CN
		self.assertEqual(
			self.wsChecks("Abdul's Discount Magic Supplies", '阿卜杜的廉价魔法器具 '),
			['whitespace'])

	def testDroppedLeadingSpaceIsExempt(self):
		self.assertEqual(self.wsChecks(' Brand', '布兰德'), [])

	def testAddedLeadingSpaceIsReported(self):
		self.assertEqual(self.wsChecks('Brand', ' 布兰德'), ['whitespace'])

	def testMergedLinesAreExempt(self):
		# 84% of the real newline differences: CJK does not need the
		# English line breaks
		self.assertEqual(
			self.nlChecks('Hello?\nAh, someone else!\nMy name is Simon.',
				'你好！啊，又是另一个家伙！我是赛蒙。'), [])

	def testAddedNewlineIsReported(self):
		self.assertEqual(
			self.nlChecks('Etched into the tree a message reads:      ',
				'树上刻着的消息如下：\n第一个是第四个的一半再加一'),
			['newline'])

	def testEqualCountsPass(self):
		self.assertEqual(self.nlChecks('a\nb', 'x\ny'), [])

	def testDirectionalFindingsAreWarnLevel(self):
		self.assertEqual(
			[f.level for f in pocheck.checkNewlines('a', 'x\ny')], [pocheck.WARN])
		self.assertEqual(
			[f.level for f in pocheck.checkWhitespace('a', 'x ')], [pocheck.WARN])

	def testExemptDifferencesReportsReductions(self):
		self.assertEqual(
			[f.check for f in pocheck.exemptDifferences('Brand ', '布兰德')],
			['whitespace'])
		self.assertEqual(
			[f.check for f in pocheck.exemptDifferences('a\nb', 'ab')],
			['newline'])

	def testExemptDifferencesIgnoresAdditions(self):
		# additions are the reported direction, not the exempt one
		self.assertEqual(pocheck.exemptDifferences('Brand', '布兰德 '), [])
		self.assertEqual(pocheck.exemptDifferences('ab', 'a\nb'), [])

	def testExemptFindingsCarryExemptLevel(self):
		self.assertEqual(
			[f.level for f in pocheck.exemptDifferences('a\nb', 'ab')],
			[pocheck.EXEMPT])


class TestAllowlist(unittest.TestCase):

	def testKeyIsTwelveHexChars(self):
		k = pocheck.entryKey('location', 'Brand')
		self.assertEqual(len(k), 12)
		self.assertTrue(all(c in '0123456789abcdef' for c in k))

	def testKeyDependsOnBothParts(self):
		self.assertNotEqual(
			pocheck.entryKey('location', 'Brand'),
			pocheck.entryKey('npcprof', 'Brand'))
		self.assertNotEqual(
			pocheck.entryKey('location', 'Brand'),
			pocheck.entryKey('location', 'Erathia'))

	def testKeyIsStable(self):
		self.assertEqual(
			pocheck.entryKey('location', 'Brand'),
			pocheck.entryKey('location', 'Brand'))

	def testMissingFileLoadsEmpty(self):
		self.assertEqual(pocheck.loadAllowlist(Path('does/not/exist.toml')), {})

	def testLoadedEntryScopesToNamedChecks(self):
		with tempfile.TemporaryDirectory() as d:
			p = Path(d, 'a.toml')
			p.write_text(
				'[[allow]]\n'
				'key = "abc123abc123"\n'
				'lang = "zh_CN"\n'
				'checks = ["newline"]\n'
				'reason = "test"\n', encoding = 'UTF-8')
			al = pocheck.loadAllowlist(p)
		self.assertTrue(pocheck.isAllowed(al, 'zh_CN', 'abc123abc123', 'newline'))
		# a different check on the same entry is still reported
		self.assertFalse(pocheck.isAllowed(al, 'zh_CN', 'abc123abc123', 'whitespace'))
		# a different language is unaffected
		self.assertFalse(pocheck.isAllowed(al, 'de', 'abc123abc123', 'newline'))

	def testShippedAllowlistParses(self):
		al = pocheck.loadAllowlist()
		self.assertIsInstance(al, dict)


class TestCheckEntry(unittest.TestCase):

	def checksFor(self, msgid, msgstr, ctxt = 'location', allowlist = None):
		e = polib.POEntry(msgctxt = ctxt, msgid = msgid, msgstr = msgstr)
		return [f.check for f in pocheck.checkEntry(e, 'zh_CN', allowlist or {})]

	def testCleanEntryHasNoFindings(self):
		self.assertEqual(self.checksFor('%31 arrives', '%31 到了'), [])

	def testUntranslatedEntryIsSkipped(self):
		self.assertEqual(self.checksFor('%31 arrives', ''), [])

	def testObsoleteEntryIsSkipped(self):
		e = polib.POEntry(msgctxt = 'location', msgid = '%s', msgstr = 'no token')
		e.obsolete = True
		self.assertEqual(pocheck.checkEntry(e, 'zh_CN', {}), [])

	def testFuzzyEntryIsSkipped(self):
		e = polib.POEntry(msgctxt = 'location', msgid = '%s', msgstr = 'no token')
		e.flags = ['fuzzy']
		self.assertEqual(pocheck.checkEntry(e, 'zh_CN', {}), [])

	def testCollectsAcrossCheckFamilies(self):
		self.assertEqual(
			sorted(self.checksFor('%s here', 'no token\there ')),
			['placeholder-set', 'tab', 'whitespace'])

	def testAllowlistSuppressesOnlyNamedCheck(self):
		key = pocheck.entryKey('location', 'Brand')
		al = {('zh_CN', key): {'whitespace'}}
		self.assertEqual(self.checksFor('Brand', '布兰德 ', allowlist = al), [])
		# same entry, a check that is not exempt
		al2 = {('zh_CN', key): {'newline'}}
		self.assertEqual(self.checksFor('Brand', '布兰德 ', allowlist = al2),
			['whitespace'])


class TestCheckFile(unittest.TestCase):

	def samplePo(self, d):
		p = Path(d, 'x.po')
		buildPo([
			('location', '%s gold', 'no token'),      # FAIL
			('location', 'Brand ', '布兰德 '),         # clean (equal padding)
			('location', 'Erathia', '厄拉希亚 '),       # WARN (added space)
			('location', 'a\nb', 'ab'),               # exempt (dropped break)
		]).save(str(p))
		return p

	def testCountsFailAndWarnSeparately(self):
		with tempfile.TemporaryDirectory() as d:
			pairs, total, _ = pocheck.checkFile(self.samplePo(d), 'zh_CN', {})
		levels = [f.level for _, f in pairs]
		self.assertEqual(total, 4)
		self.assertEqual(levels.count(pocheck.FAIL), 1)
		self.assertEqual(levels.count(pocheck.WARN), 1)
		self.assertEqual(levels.count(pocheck.EXEMPT), 0)

	def testStrictPromotesWarnToFail(self):
		with tempfile.TemporaryDirectory() as d:
			pairs, _, _ = pocheck.checkFile(
				self.samplePo(d), 'zh_CN', {}, strict = True)
		levels = [f.level for _, f in pairs]
		self.assertEqual(levels.count(pocheck.FAIL), 2)
		self.assertEqual(levels.count(pocheck.WARN), 0)

	def testShowExemptAddsSuppressedDifferences(self):
		with tempfile.TemporaryDirectory() as d:
			pairs, _, _ = pocheck.checkFile(
				self.samplePo(d), 'zh_CN', {}, showExempt = True)
		levels = [f.level for _, f in pairs]
		self.assertEqual(levels.count(pocheck.EXEMPT), 1)

	def testPairsCarryTheirEntry(self):
		with tempfile.TemporaryDirectory() as d:
			pairs, _, _ = pocheck.checkFile(self.samplePo(d), 'zh_CN', {})
		entry, finding = next((e, f) for e, f in pairs if f.level == pocheck.FAIL)
		self.assertEqual(entry.msgid, '%s gold')
		self.assertEqual(finding.check, 'placeholder-set')


if __name__ == '__main__':
	unittest.main()
