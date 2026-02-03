import re

def ass_to_txt(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_events = False
    lyrics = []

    for line in lines:
        line = line.strip()
        # 进入 Events 区域
        if line.startswith("[Events]"):
            in_events = True
            continue

        if not in_events:
            continue

        # 只处理 Dialogue 行
        if line.startswith("Dialogue:"):
            # ASS 格式中 "Text" 字段在第9个逗号后（前面有9个逗号）
            parts = line.split(",", 9)
            if len(parts) < 10:
                continue
            text = parts[9]

            # 去掉花括号特效，如 {\kf50}
            text = re.sub(r"\{.*?\}", "", text)

            # 去掉首尾空格
            text = text.strip()

            if text:
                lyrics.append(text)

    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lyrics))

    print(f"提取完成！共 {len(lyrics)} 行歌词，已保存到 {output_path}")

# 使用示例
if __name__ == "__main__":
    input_file = "何时/audio.ass"   # 输入文件名
    output_file = "何时/lyrics.txt"   # 输出文件名
    ass_to_txt(input_file, output_file)
