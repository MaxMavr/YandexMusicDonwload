from config import *


yandex_client = ClientAsync(YANDEX_TOKEN)


print("\n\n\n\tЯндекс Скачиватель 1.0.0\n\n")


def make_song_link(song_id: str, album_id: str) -> str:
    return f'https://music.yandex.ru/album/{album_id}/track/{song_id}'


def make_dir(dir_path) -> bool:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        return True
    return False


def clear_special_char(string: str) -> str:
    special_chars = '\\/:*?"<>|.'

    for ch in special_chars:
        string = string.replace(ch, '')

    return string


def make_artists_title(artists: List[Artist]):
    return ', '.join([art.name for art in artists])


def make_feats_artists_title(artists: List[Artist]):
    return 'feat. ' + ', '.join([art.name for art in artists[1:]])


async def download_img(img_link: str) -> str:
    save_path = f'{TEMP_PATH}/{clear_special_char(img_link)}.png'
    url = 'https://' + img_link.replace('%%', '1000x1000')

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aio_open(save_path, 'wb') as img:
                        await img.write(content)
                    return save_path
    except Exception as e:
        print(f"Ошибка при загрузке обложки: {e}")
    return ''


async def decoration_song(album: Album, song: Track, song_path: str):
    audio = MP3(song_path, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    feats = make_feats_artists_title(song.artists)
    release_date = album.release_date
    img = await download_img(album.cover_uri)

    # - TIT2 - Название трека (Title)
    # - TPE1 - Исполнитель (Artist)
    # - TALB - Альбом (Album)
    # - TYER - Год (Year)
    # - TPE2 - Исполнитель альбома (Album Artist)
    # - TDRL - Дата релиза (Release Time)
    # - TCON - Жанр (Genre)
    # - TRCK - Номер трека (Track Number)
    # - WXXX - URL (Website)
    # - APIC - Вложенные изображения (Attached Picture)

    # -- TPOS - Позиция диска (Disc Number)
    # -- TCOM - Композитор (Composer)
    # -- TCOP - Авторские права (Copyright)
    # -- TDRC - Дата записи (Recording Time)
    # -- TKEY - Ключ (Musical Key)
    # -- TLEN - Длительность (Length)
    # -- USER - Пользовательские теги (User Defined Text)
    # -- COMM - Комментарии (Comments) (может иметь язык)

    audio.tags.add(TIT2(encoding=3, text=song.title))
    audio.tags.add(TALB(encoding=3, text=album.title))
    audio.tags.add(TCON(encoding=3, text=album.genre))
    audio.tags.add(TPE1(encoding=3, text=song.artists[0].name))

    if song.meta_data:
        if song.meta_data.number:
            audio.tags.add(TRCK(encoding=3, text=song.meta_data.number))

    audio.tags.add(WXXX(encoding=3, text=make_song_link(song.id, str(album.id))))

    if feats != 'feat. ':
        audio.tags.add(TPE2(encoding=3, text=feats))

    if release_date:
        date = datetime.fromisoformat(release_date)
        audio.tags.add(TYER(encoding=3, text=str(date.year)))
        audio.tags.add(TDRL(encoding=3, text=date.strftime("%Y-%m-%d")))

    if img:
        with open(img, 'rb') as img_file:
            img_data = img_file.read()

        audio.tags.add(APIC(mime='image/png', type=3, desc='Cover', data=img_data))
        os.remove(img)
    audio.save()


async def download_song(album: Union[Album, str], song: Union[Track, str]):
    if isinstance(album, str):
        album = (await yandex_client.albums(album))[0]
    if isinstance(song, str):
        song = (await yandex_client.tracks(song))[0]

    album: Album = album
    song: Track = song

    song_file_title = clear_special_char(song.title)
    album_dir_title = clear_special_char(album.title)

    song_artists_dir_title = clear_special_char(make_artists_title(song.artists))
    album_artists_dir_title = clear_special_char(make_artists_title(album.artists))

    if make_dir(f'{DOWNLOAD_PATH}/{album_artists_dir_title}'):
        print(f'\t   Создал папку артиста {album_artists_dir_title}')

    if make_dir(f'{DOWNLOAD_PATH}/{album_artists_dir_title}/{album_dir_title}'):
        print(f'\t      Создал папку альбома {album_dir_title}')

    if album_artists_dir_title != song_artists_dir_title:
        song_file_title += ' - ' + song_artists_dir_title

    save_path = f'{DOWNLOAD_PATH}/{album_artists_dir_title}/{album_dir_title}/{song_file_title}.mp3'
    if os.path.exists(save_path):
        print(f'\t         Нашёл песню {song_file_title}')
    else:
        delay = 1
        for i in range(NUMBER_DOWNLOAD_TRYING):
            try:
                await song.download_async(save_path)
                print(f'\t         Скачал песню {song_file_title}')

                await decoration_song(album, song, save_path)

                break
            except Exception as e:
                print(f"\t         Не удалось скачать.\n\t         Попытка: {i + 1}\n\t         Ошибка: {e}")

                await asyncio.sleep(delay)
                delay *= 2


async def download_album(album: str):
    album = await yandex_client.albums_with_tracks(album)

    for volume in album.volumes:
        for song in volume:
            await download_song(album, song)


async def download_artist(artist_id: str):
    artist = (await yandex_client.artists(artist_id))[0]

    for album in await artist.get_albums():
        await download_album(album.id)


async def main():
    print(f'\tСохраняет в стандартную папку загрузок\n\t\t{DOWNLOAD_PATH}\n\tДля выхода просто введи «!»')

    while True:
        link = input("\n\tВведи ссылку на трек или на альбом:\n\t")

        song = re_search(YANDEX_SONG_ID_PATTERN, link)
        album = re_search(YANDEX_ALBUM_ID_PATTERN, link)
        artist = re_search(YANDEX_ARTIST_ID_PATTERN, link)

        if song:
            await download_song(album=song.group(1), song=song.group(2))

        elif album:
            await download_album(album=album.group(1))

        elif artist:
            await download_artist(artist_id=artist.group(1))

        elif link == '!':
            break

        else:
            print("\t         _          _   _ \n\t| |    ___ | | | |\n\t| |   / _ \\\\| | | |\n\t| |__| (_) | | |_|\n\t|_____\\\\___/|_| (_)\n\n\tЧто-то херню ты ввёл! попробуй ещё разок\n",)

make_dir(DOWNLOAD_PATH)
make_dir(TEMP_PATH)

if __name__ == '__main__':
    asyncio.run(main())
