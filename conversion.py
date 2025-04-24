import os
import sys
import subprocess
import logging
from pathlib import Path
from functools import partial
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import argparse

# logging (for confirmation)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_cover(flac_path: Path, dry_run: bool):
    """
    Extract embedded cover art (if present) to a .jpg alongside the FLAC file.
    """
    cover_jpg = flac_path.with_suffix('.jpg')
    if cover_jpg.exists():
        logging.debug(f"Cover image already exists, skipping: {cover_jpg}")
        return False

    cmd = [
        'ffmpeg',
        '-hide_banner', '-loglevel', 'warning',
        '-i', str(flac_path),
        '-map', '0:v?',      
        '-c:v', 'mjpeg',      
        str(cover_jpg)
    ]
    logging.info(f"Extracting cover art: {flac_path} → {cover_jpg}")
    logging.debug(" ".join(cmd))

    if dry_run:
        logging.info(f"[DRY RUN] Would extract cover art to {cover_jpg}")
        return True

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except Exception as e:
        logging.warning(f"Cover extraction failed for {flac_path}: {e}")
        return False


def convert_file(flac_path: Path, bitrate: str, dry_run: bool) -> tuple:
    """
    Transcode a single FLAC file to Opus, preserving metadata.
    Returns (converted, skipped, error).
    """
    opus_path = flac_path.with_suffix('.opus')

    # ignoring macOS metadata files (yes, mac dev woes)
    if flac_path.name.startswith('._'):
        logging.debug(f"Skipping metadata file: {flac_path.name}")
        return (False, True, False)

    # Skip if already converted (because iterations)
    if opus_path.exists():
        logging.debug(f"Already exists, skipping: {opus_path}")
        return (False, True, False)

    # cover extraction
    extract_cover(flac_path, dry_run)

    # ffmpeg command for audio conversion
    cmd = [
        'ffmpeg',
        '-hide_banner', '-loglevel', 'warning',
        '-f', 'flac',
        '-analyzeduration', '10000000',
        '-probesize', '20000000',
        '-i', str(flac_path),
        '-map', '0:a',            # audio streams 
        '-map_metadata', '0',     # copy metadata
        '-c:a', 'libopus',        # encode audio 
        '-b:a', bitrate,
        '-vbr', 'on',
        '-threads', '0',          # auto-thread inside ffmpeg
        str(opus_path)
    ]

    logging.info(f"Converting: {flac_path}")
    logging.debug(" ".join(cmd))

    if dry_run:
        logging.info(f"[DRY RUN] Would convert {flac_path} → {opus_path}")
        return (True, False, False)

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Successfully created: {opus_path}")
        return (True, False, False)
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error ({flac_path}): returncode={e.returncode}")
        if e.stderr:
            logging.error(f"  stderr: {e.stderr.strip()}")
        return (False, False, True)
    except Exception as e:
        logging.error(f"Unexpected error ({flac_path}): {e}")
        return (False, False, True)


def gather_flac_files(root: Path) -> list:
    """Recursively collect all .flac files under the root directory."""
    return list(root.rglob('*.flac'))


def main():
    parser = argparse.ArgumentParser(description="Parallel FLAC → Opus transcoder with cover art extraction")
    parser.add_argument('root', type=Path, help="Root directory to scan for .flac files")
    parser.add_argument('-b', '--bitrate', default="192k", help="Opus bitrate (e.g. 128k, 192k)")
    parser.add_argument('-j', '--jobs', type=int, default=multiprocessing.cpu_count(),
                        help="Number of parallel ffmpeg jobs (default: number of CPUs)")
    parser.add_argument('--dry-run', action='store_true', help="Show actions without running ffmpeg")
    args = parser.parse_args()

    if not args.root.is_dir():
        logging.error(f"Directory not found: {args.root}")
        sys.exit(1)

    # files parser
    flac_list = gather_flac_files(args.root)
    total = len(flac_list)
    logging.info(f"Found {total} .flac files under {args.root}")
    if total == 0:
        return

    converted = skipped = errors = 0
    worker = partial(convert_file, bitrate=args.bitrate, dry_run=args.dry_run)

    # Parallel execution (USES 100% CPU)
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(worker, flac): flac for flac in flac_list}
        for future in as_completed(futures):
            flac = futures[future]
            try:
                did_convert, did_skip, did_error = future.result()
                if did_convert:
                    converted += 1
                elif did_skip:
                    skipped += 1
                elif did_error:
                    errors += 1
            except Exception as exc:
                errors += 1
                logging.error(f"Worker exception for {flac}: {exc}")

    # Summary
    logging.info(f"Conversion complete: converted={converted}, skipped={skipped}, errors={errors}")
    if errors > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
