"""
DDP mastodon module
"""

from pathlib import Path
import logging
import zipfile

#import pyodide_http
#pyodide_http.patch_all()  # Patch all libraries
#import requests

import pandas as pd
#from bs4 import SoupStrainer, BeautifulSoup

import port.unzipddp as unzipddp
import port.helpers as helpers
from port.validate import (
    DDPCategory,
    StatusCode,
    ValidateInput,
    Language,
    DDPFiletype,
)

logger = logging.getLogger(__name__)

DDP_CATEGORIES = [
    DDPCategory(
        id="json_en",
        ddp_filetype=DDPFiletype.JSON,
        language=Language.EN,
        known_files=[
            "actor.json",
            "bookmarks.json",
            "likes.json",
            "outbox.json"
        ],
    ),
]

STATUS_CODES = [
    StatusCode(id=0, description="Valid DDP", message=""),
    StatusCode(id=1, description="Not a valid DDP", message=""),
    StatusCode(id=2, description="Bad zip", message=""),
]

def validate_zip(file: Path) -> ValidateInput:
    """
    Validates the input of a Mastodon submission
    """

    validation = ValidateInput(STATUS_CODES, DDP_CATEGORIES)

    try:
        paths = []
        with zipfile.ZipFile(file, "r") as zf:
            for f in zf.namelist():
                p = Path(f)
                if p.suffix in (".json"):
                    logger.debug("Found: %s in zip", p.name)
                    paths.append(p.name)

        valid = validation.infer_ddp_category(paths)
        if valid:  # pyright: ignore
            validation.set_status_code_by_id(0)
        else: 
            validation.set_status_code_by_id(1)

    except zipfile.BadZipFile:
        validation.set_status_code(2)

    return validation



def likes_to_df(mastodon_zip: str):

    b = unzipddp.extract_file_from_zip(mastodon_zip, "likes.json")
    likes = unzipddp.read_json_from_bytes(b)

    datapoints = []
    out = pd.DataFrame()

    try:
        links = likes["orderedItems"]
        '''
        for link in links:
            page = requests.get(link)
            meta_tags = BeautifulSoup(page, "html.parser", parse_only=SoupStrainer("meta"))
            user = meta_tags.find(property="profile:username").content
            time = meta_tags.find(property="og:published_time").content
            time = helpers.convert_unix_timestamp(time)

            datapoint = {
                "like_user": user,
                "time": time,
            }
            datapoints.append(datapoint)
        
        out = pd.DataFrame(datapoints)
        '''
        out = pd.DataFrame(links, columns=['links'])
    except Exception as e:
        logger.error("Data extraction error: %s", e)
        
    return out
