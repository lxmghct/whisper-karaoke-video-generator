# Whisper Karaoke Video Generator

## 1. 简介
一个基于 OpenAI Whisper 的歌词视频生成工具。

本项目可以：

- 自动识别音频生成逐字时间戳
- 生成 KTV 风格 .ass 歌词字幕
- 支持繁简体转换
- 支持人工修正歌词并自动重新对齐时间
- 生成 图片 + 音频 的视频
- 自动将歌词嵌入视频

最终生成一个带逐字高亮效果的卡拉 OK 视频。

示例如下：
![示例](doc/lyrics_example.gif)

## 2. 功能流程
完整流程分为两个阶段：

1. prepare 阶段（生成歌词供修改）
    - Whisper 识别音频
    - 生成原始 .ass 和 .txt
    - 自动将歌词转为简体
    - 等待人工修改歌词

2. finalize 阶段（生成最终视频）
    - 根据人工修正的 txt 更新 ass 时间轴
    - 生成 图片 + 音频 视频
    - 使用 ffmpeg 写入字幕
    - 清理中间文件

## 3. 环境配置
- Python >= 3.8
- ffmpeg

```
pip install -r requirements.txt
```


## 4. 使用方法
### 4.1. 生成歌词（准备阶段）
```
# 可选参数：--st_type s, 简体: s(默认), 繁体: t
python main.py --audio your_song.mp3 --image cover.jpg --mode prepare
```
Whisper 使用 medium 模型，可在 main.py 中自行修改为 small / large。

输出目录：
```
outputs/歌名/
    old_lyrics.ass
    lyrics_raw.txt
    lyrics.txt   ← 请修改这个文件
```
请检查 lyrics.txt 中的歌词是否正确，可以手动修改。

可以任意添加/删除空格和换行，但是除了空白字符以外的其他字的总字数不能变化。

如果确实修改后导致总字数变化了（添加或删除了某些字），程序会给出错位提示，可选择是否继续，此时如果需要继续，请同步修改 old_lyrics.ass 中的对应片段，否则有可能会出现问题。

### 4.2. 生成最终视频
修改完成后运行：
```
python main.py --audio your_song.mp3 --image cover.jpg --mode finalize
```
也可以使用自定义的视频（时长需大于等于音频时长）：
```
python main.py --audio your_song.mp3 --video my_video.mp4 --mode finalize
```

最终输出：
```
outputs/歌名/
    lyrics.txt        ← 人工修正后的歌词
    lyrics.ass        ← 最终字幕
    歌名.mp4          ← 带歌词视频
```

## 4.3. 直接给视频插入歌词
```
python main.py --ass inputs/lyrics.ass --video inputs/video.mp4
```

## 5. 项目结构
```
.
├── main.py
├── create_video.py
├── update_lyrics.py
├── convert_chinese.py
├── utils/
│   ├── sequence_diff.py
│   └── st_utils.py
└── outputs/
```

# 6. 核心模块说明
- main.py
    + 主程序入口，负责：
    + 调用 Whisper
    + 管理流程
    + 调用各工具模块
    + 调用 ffmpeg 写入字幕

- update_lyrics.py
    + 对比原始 Whisper 歌词与人工修正歌词
    + 自动计算错位区间
    + 重新分配逐字时间
    + 生成新的 .ass 文件
    + 增删空格和换行，修改但不增删歌词字数，不会破坏整体时间轴。

- convert_chinese.py
    + 简繁转换

- create_video.py
    + 使用 moviepy 根据单张图片生成匹配音频时长的视频
