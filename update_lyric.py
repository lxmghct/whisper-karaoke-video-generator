import re
from io import StringIO
from utils.sequence_diff import find_misalignment_intervals


class AssTime:
    def __init__(self, arg):
        """
        time_str: 字符串，格式为 "时:分:秒.百分秒"，例如 "0:00:12.41
        """
        if isinstance(arg, int):
            self.total_hundredths = arg
        else:
            hours, minutes, rest = arg.split(':')
            seconds, hundredths = rest.split('.')
            self.total_hundredths = (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 100 + int(hundredths)

    def add(self, add_time):
        self.total_hundredths += add_time

    def __str__(self):
        total_seconds = self.total_hundredths // 100
        remaining_hundredths = self.total_hundredths % 100

        hours = total_seconds // 3600
        remaining_seconds = total_seconds % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        return f"{hours}:{minutes:02d}:{seconds:02d}.{remaining_hundredths:02d}"
    
    def copy(self):
        return AssTime(self.total_hundredths)


print(AssTime("0:01:23.45"))


def replace_ass_lyrics(txt_path, ass_path, output_path, ignore_space=True):
    """
    ignore_space: 是否忽略原歌词中的空格
    """
    # 读取修改后的 txt 歌词
    with open(txt_path, 'r', encoding='utf-8') as f:
        txt_lines = [line.strip() for line in f.readlines() if line.strip()]

    # 读取原始 ass 文件
    with open(ass_path, 'r', encoding='utf-8') as f:
        ass_lines = f.readlines()

    # 找到 [Events] 段起始索引
    event_start = None
    for i, line in enumerate(ass_lines):
        if line.strip().startswith('[Events]'):
            event_start = i
            break
    if event_start is None:
        raise ValueError("ASS 文件中未找到 [Events] 段")

    # 分离出元信息和歌词部分
    header = ass_lines[:event_start + 2]
    dialogue_lines = ass_lines[event_start + 2:]

    # 格式化旧歌词 [[word, dialogue_time_row, tag]]
    lyric_words = []
    # 存储每个dialogue的时间[start_time, end_time]
    dialogue_time_rows = []

    for i, line in enumerate(dialogue_lines):
        parts = line.strip().split(',', 9)
        dialogue_time_rows.append([AssTime(parts[1]), AssTime(parts[2])])
        lyric_part = parts[9].strip()
        j = 0
        lyric_len = len(lyric_part)
        current_lyric_word = [None, i, None]
        while j < lyric_len:
            c = lyric_part[j]
            j += 1
            if c == ' ':
                if ignore_space:
                    continue
                if current_lyric_word[2] is None:
                    lyric_words[-1][0] += ' '
                elif current_lyric_word[0] is None:
                    current_lyric_word[0] = ' '
                else:
                    current_lyric_word[0] += ' '
                continue
            if c == '{':
                t = j
                while j < lyric_len and lyric_part[j] != '}':
                    j += 1
                current_lyric_word[2] = lyric_part[t: j]
                j += 1
                continue
            current_lyric_word[0] = c if current_lyric_word[0] is None else current_lyric_word[0] + c
            lyric_words.append(current_lyric_word)
            current_lyric_word = [None, i, None]
   
   
    # 将新旧歌词全部转为字符串进行对比，找出错位区间，先去除所有空白字符
    old_lyric_str = ''.join(w[0] for w in lyric_words).replace(' ', '')
    new_lyric_str = ''.join(line.replace(' ', '') for line in txt_lines)
    print(f'原歌词总字数（不含空格）: {len(old_lyric_str)}')
    print(f'新歌词总字数（不含空格）: {len(new_lyric_str)}')
    if len(old_lyric_str) != len(new_lyric_str):
        print('⚠️ 警告：新旧歌词字数不匹配，可能导致时间信息错乱！')
        intervals = find_misalignment_intervals(
            ref=old_lyric_str,
            pred=new_lyric_str,
            min_match_len=3,
            offset_tolerance=10
        )
        print('错位区间列表(括号里表示字在歌词中的位置):')
        for i, inteval in enumerate(intervals):
            print(f'  {i + 1}. 新歌词({inteval["start_pred"]}): {inteval["lyric_pred"]}')
            print(f'     原歌词({inteval["start_ref"]}): {inteval["lyric_ref"]}')
        print('请确认是否无视这些错位区间并继续？')
        temp = input('输入 y 继续，其他键退出: ')
        if temp.lower() != 'y':
            print('已退出。')
            return
    # 歌词替换
    word_index = 0
    new_word_rows = []
    total_words = len(lyric_words)
    for line in txt_lines:
        row = []
        new_word_rows.append(row)
        for c in line:
            if word_index >= total_words:
                break
            if c == ' ':
                if lyric_words[word_index][0][0] != ' ' and lyric_words[word_index - 1][0][-1] != ' ':
                    lyric_words[word_index - 1][0] += ' '
                continue
            if lyric_words[word_index][0][0] == ' ':
                lyric_words[word_index][0] = ' ' + c
            elif lyric_words[word_index][0][-1] == ' ':
                lyric_words[word_index][0] = c + ' '
            else:
                lyric_words[word_index][0] = c
            row.append(lyric_words[word_index])
            word_index += 1

    # 生成新的 dialogue 行
    dialogue_example_line = dialogue_lines[0]
    example_parts = dialogue_example_line.strip().split(',', 9)

    new_dialogues = []

    word_index = 0
    for i, word_row in enumerate(new_word_rows):
        if not word_row:
            continue

        # 计算 start_time
        start_time_row_index = word_row[0][1]
        t = word_index - 1
        while t >= 0 and lyric_words[t][1] == start_time_row_index:
            t -= 1
        if t < word_index - 1:
            temp_start = dialogue_time_rows[lyric_words[t + 1][1]][0].copy()
            for p in range(t + 1, word_index):
                tag = lyric_words[p][2]
                if tag:
                    temp_start.add(int(re.search(r'\d+', tag).group()))
            start_time = temp_start
        else:
            start_time = dialogue_time_rows[start_time_row_index][0]
        
        # 计算 end_time (如果最后一个字恰好是该行最后一个字，则取该行end_time而非start_time加偏移量)
        word_index += len(word_row)
        end_time_row_index = word_row[-1][1]
        if word_index < total_words and lyric_words[word_index][1] > end_time_row_index:
            end_time = dialogue_time_rows[end_time_row_index][1]
        else:
            # 旧歌词的end_time会稍有偏移量，故采用start_time加偏移量的方式计算
            t = 2
            while t < len(word_row) and lyric_words[word_index - t][1] == end_time_row_index:
                t += 1
            temp_end = dialogue_time_rows[lyric_words[word_index - t][1]][0].copy()
            for p in range(word_index - t, word_index):
                tag = lyric_words[p][2]
                if tag:
                    temp_end.add(int(re.search(r'\d+', tag).group()))
            end_time = temp_end

        # 生成新的 lyric 部分
        new_lyric_part_io = StringIO()
        for w in word_row:
            if w[2]:
                new_lyric_part_io.write('{' + w[2] + '}')
            new_lyric_part_io.write(w[0])

        example_parts[1] = str(start_time)
        example_parts[2] = str(end_time)
        example_parts[9] = new_lyric_part_io.getvalue()

        new_dialogue_line = ','.join(example_parts) + '\n'
        new_dialogues.append(new_dialogue_line)

    # 生成新的 ASS 内容
    new_ass = header + new_dialogues

    # 写入新文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(new_ass)

    print(f'✅ 已生成新的 ASS 文件: {output_path}')


# 示例用法
# replace_ass_lyrics(
#     txt_path='new_text.txt',
#     ass_path='audio.ass',
#     output_path='output_fixed.ass',
#     ignore_space=False
# )
    
def replace_ass(song_name):
    """
    默认路径:
    歌词文本路径: {song_name}/lyrics.txt
    歌词ass路径: {song_name}/old_lyrics.ass
    输出路径: {song_name}/lyrics.ass
    """
    replace_ass_lyrics(
        txt_path=f'{song_name}/lyrics.txt',
        ass_path=f'{song_name}/old_lyrics.ass',
        output_path=f'{song_name}/lyrics.ass',
        ignore_space=True
    )


if __name__ == '__main__':
    # replace_ass('何时')
    replace_ass('only_my_railguns')
