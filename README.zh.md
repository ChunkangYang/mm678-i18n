# 魔法门678语言包项目（MM678 I18N）

[English README](README.md)

本项目用于制作打了 [GrayFace（灰脸）补丁](https://grayface.github.io/mm/) 的**魔法门6、7、8**以及**魔法门678整合版（MM Merge）**的各语言语言包。

管线支持任意语言；目前已发布魔法门678整合版和魔法门8的简体、繁体中文语言包。

## 🎮 玩家

- **下载语言包**：[GitHub Releases](https://github.com/might-and-magic/mm678-i18n/releases)（含百度网盘链接见中文文档）
- **安装**：把语言包 `.exe` 放进游戏目录运行即可
- **详细说明、截图、常见问题**：[中文文档站](https://might-and-magic.github.io/mm678-i18n/zh/)

## 🛠 开发者与翻译者

一条命令完成构建：

```
pip install -e .
mm678 build        # .po -> .mo -> 游戏文本 -> postprod -> 安装包
```

开发文档（英文）：[架构与管线](docs/dev/architecture.md) ·
[构建指南](docs/dev/building.md) ·
[新增语言](docs/dev/new-language.md) ·
[发版流程](docs/dev/release.md) ·
[贡献指南](CONTRIBUTING.md) ·
[更新日志](CHANGELOG.md)

相关项目见 [github.com/might-and-magic](https://github.com/might-and-magic)：[整合版升级补丁](https://github.com/might-and-magic/mmmerge-update-patch)、[mmarch](https://github.com/might-and-magic/mmarch)、[作弊工具](https://github.com/might-and-magic/mm678-cheat) 等。

## 版权

代码使用 [MIT License](LICENSE.md)。“魔法门”商标和魔法门游戏文件版权属育碧公司，合理使用，不含游戏主体；GrayFace 的补丁和工具见[其 LICENSE 文件](https://github.com/GrayFace/Misc/blob/master/LICENSE)。
