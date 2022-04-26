import time
import pymongo
import helpers
import datetime
import numpy as np

from fastapi import FastAPI, HTTPException


app = FastAPI()

VERSION = 1.0
cfg = helpers.load_config('cfg.ini')
client = pymongo.MongoClient(cfg['db_string'])
tidepool_db = client['tidepool']
tidepool_stats_db = client['tidepool-stats']


@app.get('/v1/')
def root():

    info = {
        'api_version': VERSION,
        'db_version': tidepool_db.command({'buildInfo': 1})['version']
    }

    return info


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

    info = {}
    for instrument in instruments:
        info[instrument] = stats[instrument]['count']

    return info


@app.get('/v1/data/{instrument}')
def instrument_data(instrument, after: float = 0.0, count: int = 1000):
    if instrument not in list_instruments():
        raise HTTPException(status_code=404, detail=f"Instrument '{instrument}' not found.")

    after = 0 if not (time.time() > after > 0) else after
    count = 1000 if not (1000 > count > 0) else count

    date = datetime.datetime.utcfromtimestamp(after)

    col = tidepool_db[instrument]
    docs = list(col.find({'time': {'$gt': date}}, {'_id': False}))

    if len(docs) == 0:
        return []

    if count > len(docs):
        count = len(docs) - 1

    indeces = np.round(np.linspace(0, len(docs) - 1, count)).astype(int)

    result = [docs[idx] for idx in indeces]

    return result
