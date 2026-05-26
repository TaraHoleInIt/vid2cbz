# Video to CBZ Converter

This is a command-line video processing tool that converts videos into a CBZ archive format containing frames with 
overlaid subtitles.

Python is not my strong suit, so this program is what it is (bad).

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

To convert a video to a CBZ file, run the following command in your terminal:

```bash
python vid2cbz.py --input <input_video> --srt <input_subtitles> --output <output_cbz> --font <font> --font-size <font_size> 
--stroke-color <stroke_color> --text-color <text_color> --background-color <background_color> --rotate 
<rotate_angle> --size <output_size> --sub-seek <seek_pos> --ffmpeg-video-filter <filters>
```

Replace the placeholders with your desired values:

- `<input_video>`: Path to the input video file.
- `<input_subtitles>`: Path to subtitles file; optional if video has embedded subtitles.
- `<output_cbz>`: (OPTIONAL) Output CBZ archive name and path.
- `<font>`: (OPTIONAL) Font for subtitle text (default is Arial).
- `<font_size>`: (OPTIONAL) Font size in points (default is 48).
- `<stroke_color>`: (OPTIONAL) Subtitle stroke color (default is black).
- `<text_color>`: (OPTIONAL) Subtitle fill color (default is white).
- `<background_color>`: (OPTIONAL) Subtitle background color (default is rgba(0,0,0,0.5)).
- `<rotate_angle>`: (OPTIONAL) Rotate the final image by this angle (default is 0 degrees).
- `<output_size>`: (OPTIONAL) Scale the final image to this size (AFTER rotation; passed to ImageMagick as -resize; use ImageMagick size formatting).
- `<seek_pos>`: (OPTIONAL) Where to seek within the subtitle range; values are: start, mid, and end.
- `<filters>`: (OPTIONAL) Filters passed to -vf parameter in ffmpeg during frame extraction.


You can optionally include these flags to customize your output:

- `--reencode-fast`: Re-encodes input to a temporary file for faster processing. Uses lots of disk space.
- `--list-fonts`: Lists available fonts.
- `--list-languages`: Lists subtitle languages within the input video.

For more details about each flag, run:

```bash
python vid2cbz.py --help
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
