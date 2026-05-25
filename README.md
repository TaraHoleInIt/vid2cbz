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
python video_to_cbz.py --input <input_video> --output <output_cbz> --font <font> --font-size <font_size> 
--stroke-color <stroke_color> --text-color <text_color> --background-color <background_color> --rotate 
<rotate_angle>
```

Replace the placeholders with your desired values:

- `<input_video>`: Path to the input video file.
- `<output_cbz>`: Output CBZ archive name and path.
- `<font>`: Font for subtitle text (default is Arial).
- `<font_size>`: Font size in points (default is 48).
- `<stroke_color>`: Subtitle stroke color (default is black).
- `<text_color>`: Subtitle fill color (default is white).
- `<background_color>`: Subtitle background color (default is rgba(0,0,0,0.5)).
- `<rotate_angle>`: Rotate the final image by this angle (default is 0 degrees).

You can optionally include these flags to customize your output:

- `--reencode-fast`: Re-encodes input to a temporary file for faster processing. Uses lots of disk space.
- `--list-fonts`: Lists available fonts.
- `--list-languages`: Lists subtitle languages within the input video.

For more details about each flag, run:

```bash
python video_to_cbz.py --help
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
