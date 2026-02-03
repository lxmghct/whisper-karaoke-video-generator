https://aegisub.org/zh-cn/docs/latest/attaching_subtitles_to_video/


LoadPlugin("c:\program files\aegisub\csri\vsfilter.dll")
AVISource("c:\projects\project1\video\mycoolvideo.avi")
TextSub("c:\projects\project1\subs\mainsubtitles.ass")
TextSub("c:\projects\project1\subs\endkaraoke.ass")


ffmpeg -i audio.mp4 -vf ass=lyrics.ass output.mp4
