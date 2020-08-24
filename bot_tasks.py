import asyncio
import datetime
import os

from discord.ext import tasks

from base_bot import log
from configurations import CONFIG
from game_assets import GameAssets
from jobs.news_downloader import NewsDownloader
from team_expando import TeamExpander, update_translations
from translations import LANG_FILES


@tasks.loop(minutes=CONFIG.get('news_check_interval_minutes'), reconnect=False)
async def task_check_for_news(discord_client):
    lock = asyncio.Lock()
    async with lock:
        try:
            downloader = NewsDownloader()
            downloader.process_news_feed()
            await discord_client.show_latest_news()
        except Exception as e:
            log.error('Could not update news. Stacktrace follows.')
            log.exception(e)


@tasks.loop(seconds=CONFIG.get('file_update_check_seconds'))
async def task_check_for_data_updates(discord_client):
    filenames = LANG_FILES + ['World.json', 'User.json']
    now = datetime.datetime.now()
    modified_files = []
    for filename in filenames:
        file_path = GameAssets.path(filename)
        try:
            modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        except FileNotFoundError:
            return
        modified = now - modification_time <= datetime.timedelta(seconds=CONFIG.get('file_update_check_seconds'))
        if modified:
            modified_files.append(filename)
    if modified_files:
        log.debug(f'Game file modification detected, reloading {", ".join(modified_files)}.')
        lock = asyncio.Lock()
        async with lock:
            del discord_client.expander
            discord_client.expander = TeamExpander()
            update_translations()
