# 媒体本地化清单(图片 / 音频 / 视频)

MM6/7/8 + MM Merge 全部需要 i18n 的非文本资产,盘点于 2026-08(与最新上游
GrayFace 2.5.7 / Merge 2024-10-30 逐字节对账后的结果;死重已剔除)。
文字表格类见文本管线,字体见 `fonts.md`。

## 总览

| 游戏 | 图片 zh_CN | 图片 zh_TW | 音频(配音 wav) | 视频 | 打包目标 |
|---|---|---|---|---|---|
| mm6 | 56 | 2(暂不补) | 846 | 4(未接管线) | `10 Loc*.icons.lod` / `10 Loc*.Audio.snd` |
| mm7 | 88 | 85 | 2001 | 10(未接管线) | `10 Loc*.icons.lod` / `10 Loc*.Audio.snd` |
| mm8 | 9 + 共享 174 | 9 + 共享 172 | 无 | — | `10 Loc*.EnglishD.lod` |
| mmmerge | 9 + 18 + 共享 174 | 11 + 18 + 共享 172 | 846(复用 mm6) | 15(未接管线) | `zz Loc*.D.lod`(含配音)/ `zz Loc*.icons.lod` |

- 资产位置:`assets/img/prod/<lang>/<game>/…`、`assets/sound/prod/zh_CN/…`、
  `assets/video/prod/zh_CN/…`(sound/video 体积大,git 忽略,仅本地)。
- `mmmerge_and_mm8` 是伪游戏目录:一份源同时发往 mm8 与 mmmerge。
- zh_TW 的音频在 postprod 自动复用 zh_CN 配音,无独立资产。
- `en/mmmerge/Data/EnglishD`(201 个)是英文参考副本,非翻译对象。

## mm6 图片(zh_CN 56 张,`data/icons` → `10 LocZHCN.icons.lod`)

- 标题:`mm6title.pcx`(魔法门VI天堂之令)、`title.pcx`、`segue_bg.pcx`
- 主菜单按钮:`mmnew1` `mmloa1` `mmcre1` `mmesc1`、`new1` `load1` `save1`
  `quit1` `resume1` `creat_dn` `quick_dn`
- 载入/存档:`loadsave` `lsave640.pcx` `load_up` `save_up`
- 设置:`options` `control1` `controlbg`、视频按钮 `con_16x` `con_32x`
  `con_high` `con_med` `con_low` `con_resh` `con_smoo`
- 开场剧情图:`start00a`–`start06d`(7 幕 × 4 帧,28 张)
- zh_TW 仅 `mm6title.pcx` `title.pcx` 两张(2026-08 决定暂不补齐其余,
  忠实 CHT 官方原版)

## mm7 图片(zh_CN 88 / zh_TW 85,`DATA/icons` → `10 Loc*.icons.lod`)

- 标题与主菜单:`title.pcx` `mm6title.pcx` `title_new` `title_load`
  `title_cred` `title_exit`、`new1` `load1` `save1` `quit1` `resume1`
  `controls1` `buttexi2` `buttmake` `buttmake2`
- 载入/存档:`loadsave` `lsave640.pcx` `ls_loadd/u` `ls_saved/u`
  `load_up` `save_up`
- 设置:`options` `option01`–`04`、键位 `optkb` `optkb_1/2/b/d/r`
  `conkb-d` `controlbg`、视频 `optvid` `optv_d` `opvdg-*` `opvdh-*`
  `con_*`(16x/32x/high/med/low/smoo)
- 角色界面页框:`fr_stats` `fr_skill` `fr_inven`(-b/-c)`fr_award`
- 界面侧栏/日历等:`ib-bcd/bcu-*` `ib-cd1–5-d` `ib-m5/m6-*`
  `ib-ma/mb-*`(Arcomage 桌沿)`ib-r-*.pcx`
- `Sprites.PCX`:**Arcomage 卡牌图集简中版(960×1372,全卡牌+按钮)**
- 其他:`quikref`(快速参考)`makeme.pcx`(创建角色)`x_d` `x_u`
  `x_ok_d/u` `x_x_u`(关闭/确认)
- 简繁互缺(见 TODO):zh_TW 缺 `con_16x/32x` `load_up/save_up`;
  zh_CN 缺 `buttexi1`

## mm8 / mmmerge 专属图片

mm8 与 merge 各自的 `Data/EnglishD`(9–11 张):`Title.pcx` `mm6title.pcx`
`Options` `optkb` `optvid` `controlbg` `makeme.pcx` `Lsave640`,外加
mm8 的 `winBG.pcx` / merge 的 `winbg2.pcx`(胜利结算底图)。zh_TW 版另含
`sprites.pcx`/`sba000`(历史打包差异,内容与共享版一致)。

