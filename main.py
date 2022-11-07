import time
import pymongo
import datetime
import numpy as np

from fastapi import FastAPI, HTTPException
from helpers.misc import load_config
from helpers.ipc import gather_stats
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
origin_regex = r'http(s*):\/\/([a-zA-Z].)*tidepool.finance(\/[a-zA-Z]\d)*'
app.add_middleware(CORSMiddleware,
                   allow_origin_regex=origin_regex,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )

VERSION = 1.0
cfg = load_config('cfg.ini')
client = pymongo.MongoClient(cfg['db_string'])
tidepool_db = client['tidepool']
tidepool_stats_db = client['tidepool-stats']


@app.get('/v1/stats/latest/')
def all_latest_stats():
    data_rates = tidepool_stats_db['latest'].find({})

    response = {}
    for doc in data_rates:
        doc.pop('_id')
        instrument = doc.pop('instrument')

        stats = {}
        for key, value in doc.items():
            stats[key] = value

        response[instrument] = stats

    return response


@app.get('/v1/stats/latest/{instrument}')
def latest_stats(instrument):
    all_stats = all_latest_stats()

    if instrument in all_stats:
        return all_stats[instrument]

    else:
        raise HTTPException(status_code=404, detail=f"Instrument '{instrument}' not found.")


@app.get('/v1/data/instruments')
def list_instruments():
    instruments = tidepool_db.list_collection_names()
    instruments.remove('raw')

    return instruments


@app.get('/v1/data/')
def data_info():
    instruments = tidepool_db.list_collection_names()
    instruments.remove('raw')

    stats = all_latest_stats()

    data = []
    for instrument in instruments:
        data.append({
            'instrument': instrument,
            'count': stats[instrument]['count']
        })

    data.sort(key=lambda x: x['count'])

    return data


@app.get('/v1/data/{instrument}')
def instrument_data(instrument, after: float = 0.0, count: int = 1000):
    if instrument not in list_instruments():
        raise HTTPException(status_code=404, detail=f"Instrument '{instrument}' not found.")

    after = 0 if not (0 < after < time.time()) else after
    count = 1000 if not (1000 > count > 0) else count

    date = datetime.datetime.utcfromtimestamp(after)

    col = tidepool_db[instrument]
    print('Gathering documents from collection...')
    docs = list(col.find({'time': {'$gt': date}}, {'_id': False}))
    print('done.')

    if len(docs) == 0:
        return []

    if count > len(docs):
        count = len(docs) - 1

    indices = np.round(np.linspace(0, len(docs) - 1, count)).astype(int)

    result = [docs[idx] for idx in indices]

    return result


@app.get('/')
def root():
    return {'versions': ['v1']}


@app.get('/v1/')
def v1():

    info = {
        'api_version': VERSION,
        'db_version': tidepool_db.command({'buildInfo': 1})['version'],
        'endpoints': ['stats', 'data']
    }

    return info


@app.get('/v1/stats/')
def stats():
    return gather_stats()


# @app.get('/v1/stats/{type}')
# def stats_of_category(category):
#     # TODO: Move /stats/instruments to /stats/datastream
#     return stats()[category]


@app.get('/v1/stats/datastream/{instrument}')
def datastream_stats(instrument):
    return stats()['instruments'][instrument]


@app.get('/v1/stats/database')
def database_stats():
    stats = {}
    for col in tidepool_db.list_collection_names():
        stats[col] = tidepool_db[col].estimated_document_count()
    return stats


@app.get('/v1/status')
def status():
    status_dict = {
        'api': True,
        'datastream': bool(stats()),
        'trading': False
    }

    return status_dict


