import asyncio
import aiohttp
import asyncio
from aiofiles import open as aio_open

import os
from re import search as re_search
from json import load as json_load
from datetime import datetime

from typing import List, Union, Dict, Any
from yandex_music import ClientAsync, Artist, Album, Track

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, TCON, TRCK, WXXX, TYER, TDRL, APIC

from secret_token import YANDEX_TOKEN
YANDEX_SONG_ID_PATTERN = r'https://music\.yandex\.ru/album/(\d+)/track/(\d+)'
YANDEX_ALBUM_ID_PATTERN = r'https://music\.yandex\.ru/album/(\d+)'
YANDEX_ARTIST_ID_PATTERN = r'https://music\.yandex\.ru/artist/(\d+)'


__MAIN_DIR = f'{os.path.dirname(__file__)}'
DOWNLOAD_PATH = f'L:/video photo music/music/Скаченое'
TEMP_PATH = f'{DOWNLOAD_PATH}/temp'
