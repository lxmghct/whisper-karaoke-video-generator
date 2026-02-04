from utils.st_utils import traditionalized, simplized
import os

def convert_file(txt_path: str, mode: str, output_path: str):
    """
    转换文本文件为简体或繁体。
    :param txt_path: 输入txt文件路径
    :param mode: 's' 表示转简体，'t' 表示转繁体
    :param output_path: 输出txt文件路径
    """
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"输入文件不存在：{txt_path}")

    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if mode.lower() in ('t', 'trad', 'traditional'):
        result = traditionalized(text)
        direction = "简体 → 繁体"
    elif mode.lower() in ('s', 'simp', 'simplified'):
        result = simplized(text)
        direction = "繁体 → 简体"
    else:
        raise ValueError("mode 参数必须是 's' (简体) 或 't' (繁体)")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✅ 转换完成：{direction}")
    print(f"📄 输出文件：{output_path}")

if __name__ == "__main__":
    # 示例用法
    convert_file(
        txt_path='test1/lyrics.txt',
        mode='s',  # 's' 转简体, 't' 转繁体
        output_path='test1/output.txt'
    )
