
import sys
import whisper

# ---------------------------
# LRC → ASS (KTV 效果)
# ---------------------------
def whisper_to_ass(result):
    """
    使用 Whisper 输出的 segments 直接生成 ASS 字幕
    """
    header = """[Script Info]
Title: Karaoke Lyrics
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H0000FF00,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    text_lines = []

    for seg in result["segments"]:
        words = seg.get("words", [])
        if not words:
            continue

        line_start = words[0]["start"]
        line_end = words[-1]["end"]

        # 计算每个字的 \k 时间（单位: centisecond，即 1/100 秒）
        ass_lyric = ""
        text = ""
        for w in words:
            dur_cs = int((w["end"] - w["start"]) * 100)
            # \k 标签表示当前字高亮持续时间（单位 1/100 秒）
            # ass_lyric += f"{{\\k{dur_cs}}}{w['word']}"
            # \kf 表示渐变颜色
            ass_lyric += f"{{\\kf{dur_cs}}}{w['word']}"
            text += w['word']

        events.append(
            f"Dialogue: 0,{format_ass_time(line_start)},{format_ass_time(line_end)},Default,,0,0,0,,{ass_lyric}"
        )
        text_lines.append(text)

    ass_file = f"{audio_file.rsplit('.', 1)[0]}.ass"
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
    txt_file = f"{audio_file.rsplit('.', 1)[0]}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(text_lines))

    print(f"[INFO] 生成 ASS 文件: {ass_file}")
    print(f"[INFO] 生成 TXT 文件: {txt_file}")


def format_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int((sec - int(sec)) * 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


# ---------------------------
# 主流程
# ---------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py audio.mp3")
        sys.exit(1)

    audio_file = sys.argv[1]

    # Step 1: Whisper 转录 mp3，获取逐字时间戳
    print("[INFO] 加载 Whisper 模型...")
    model = whisper.load_model("medium")
    print("[INFO] 开始识别音频...")
    result = model.transcribe(audio_file, language="zh", word_timestamps=True)

    # Step 2: 生成 ASS 字幕
    whisper_to_ass(result)
