from difflib import SequenceMatcher

def find_misalignment_intervals(ref, pred, min_match_len=3, offset_tolerance=5):
    """
    查找两个歌词字符串中的错位区间。

    参数：
        ref (str): 正确歌词
        pred (str): 识别歌词
        min_match_len (int): 最小匹配子串长度，过滤掉太短的偶然匹配
        offset_tolerance (int): 最大允许的匹配位置差，避免歌词重复误判

    返回：
        list[dict]: 错位区间列表，例如：
        [
            {"start_ref": 50, "end_ref": 120, "start_pred": 48, "end_pred": 118, "offset": -2},
            ...
        ]
    """
    matcher = SequenceMatcher(None, ref, pred)
    matches = matcher.get_matching_blocks()

    intervals = []
    prev_offset = 0

    for i, match in enumerate(matches):
        if match.size < min_match_len:
            continue

        offset = match.b - match.a

        # 跳过明显不对应的（比如副歌重复太远）
        if abs(offset) > offset_tolerance:
            continue

        if offset != prev_offset:
            last_match = matches[i - 1] if i > 0 else {"a": 0, "b": 0, "size": 0}
            inteval = {
                "start_ref": last_match.a + last_match.size,
                "start_pred": last_match.b + last_match.size,
                "end_ref": match.a,
                "end_pred": match.b,
                "offset": offset - prev_offset,
                "lyric_ref": ref[last_match.a + last_match.size: match.a],
                "lyric_pred": pred[last_match.b + last_match.size: match.b],
            }
            intervals.append(inteval)
            prev_offset = offset

    return intervals


if __name__ == "__main__":
    ref_lyric = "这是正确的歌词，用于测试错位检测功能。"
    pred_lyric = "这是错误的歌词，用于测试检测功能。"

    intervals = find_misalignment_intervals(ref_lyric, pred_lyric)
    for interval in intervals:
        print(interval)