merge 的 `Data/icons`(18 张,简繁各一套)→ `zz Loc*.icons.lod`:

- 大陆选择屏:`SlBackgr` `SlEnrothDw/Up` `SlJadamDw/Up` `SlAntagDw/Up`
- 附加设置屏:`ExSetScr`(选项列表)`ExSetScr2`(空模板)
  `ExSetScrK`(额外键位)`ExtSetDw/Up`
- 开关:`TmblrOff/On` `blstr_off/on` `wthr_off/on`
- 待重画 2 张(上游 2024-10-30 改文,见 TODO):`ExSetScr`(第 4 项
  Frame limit,现仍是"增大视野范围")、`ExSetScrK`(缺 EXTRA KEYBINDS
  标题)

## 共享图片 `mmmerge_and_mm8/Data/EnglishD`(zh_CN 174 / zh_TW 172)

同时发往 mm8 与 mmmerge(merge 里进 `zz Loc*.D.lod`):

- MM6 风格三态按钮:`bt_*`(new/load/save/quit/cont/back/cncl/dflt/rtrn/
  sage/loag/run/flip/hits/smoo/vdop/wksd/cfkb… × Down/Hover/Up)
  `bu_*`(load/save/rtrn)`bv_rtrn*`
- 设置行标签:`bl_*`(music/sound/voice/brite/tint/colt/blsp/turn/prevu)
- 自定义键位:`c_*`(ok/close/clr/cncl/dft/ext × dn/ht/up)
- 标题菜单:`t_new/load/cred/quit_*`
- 休息界面:`restmain` `r*` `rdawn*` `rexit*` `irt*`
- 雇佣:`buthire[d/h/u]`、其余 `but*` 按钮
- 法术书页:`sb[a/b/d/de/dk/e/f/l/m/s/v/w]000`(12 系;页面本身无字,
  仅边框/导出差异。英文档里另有 `sb*000a` 后缀变体,同样无字,无需处理)
- **`sprites.pcx`:Arcomage 卡牌图集简中版,960×2500 全尺寸**——与最新
  merge 的英文版同尺寸,merge 的 Arcomage 汉化**已由此覆盖**(merge 自身
  的 mmmerge.D.lod 不含 sprites,继承 mm8.D 后被我们的 zz 档压住)
- `ib-comp-a`、`bt_p1/p2*`(指南针/翻页)

## 音频(配音,zh_CN;zh_TW 构建时自动复用)

- mm6:`Sounds/Audio` 846 个 wav → `10 Loc*.Audio.snd`
- mm7:`SOUNDS/Audio` 2001 个 wav → `10 Loc*.Audio.snd`
- mmmerge:`Data/EnglishD` 846 个 wav(即 mm6 配音,merge 里 NPC 语音走
  D 档)→ 并入 `zz Loc*.D.lod`(与图片同档)
- mm8:无中文配音

## 视频(zh_CN,**尚未接入管线**——见 TODO)

- mm6 `Anims/Anims2`:`MM6Intro.smk` `credits.smk` `CityTrtr.smk`
  `End_seq1.smk`
- mm7 `Anims/Magic7`:`Intro.bik` `Intro Post.bik` `Arbiter Good/Evil.bik`
  `MM3 People Good/Evil.bik` `Endgame 1 Good.bik` `Family Reunion.bik`
  `LoseGame.bik` `PCOut01.bik`
- mmmerge(平铺,含上述两代合集):`6intro` `7intro` `7losegame` 等
  14 个 + `中文动画.zip`(源包)
- 计划:`Anims/10 Loc*.Magicdod.vid` 之类的追加 vid 档(postprod 的
  TODO 注释),或按 merge 惯例直接放 `Anims/` 松散文件

## 新语言备忘

必做:标题/菜单/设置按钮类(mm6 56、mm7 88、mm8+共享 183、merge icons
18)。可选:Arcomage 图集(工作量大,参考 zh_CN/LocFR)、配音、视频。

已有官方/民间本地化版游戏时,用提取管线一键对账搬运(zh_CN 资产树即
"可翻译清单"参照;与英文版逐字节比对,只取真被改过的文件,不会搬入死重;
参照集外的差异文件出报告供人工审阅):

```
python tools/extract_media.py <lang> <game> <本地化版安装目录> <英文版安装目录> [--sound] [--video] [--all-images]
# 例:python tools/extract_media.py ja mm6 D:\games\mm6ja C:\game\mm\mmoriglang\mm6enpatch257
```

抽完 `mm678 postprod` 即打进对应语言的补丁档。没有现成本地化版的语言则需
从英文原图重画(原图可从英文版安装的 lod 里用 mmarch 解出)。
