# Asset interactive experiments

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import csv
from datetime import datetime, timedelta
from math import ceil
from operator import itemgetter
from typing import *

from automate.ark import ArkSteamManager
from automate.steamapi import SteamApi
from config import ConfigFile, get_global_config

config = get_global_config()
config.settings.SkipInstall = True

arkman = ArkSteamManager(config=config)
arkman.ensureSteamCmd()
arkman.ensureGameUpdated()
arkman.ensureModsUpdated(config.mods)
loader = arkman.getLoader()

#%% Mod list

modids = set([
    # Delayed decisions
    '538986229',  # Annunaki Genesis - old but still loved and kind of working
    '632898827',  # Dino Colors Plus - adds copies of vanilla species with more colours
    '833379388',  # Pugnacia Dinos
    '916417001',  # MAP: Ebenus Astrum -                                        CHECK for dinos
    '972887420',  # Jurassic Park Expansion - massive, but updated

    # Candidates
    '1984936918',  # Marnii's Mods: Wildlife
])

#%% Conversion function


def data_from_mod(data):
    return dict(
        id=data['publishedfileid'],
        file_size=data['file_size'],
        title=data['title'],
        time_created=datetime.fromtimestamp(int(data['time_created'])),
        time_updated=datetime.fromtimestamp(int(data['time_updated'])),
        visibility=data['visibility'],
        banned=data['banned'] and (data['ban_reason'] or '<unknown ban reason>'),
        sub_count_current=data['subscriptions'],
        sub_count_lifetime=data['lifetime_subscriptions'],
        fave_count_current=data['favorited'],
        fave_count_lifetime=data['lifetime_favorited'],
        page_views=data['views'],
    )


#%% Fetch data for them all
mod_data = SteamApi.GetPublishedFileDetails(list(modids))
output_data = [data_from_mod(d) for d in mod_data]

#%% CSV export

with open('livedata/mod_requests.csv', 'wt', newline='') as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(output_data[0].keys())
    csv_writer.writerows(mod.values() for mod in output_data)

#%% Config addition

age_cutoff = datetime.utcnow() - timedelta(days=365)
for mod in sorted(output_data, key=lambda v: int(v['id'])):
    size = f"{ceil(mod['file_size']/1024.0/1024.0):>4.0f}"
    comment = f"{size} Mb, {mod['sub_count_current']:>7} subs, {mod['fave_count_current']:>6} faves"
    updated = mod['time_updated']
    if updated < age_cutoff:
        comment += f" (old? {updated.date()})"
    title = mod['title'][:40].replace('"', '\\"').replace('\n', ' ')
    title = f'"{title}"'
    print(f"{mod['id']:<10} = {title:42} # {comment}")
