import argparse
from moviepy.editor import ImageClip, AudioFileClip

def image_to_video(image_path, audio_path, output_path="output.mp4", volume=1.0):
    """
    生成视频：单张图片 + 背景音乐
    :param image_path: 图片路径 (jpg/png/jpeg)
    :param audio_path: 音频路径 (mp3)
    :param output_path: 输出视频路径 (默认 output.mp4)
    :param volume: 音量大小 (1.0为原音量，0.5为一半音量)
    """
    # 加载音频
    audio = AudioFileClip(audio_path).volumex(volume)
    duration = audio.duration  # 音频持续时间
    print(duration)

    # 创建图片视频片段（持续时间与音频相同）
    # clip = ImageClip(image_path, duration=duration)
    clip = ImageClip(image_path).resize(height=480, width=720).set_duration(duration)

    # 设置视频的音频
    video = clip.set_audio(audio)

    # 导出视频
    video.write_videofile(
        output_path,
        fps=24,          # 帧率
        # codec="libx264",
        # audio_codec="aac",
        # ffmpeg_params=[
        #     "-pix_fmt", "yuv420p",
        #     "-movflags", "+faststart"
        # ]
    )

    print(f"✅ 视频已生成: {output_path}")
    # print(f"🎵 音频长度: {duration:.2f} 秒")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图片 + 音频生成视频")
    parser.add_argument("--image", required=True, help="输入图片路径 (jpg/png/jpeg)")
    parser.add_argument("--audio", required=True, help="输入音频路径 (mp3)")
    parser.add_argument("--output", default="output.mp4", help="输出视频文件名 (默认: output.mp4)")
    parser.add_argument("--volume", type=float, default=1.0, help="音量大小 (默认: 1.0，0.5为一半音量)")

    args = parser.parse_args()
    image_to_video(args.image, args.audio, args.output, args.volume)

# example usage:
# python create_video.py --image img/cover.png --audio mp3/audio.mp3 --output mp4/video.mp4 --volume 1