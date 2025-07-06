python
import yt_dlp

def list_formats(url: str) -> list:
    ydl_opts = { 'skip_download': True, 'quiet': True, 'force_generic_extractor': False }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    formats = []
    for f in info['formats']:
        if f.get('filesize'):
            formats.append({
                'format': f.get('format_note') or f.get('format'),
                'format_id': f['format_id'],
                'size': f['filesize'],
            })
    # отсортировать по размеру/качеству
    formats.sort(key=lambda x: x['size'])
    return formats


def download_format(url: str, fmt_id: str) -> str:
    out_template = '%(title)s.%(ext)s'
    ydl_opts = {
        'format': fmt_id,
        'outtmpl': out_template,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
    return ydl.prepare_filename(info)