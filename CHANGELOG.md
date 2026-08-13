# Changelog

Versions are those of the language packs (not of the GrayFace Patch or of MM
Merge). Player-facing notes in Chinese: see the
[中文文档](https://might-and-magic.github.io/mm678-i18n/zh/).

## [Unreleased]

- Build pipeline rewritten as the `mm678` CLI (one-command build); repository
  restructured (`source/`, `templates/`, `translations/`, `assets/`,
  `installer/`, generated output in `build/`); shared files deduplicated into
  single sources of truth; `mm678 new-language` command; French placeholder
  language added; CI checks and release workflow; portable extract-over
  `.zip` packages are now produced alongside the `.exe` installers.

## v2.3 — 2021-07-09

- 根据2021-07-05版整合版升级；更新简繁翻译

## v2.2.1 — 2020-12

- NPC姓名修正；MM78方尖塔重译；其他一些翻译统一和修正

## v2.2 — 2020-08-21

- 根据最新2020-08-16版整合版升级；NPC对话（主要是魔法门6中的）的修正；修复繁体的部分字串未显示的问题

## v2.1 — 2020-08-01

- 根据最新2020-07-12版整合版升级；一些魔法描述的小修正；特殊怪物及NWC地下城内员工名的翻译

## v2.0 — 2020-06-05

- 根据最新2020-05-26版整合版升级；发布繁体；魔法门8的“历史”未译的按原文翻译，部分重译；修复失控混沌NPC姓名问题；修复无法读LocalizeTables.*.txt中含多行的字串问题

## v1.3.1 — 2020-03-04

- hotfix：修复将队员姓名替换为吸血鬼飞龙等的问题

## v1.3 — 2020-03-03

- 谜语和需键盘输入处（阴影教传送门、黑摩尔城堡棺材、最终的失控混沌谜语等）跳出问题修复；弓箭和榴弹枪恢复时间无下限；“缺口”（Breach）改为“大裂缝”；翻译维尔丹任务、大裂缝及其地下室、少数升职任务未译字串；通关证书翻译和背景修饰；魔幻牌几张牌修正；加入魔法门8简中升级包

## v1.2.2 — 2020-02-21

- 技能专家大师描述检查统一；火炬加点数问题修复；火炬名；“游侠/武士”（Paladin）改为“圣武士”

## v1.2.1 — 2020-02-12

- hotfix：修复文字中的“{}”符号

## v1.2 — 2020-02-12

- 统一职业、技能、属性、魔法、生物、物品、词缀、地图等的翻译；全部译完；MM6翻译使用“完美版”；NPCText.txt根据整合版修改；修复了mm?lang.ini中的中文的显示问题；MM8Setup.Exe的汉化和修图

## v1.1.1 — 2020-02-04

- 修复了setPlayerName()的问题；主题和选项画面、三大陆图等加中文，MM8 logo换掉；解决翡翠岛上NPC对话无法翻译的问题

## v1.1 — 2020-02-03

- 修复了.str中字串过长进入地图跳出的问题；Global.txt里的翻译修正

## v1.0 — 2020-02-02

- 修复显示不正常问题；修复无.fnt文件跳出问题；加了mm6的中文语音，几乎全部汉化；统一了几乎所有标题名字的字串的翻译；NPC姓名的本地化文件放于Data下；怪物强化公式用乘以（但在2020-06-05版本中还原为了原版整合版的设置）；魔幻牌图片

## v0.9.1 — 2020-01-25

- 修改了存档文件名导致崩溃的问题

## v0.9 — 2020-01-24

- 初始发布
