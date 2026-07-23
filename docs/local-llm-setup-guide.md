# 本地 LLM 角色扮演部署方案

> 配置: RTX 4060 8GB + i5-13500 | Windows | 用途: 本地角色扮演/小说创作

## 推荐模型（按优先级）

### 🥇 Mellum2-Thinker-12B-A2.5B (MoE) — 最适配 4060 8G
- HuggingFace: `WithinUsAI/Mellum2-Thinker.Uncensored-12B-A2.5B-gguf`
- 显存占用: ~3-4GB（12B 总量，仅 2.5B 活跃）
- 上下文: 131K
- 量化: Q4_K_M
- 拉取: `ollama run hf.co/WithinUsAI/Mellum2-Thinker.Uncensored-12B-A2.5B-gguf:Q4_K_M`

### 🥈 OpenElla-NovelWriter-8B-V2
- HuggingFace: `N-Bot-Int/OpenElla-NovelWriter-8B-V2-merged`
- 显存占用: ~5.5GB (Q4_K_M)
- 特点: 自动格式化对话 `"引号"` + 动作 `*星号*`
- 拉取: `ollama run hf.co/N-Bot-Int/OpenElla-NovelWriter-8B-V2-merged:Q4_K_M`

### 备选 12B
- **NightShade-Lotus-12B**: 暗黑奇幻，~7.5GB，4060 可跑但略卡
- **Helcyon-Grok-12B v3**: 机智幽默，对话自然

### 轻量备选
- **DECKARD-HERETIC-4B**: 256K 上下文，~3GB
- **MiniCPM5-1B-Heretic**: CPU 都能跑，128K 上下文

## 安装步骤

### 1. 安装 Ollama
- 下载: https://ollama.com (Windows exe)
- 耗时: ~2 分钟

### 2. 拉取模型
- Mellum2-12B Q4_K_M: ~7GB 下载，8-15 分钟
- 终端直接聊（跳过前端）: `ollama run <模型名>`

### 3. 安装前端（推荐 Open Dungeon）
- 仓库: https://github.com/newideas99/open-dungeon
- 备选: RP-Hub (纯 HTML 双击即用), SillyTavern (经典 RP 前端)

### 总耗时: 20-30 分钟

## 注意事项
- 8GB 显存建议上下文 ≤ 32K（长对话额外吃显存）
- 系统 RAM 建议 16GB+
- 所有推荐模型均为社区去除安全审查版本，完全本地运行
- 模型存储: `C:\Users\<用户名>\.ollama\models\`
