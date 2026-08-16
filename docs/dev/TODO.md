# TODO & known issues

(These would make good GitHub issues; kept here so they are not lost.)

## Images (2026-08 upstream audit)

对比最新上游后,全部 508 张本地化图片中仅 merge 的设置界面 3 张需要跟进
(中文源图在 `assets/img/prod/zh_CN/mmmerge/Data/icons/`,最新英文原图可从
`original-latest\mmmerge\Data\mmmerge.icons.lod` 解出;改完跑 `mm678 postprod`):

- [ ] `exsetscr.bmp`——上游把第 4 项 "Increased view range" 换成 **"Frame
  limit"**,中文版第 4 行仍是"增大视野范围",需重画(建议:帧数上限)
- [ ] `exsetscrk.bmp`——上游加了 **"EXTRA KEYBINDS"** 大标题,中文版没有,
  需补(建议:额外按键绑定)
- `exsetscr2.bmp` 仅底图重导出差异,无需改动
- (可选)**merge 版 Arcomage 卡牌汉化**:merge 的 `Sprites.pcx`(960×2500,
  在 `original-latest\mmmerge\Data\mm8.D.lod`)含全部卡牌文字与按钮,LocFR
  已全翻(参考 `C:\Users\Chen\Downloads\LocFR\zz LocFR.D.lod`)。**大底子已
  有**:`assets/img/prod/zh_CN/mm7/DATA/icons/Sprites.PCX` 是完整简中卡牌
  图集(960×1372,MM7 版),merge 版是其加高扩充,可在其基础上补差。
  `Layout.PCX`(棋盘背景)无文字不用做;FR 包里其余非 wav 差异(法术书
  空白页 sb*000a、16x/32x 按钮)经比对无文字变化,不需要做
- (可选)mm7cht 的 `swptree1-4.bmp`(sprites.lod 内无字树木图)与 zh-only
  杂项(lloyd41-45 引导图、全黑 image.pcx)审阅后判定不需要移植
- zh_TW 的 mm6 图片**暂不翻译**(2026-08 决定):忠实 CHT 原版,只有 2 张
  标题图,主菜单等保持英文;将来如需可把 zh_CN 的 56 张转繁重制
- mm7 简繁图集互有缺口(各自忠实官方版,2026-08 对账结论):
  - [ ] zh_TW 缺 4 张(CHT 官方没翻):`con_16x.bmp`/`con_32x.bmp`(视频
    选项 "16X/32X" 按钮,简体版重绘过样式)、`load_up.bmp`/`save_up.bmp`
    (**"装载游戏"/"保存游戏"大按钮的亮起态**——繁体版只翻了普通态,鼠标
    悬停时会闪回英文,可从 zh_CN 版转繁补齐)
  - [ ] zh_CN 缺 1 张(CHS 官方没翻):`buttexi1.bmp`("離開/离开"按钮的
    另一状态;简体版只翻了 buttexi2,可参照 zh_TW 版转简补齐)

## Pipeline / packaging

- NSIS 安装包 Delete 列表补旧布局残留(`10 LocZHCN.EnglishD.lod`、
  `z10 LocZHCN.icons.lod`、`10 LocLANG.EnglishT` 时代文件)——2026-08 改为
  `zz LocZHCN.{T,D,icons}.lod` 三件套后,旧包升级需清理
- `config/versions.py` 的 merge 版本号更新到最新基线
- 安装包清理其他语言的残留文件
- 视频本地化：`assets/video/zh_CN` → `Anims/10 LocZHCN.Magicdod.vid`

## Untranslated / display bugs

- torch、tree 的鼠标悬停标签未翻译（硬3D高清不显示标签，软3D低清显示但无法汉化；原版即有此问题）
- 维兰坟墓 “What is the Captain's code?” 字样不显示（英文版未知；“答案是？”正常）
- 道标的字体
- 高级议会 “Enter” 未翻译
- 时空之门切换大陆时大陆名称未翻译
- 通关后的白房子 “Uneasy origin matter” 未翻译
- 翡翠岛 NPC 对话有数条英文条目（标题为龙蝇、火焰抗性等）
- 巫妖物品描述中“心系抗性”不存在？（Mind and Spirit resistances 的译法待查）

## Translation quality (zh_CN)

- 单个魔法描述和其专家大师描述统一检查（进行中）
- 药剂描述快速检查
- 神器物品描述中“(加X属性)”统一为“某属性+阿拉伯数字”（参考“完美版”MM6）
- 杀伤/伤害/攻击力、技术→技能 用词统一
- MM6 开头介绍
- 方尖塔记录消失问题（MM8 缺 3#、4# 两条；6代正常、7代石圈白花不出现）

## Other game bugs (upstream)

- Noble Plate Armor 无穿戴状态图 `evt.GiveItem{1,0,880}`
- 幽灵沼泽门不对 (mm6)
- 阿拉莫斯城堡传送器 (mm6)

## Ideas

- 中文视频
- 其他语言的介绍文字

## 其他

- 把简体、繁体中文的所有图片上的“科洛尼世界”改为“恩洛斯世界”
- extract简体繁体的mm6、7需要翻译的（和英文版不同的）图片
- 似乎mm6有的需要修改，在\assets\img\dev\zh_CN\mm6里面
- 其他语言语言包生成po（`mm678 new-language` 已提供基础）、extract图片、翻译等等