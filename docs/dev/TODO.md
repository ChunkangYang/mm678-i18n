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
- (可选)FR 包做了、我们从未做过的:MM6 法术书页签 `sb*000a` 12 张、
  `bt_16x/32x` 分辨率按钮 4 张、`layout.pcx`/`sprites.pcx`

## Pipeline / packaging

- NSIS 安装包 Delete 列表补旧布局残留(`10 LocZHCN.EnglishD.lod`、
  `z10 LocZHCN.icons.lod`、`10 LocLANG.EnglishT` 时代文件)——2026-08 改为
  `zz LocZHCN.{T,D,icons}.lod` 三件套后,旧包升级需清理
- `config/versions.py` 的 merge 版本号更新到最新基线
- 安装包清理其他语言的残留文件
- 整合版补丁装不进 MM8，但 MM8 补丁能装进整合版——应让后者也不可以
- 视频本地化：`assets/video/zh_CN` → `Anims/10 LocZHCN.Magicdod.vid`
- `%` 转义（`#, python-format`）研究
- 比较 Merge 的 rodril 分支与 master 分支的脚本差异

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
- 天气效果无法立即关闭

## Ideas

- 魔法门7、6的灰脸补丁简体中文汉化
- 中文视频
- 其他语言语言包自动生成（`mm678 new-language` 已提供基础）
- 其他语言的介绍文字
