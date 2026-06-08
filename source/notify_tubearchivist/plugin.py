import logging
import requests
from pathlib import Path
from unmanic.libs.unplugins.settings import PluginSettings

class Settings(PluginSettings):
    settings = {
        "ta_url": "",
        "ta_token": "",
    }
    form_settings = {
        "ta_url": {
            "label": "TubeArchivist URL",
        },
        "ta_token": {
            "label": "TubeArchivist API Token",
        },
    }

def ta_video_exists(ta_url: str, ta_token: str, video_id: str) -> bool:
    headers = {
        "Authorization": f"Token {ta_token}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(f"{ta_url}/api/video/{video_id}", headers=headers, timeout=10)
        return r.status_code = 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to TubeArchivist API: {e}")
        return False

def notify_ta(ta_url: str, ta_token: str, video_id: str):
    headers = {
        "Authorization": f"Token {ta_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "video": video_id
    }

    try:
        r = requests.post(f"{ta_url}/api/refresh/", json=payload, headers=headers, timeout=10)

        if r.status_code = 200:
            logger.info(f"Successfully triggered TubeArchivist refresh for {video_id}")
        else:
            logger.error(f"Failed to trigger TubeArchivist refresh. Status code: {r.status_code}, Response: {r.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to TubeArchivist API: {e}")

def on_postprocessor_task_results(data):
    if not data.get('destination_files'):
        logging.info('No destination files')
        return data

    settings = Settings(library_id=data.get('library_id'))
    ta_url = settings.get_setting('ta_url')
    ta_token = settings.get_setting('ta_token')

    if not ta_url or not ta_token:
        logging.warning("TubeArchivist URL/API Token is not configured, skipping")
        return data

    for file in data.get('destination_files'):
        video_id = Path(file).stem

        if ta_video_exists(ta_url, ta_token, video_id):
            notify_ta(ta_url, ta_token, video_id)
        else:
            logging.warning(f"Video {video_id} does not exist on TubeArchivist")

    return data
