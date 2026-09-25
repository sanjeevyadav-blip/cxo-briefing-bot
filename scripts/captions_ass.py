"""
Caption track for the slide videos: the spoken words, a few at a time, in
the dark band at the bottom of each slide. Timing comes from ass_slides.
"""
from ass_slides import ass_time, captions, clean

_HEAD = "\n".join([
    "[Script Info]", "ScriptType: v4.00+",
    "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
    "[V4+ Styles]",
    "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,"
    "Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,"
    "Encoding",
    "Style: Cap,DejaVu Sans,27,&H00F5F5F5,&H00000000,&H0,0,1,1,0,2,"
    "140,140,24,1",
    "Style: Who,DejaVu Sans,19,&H00A0A0A0,&H0,&H0,1,1,0,0,1,60,60,30,1",
    "", "[Events]",
    "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    "",
])


def write(timeline, path):
    lines = []
    for s, t, text, spk in captions(timeline):
        a, b = ass_time(s), ass_time(t)
        lines.append(f"Dialogue: 1,{a},{b},Cap,,0,0,0,,{clean(text)}")
        lines.append(f"Dialogue: 1,{a},{b},Who,,0,0,0,,HOST {spk}")
    path.write_text(_HEAD + "\n".join(lines) + "\n")
