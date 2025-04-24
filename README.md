# FLAC to OPUS Converter

I made this as I wanted to convert my FLAC files on my phone to OPUS to reduce file size.

## Steps
0. **IT IS ADVISABLE TO DUPLICATE YOUR MUSIC LIBRARY OR BACK IT UP BEFORE PERFORMING THIS OPERATION.**
1. Clone the repo, and copy the `.py` and `.sh` files to the root of your music repo, and then navigate to it in your terminal via `cd` or `zoxide`.
2. Run the python script in root, using `python3` or [uv](https://docs.astral.sh/uv/); the commands are `python3 conversion.py` or `uv run conversion.py`. This script parses all directories and wherever it finds a FLAC, it makes an OPUS file with the same name and metadata, and extracts the cover and ensures it has the same name as the music file.
3. Now, the original FLACs still remain. You can directly copy and run the command in `delete-flacs.sh` in your terminal, or just run the shell script. (`chmod +x delete-flacs.sh; ./delete-flacs.sh`)
4. The new folder now has OPUS files with a much smaller filesize. :)


