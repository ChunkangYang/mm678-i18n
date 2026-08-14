# MM678 I18N

[简体中文说明 (Chinese README)](README.zh.md)

Localization project for **Might and Magic 6, 7, 8** (with [GrayFace Patch](https://grayface.github.io/mm/)) and **[Might and Magic Merge](https://www.celestialheavens.com/forum/10/16657)**.

The pipeline supports any language; Simplified Chinese (zh_CN) and Traditional Chinese (zh_TW) packs for MM Merge and MM8 are currently published.

<p align="center">
<img src="docs/img/mm678-i18n_social_preview.jpg" alt="MM678 I18N" width="600">
</p>

## 🎮 For players

| | Download | Guide |
|---|---|---|
| 中文语言包（整合版 / 魔法门8） | [GitHub Releases](https://github.com/might-and-magic/mm678-i18n/releases) | [中文说明与常见问题](https://might-and-magic.github.io/mm678-i18n/zh/) |

Install: put the language patch `.exe` into your game folder and run it. Details, screenshots and FAQ are on the [Chinese documentation site](https://might-and-magic.github.io/mm678-i18n/zh/).

## 🛠 For developers & translators

Everything is built with one command:

```
pip install -e .
mm678 build        # .po -> .mo -> game text -> postprod -> installers
```

- [Repository guide (AGENTS.md)](AGENTS.md) — one-page orientation: commands, architecture, invariants (auto-loaded by AI coding agents)
- [Architecture & pipeline](docs/dev/architecture.md) — what each stage does
- [Building](docs/dev/building.md) — prerequisites and commands
- [Adding a new language](docs/dev/new-language.md) — step-by-step (`mm678 new-language <lang>`)
- [Release process](docs/dev/release.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

Related projects: [MM Merge Updater](https://github.com/might-and-magic/mmmerge-update-patch), [mmarch](https://github.com/might-and-magic/mmarch), [cheats](https://github.com/might-and-magic/mm678-cheat) and more at [github.com/might-and-magic](https://github.com/might-and-magic).

## License

[MIT](LICENSE.md) for the code. “Might and Magic” is a trademark of Ubisoft Entertainment; game files are used under fair use and no full game content is included. GrayFace's patches and tools: see [their license](https://github.com/GrayFace/Misc/blob/master/LICENSE).
