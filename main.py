import os
import sys
import shutil
import argparse
import subprocess
import whisper

from convert_chinese import convert_file
from update_lyric import replace_ass_lyrics
from create_video import image_to_video


# ---------------------------
# 工具函数
# ---------------------------

def clean_output_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def format_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int((sec - int(sec)) * 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def whisper_to_ass(result, audio_file, output_dir):
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
    segments = result["segments"]

    for i, seg in enumerate(segments):
        if i == 0 or i == len(segments) - 1:
            # whisper有时会在开头或结尾添加「詞曲 李宗盛」，有则忽略
            text = seg.get("text", "")
            if "李宗盛" in text:
                continue
        words = seg.get("words", [])
        if not words:
            continue

        line_start = words[0]["start"]
        line_end = words[-1]["end"]

        ass_lyric = ""
        text = ""

        for w in words:
            dur_cs = int((w["end"] - w["start"]) * 100)
            ass_lyric += f"{{\\kf{dur_cs}}}{w['word']}"
            text += w["word"]

        events.append(
            f"Dialogue: 0,{format_ass_time(line_start)},{format_ass_time(line_end)},Default,,0,0,0,,{ass_lyric}"
        )
        text_lines.append(text)

    base_name = os.path.splitext(os.path.basename(audio_file))[0]

    ass_path = os.path.join(output_dir, "old_lyrics.ass")
    txt_path = os.path.join(output_dir, "lyrics_raw.txt")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_lines))

    return ass_path, txt_path


# ---------------------------
# 主流程
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="歌词视频生成工具")

    parser.add_argument("--audio", required=True, help="音频路径")
    parser.add_argument("--image", required=True, help="图片路径")
    parser.add_argument("--mode", required=True, choices=["prepare", "finalize"], help="prepare=生成歌词供修改, finalize=生成最终视频")
    parser.add_argument("--st_type", required=False, choices=["s", "t"], default="s", help="s: 简体, t: 繁体")

    args = parser.parse_args()

    song_name = os.path.splitext(os.path.basename(args.audio))[0]
    output_dir = os.path.join("outputs", song_name)

    if args.mode == "prepare":
        print("=== 准备阶段 ===")
        clean_output_dir(output_dir)

        print("[1] 加载 Whisper...")
        model = whisper.load_model("medium")

        print("[2] 识别音频...")
        result = model.transcribe(args.audio, language="zh", word_timestamps=True)

        with open("temp.txt", "w", encoding="utf-8") as f:
            f.write(str(result))

        print("[3] 生成原始 ASS + TXT")
        ass_path, raw_txt_path = whisper_to_ass(result, args.audio, output_dir)

        simplified_txt_path = os.path.join(output_dir, "lyrics.txt")

        print("[4] 转换为简体/繁体中文")
        convert_file(
            txt_path=raw_txt_path,
            mode="t" if args.st_type == "t" else "s",
            output_path=simplified_txt_path
        )

        print("✅ 准备完成，请手动修改：")
        print(simplified_txt_path)
        print("修改完成后执行：")
        print(f"python main.py --audio {args.audio} --image {args.image} --mode finalize")

    elif args.mode == "finalize":
        print("=== 生成最终视频阶段 ===")

        txt_path = os.path.join(output_dir, "lyrics.txt")
        old_ass_path = os.path.join(output_dir, "old_lyrics.ass")
        final_ass_path = os.path.join(output_dir, "lyrics.ass").replace("\\", "/")

        if not os.path.exists(txt_path):
            print("❌ 未找到修正后的 lyrics.txt")
            sys.exit(1)

        print("[1] 根据修正文本更新 ASS")
        replace_ass_lyrics(
            txt_path=txt_path,
            ass_path=old_ass_path,
            output_path=final_ass_path,
            ignore_space=True
        )

        print("[2] 生成图片+音频视频")
        temp_video = os.path.join(output_dir, "temp_video.mp4")
        image_to_video(args.image, args.audio, temp_video, volume=1.0)

        print("[3] 写入歌词")
        final_video = os.path.join(output_dir, f"{song_name}.mp4")

        # ffmpeg -i audio.mp4 -vf ass=lyrics.ass output.mp4
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", temp_video,
            "-vf", f"ass={final_ass_path}", # 这里不能用"\\"作为路径分隔符，必须使用"/"
            final_video
        ])

        print("[4] 清理中间文件")

        for f in ["old_lyrics.ass", "lyrics_raw.txt", "temp_video.mp4"]:
            path = os.path.join(output_dir, f)
            if os.path.exists(path):
                os.remove(path)

        print("✅ 完成！输出文件：")
        print(final_ass_path)
        print(txt_path)
        print(final_video)


if __name__ == "__main__":
    main()
    # python main.py --audio inputs/audio.mp3 --image img/cover.png --mode prepare
