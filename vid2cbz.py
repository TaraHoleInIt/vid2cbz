#!/usr/bin/env python3

from pathlib import Path
import subprocess
import srt
import re
import os
import argparse
from pathvalidate import sanitize_filepath

def error_exit(message: str):    
    print(f"Error: {message}")
    
    remove_temporary_files()
    exit(1)


def encode_temporary_video(args):
    res = subprocess.Popen([
        "ffmpeg",
        "-y",
        "-i", args["input"],
        "-c:v", "libx264",
        "-c:s", "copy",
        "-preset", "ultrafast",
        "-g", "1",
        "-loglevel", "quiet",
        "-progress", "pipe:1",
        "temp.mkv"
    ], stdout=subprocess.PIPE, text=True)

    for line in res.stdout:
        if line.startswith("out_time="):
            line = line.strip()
            line = line.replace("\n", "")
            line = line.removeprefix("out_time=")

            print( f"\rEncoding temporary video; current position: {line}", end="", flush=True)
    
    if res.wait() != 0:
        error_exit("FAILED")

    print(" DONE")


def get_subtitles_from_video(args):
    result = subprocess.run([
        "ffmpeg",
        "-y",
        "-loglevel", "quiet",
        "-nostdin",
        "-i", args["input_unchanged"],
        "-map", f"0:s:m:language:{args['language']}",
        "-f", "srt",
        "/dev/stdout"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        error_exit("Could not extract subtitles; maybe the video doesn't have any? Specify an external subtitle file with --srt <subtitles_file>")

    return result.stdout


def parse_content(in_content: str):
    temp = in_content.replace('\n', ' ')
    temp = re.sub(r"<[^>]+>", "", temp)
    temp = re.sub(r"\{[^}]+\}", "", temp)
    temp = re.sub(r"\\[a-zA-Z0-9]+", "", temp)

    return temp


def extract_frame(args, time_offset: str):
    command_list = [
        "ffmpeg",
        "-y",
        "-ss", time_offset,
        "-i", args["input"]      
    ]

    if args["ffmpeg_video_filter"] is not None:
        command_list += [
            "-vf", args["ffmpeg_video_filter"]
        ]

    command_list += [
        "-frames:v", "1",
        "-f", "image2pipe",
        "-vcodec", "png",
        "/dev/stdout"       
    ]

    result = subprocess.run(command_list, capture_output=True, text=False)

    if result.returncode != 0:
        error_exit(f"Failed to extract frame at offset: {time_offset}")

    return result.stdout


def old_get_video_resolution(video_path: str):
    result = subprocess.run([
        "ffprobe",
        "-show_entries", "stream=width,height",
        "-select_streams", "v:0",
        "-of", "csv=p=0",
        video_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        error_exit("Failed to get video resolution")

    res_str = result.stdout
    res = res_str.split(",")

    if res is None:
        error_exit("Failed to parse video resolution")

    return int(res[0]), int(res[1])


def get_video_resolution(args):
    first_frame = extract_frame(args, "0")

    if first_frame:
        result = subprocess.run([
            "ffprobe",
            "-show_entries", "stream=width,height",
            "-select_streams", "v:0",
            "-of", "csv=p=0",
            "pipe:0"
        ], input=first_frame, capture_output=True)

        if result.returncode != 0:
            error_exit("Failed to get video resolution")

        res_str = result.stdout.decode("utf-8").strip()
        res = res_str.split(",")

        if res is None:
            error_exit("Failed to parse video resolution")

        return int(res[0]), int(res[1])


def draw_subtitle(
        output_path: Path,
        image_content,
        resolution,
        subtitle_text: str,
        args
):
    temp_text = Path("./temp.txt")

    if temp_text.write_text(subtitle_text) != len(subtitle_text):
        error_exit("Failed to write to temporary file temp.txt")

    result = subprocess.run([
        "magick",
        "-",
        "(",
        "-size", f"{resolution[0]}x",
        "-background", args["background_color"],
        "-fill", args["text_color"],
        "-font", args["font"],
        "-pointsize", str(args["font_size"]),
        "-stroke", args["stroke_color"],
        "-strokewidth", str(args["stroke_width"]),
        "-gravity", "South",
        "caption:@./temp.txt",
        ")",
        "-composite",
        "-rotate", str(args["rotate"]),
        "-resize", args["size"],
        output_path
    ], input=image_content)

    if result.returncode != 0:
        error_exit("Failed to draw subtitle using ImageMagick")


def zip_output_dir(args, images_dir):
    png_files = [f.name for f in sorted(images_dir.glob(f"*.{args['format']}"))]

    if png_files:
        result = subprocess.run([
            "zip",
            f"{args['output']}",
        ] + png_files,
            capture_output=False,
            text=True,
            cwd=images_dir.resolve()
        )

        if result.returncode != 0:
            error_exit("Failed to create CBZ archive")
    else:
        error_exit("No images in temporary directory")


def remove_temporary_files():
    temp_path = Path("./temp-vid2cbz").resolve()

    try:
        if temp_path.exists() and temp_path.is_dir():
            for i in temp_path.glob("*"):
                i.unlink()
    
        Path("./temp.txt").unlink(True)
        Path("./temp.mkv").unlink(True)
        
        if temp_path.exists():
            temp_path.rmdir()
    except Exception as e:
        print(f"remove_temporary_files failed: {e}")


def list_fonts():
    res = subprocess.run([
        "magick",
        "-list", "font"
    ], capture_output=True, text=True)

    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if "Font:" in line:
                print(line)


def list_subtitle_langs(args):
    res = subprocess.run([
        "ffprobe",
        "-loglevel", "quiet",
        "-select_streams", "s",
        "-show_entries", "stream_tags=language",
        "-of", "compact",
        args["input"]
    ], capture_output=True, text=True)

    if res.returncode != 0:
        error_exit(f"Could not get a list of subtitles")

    for line in res.stdout.splitlines():
        print(line)


def handle_command_line():
    result = {}

    parser = argparse.ArgumentParser(description = "Video to CBZ converter")

    parser.add_argument("--input", help="Input video file")
    parser.add_argument("--srt", help="Input subtitle file (srt)")
    parser.add_argument("--list-fonts", help="List available fonts", action="store_true")
    parser.add_argument("--font", help="Font to draw subtitle with")
    parser.add_argument("--font-size", help="Font size in pt")
    parser.add_argument("--stroke-color", help="Stroke color (subtitle)")
    parser.add_argument("--stroke-width", help="Stroke width (subtitle)")
    parser.add_argument("--text-color", help="Fill color (subtitle)")
    parser.add_argument("--background-color", help="Background color (subtitle)")
    parser.add_argument("--rotate", help="Rotate the final image <param> degrees")
    parser.add_argument("--list-languages", help="Lists subtitle languages in input file", action="store_true")
    parser.add_argument("--language", help="Uses subtitles for <language> when extracting subtitles from a video")
    parser.add_argument("--reencode-fast", help="Re-encodes input to a temporary file for faster processing. Uses lots of disk space.", action="store_true")
    parser.add_argument("--output", help="Output CBZ archive")
    parser.add_argument("--format", help="Output image format (default is PNG)")
    parser.add_argument("--size", help="Output image size AFTER ROTATION (ImageMagick -resize syntax; optional; defaults to 100%%)")
    parser.add_argument("--sub-seek", help="Seeks to <position> within the subtitle time range where position is one of: start, mid, end")
    parser.add_argument("--ffmpeg-video-filter", help="Passes <filter> to ffmpeg during subtitle extraction; encapsulate in quotes.")

    args = parser.parse_args()

    result["input"] = args.input
    result["input_unchanged"] = args.input
    result["srt"] = args.srt
    result["font"] = "Arial" if args.font is None else args.font
    result["font_size"] = 48 if args.font_size is None else int(args.font_size)
    result["stroke_color"] = "black" if args.stroke_color is None else args.stroke_color
    result["stroke_width"] = 2 if args.stroke_width is None else int(args.stroke_width)
    result["text_color"] = "white" if args.text_color is None else args.text_color
    result["background_color"] = "rgba(0,0,0,0.5)" if args.background_color is None else args.background_color
    result["rotate"] = 0 if args.rotate is None else int(args.rotate)
    result["language"] = "eng" if args.language is None else args.language
    result["format"] = "png" if args.format is None else args.format
    result["reencode_fast"] = args.reencode_fast
    result["list_languages"] = args.list_languages
    result["list_fonts"] = args.list_fonts
    result["size"] = "100%" if args.size is None else args.size
    result["sub_seek"] = "start" if args.sub_seek is None else args.sub_seek
    result["ffmpeg_video_filter"] = args.ffmpeg_video_filter

    if args.list_fonts is True:
        print("Listing fonts:")

        list_fonts()
        exit(0)

    if args.list_languages is True:
        if result["input"] is None:
            error_exit("--list-languages requires --input")

        print(f"Listing subtitle languages within {result['input']}")

        list_subtitle_langs(result)
        exit(0)

    if args.input is None:
        error_exit("Input video not specified")

    result["output"] = Path(replace_file_extension(
        sanitize_filepath(Path(result["input"]).resolve()), 
        ".cbz"
    ))

    if result["output"].exists():
        while True:
            print(f"Output file {result['output']} already exists; replace it? >", end="")
            response = input().lower()

            if response.startswith("y"):
                result['output'].unlink(True)
                break
            elif response.startswith("n"):
                exit(0)

    return result


def get_subtitles(args):
    has_srt = args["srt"] is not None
    srt_content = ""
    subs = None

    if has_srt:
        srt_path = Path(args["srt"])

        try:
            srt_content = srt_path.read_text()
        except Exception as e:
            error_exit(f"Could not open srt file {args['srt']} for reading; Exception = {e}")
    else:
        srt_content = get_subtitles_from_video(args)

    try:
        subs = list(srt.parse(srt_content))
    except Exception as e:
        error_exit(f"Could not parse subtitles; {e}")

    return subs


def update_progress(pct, args):
    print(f"\rConverting {args['input_unchanged']} to CBZ archive [{pct}%]", end="", flush=True)


def replace_file_extension(file_path: Path, new_extension: str):
    return os.path.splitext(file_path)[0] + new_extension


if __name__ == "__main__":
    frame_counter = 0
    sub_index = 0

    args = handle_command_line()

    if args["reencode_fast"]:
        encode_temporary_video(args)
        args["input"] = "temp.mkv"

    subtitles = get_subtitles(args)
    res = get_video_resolution(args)

    temp_path = Path("./temp-vid2cbz").resolve()
    temp_path.mkdir(exist_ok=True)

    for i in subtitles:
        seek_pos = i.start

        if args["sub_seek"] == "mid":
            seek_pos = (i.end - i.start) / 2
        elif args["sub_seek"] == "end":
            seek_pos = i.end

        frame = extract_frame(args, str(seek_pos))

        if frame:
            out_file = Path(f"temp-vid2cbz/{frame_counter:06d}.{args['format']}")
            out_content = parse_content(i.content)

            update_progress(int((sub_index / len(subtitles)) * 100.0), args)
            draw_subtitle(
                out_file,
                frame,
                res,
                out_content,
                args
            )

            frame_counter += 1
            sub_index += 1

    zip_output_dir(args, temp_path)
    remove_temporary_files()

    print("Complete!")
