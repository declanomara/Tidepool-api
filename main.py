import pymongo
import helpers

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
