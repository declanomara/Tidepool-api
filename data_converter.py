import helpers
import pymongo
import datetime
import numpy as np

from pathlib import Path


def generate_file_path(instrument: str, before: datetime.datetime, after: datetime.datetime):
    if before is None and after is None:
        return f'bin/{instrument}-all.bin'

    if before is None and after:
        return f'bin/{instrument}-(>{after.strftime("%Y-%m-%d")}).bin'

    if after is None and before:
        return f'bin/{instrument}-(<{before.strftime("%Y-%m-%d")}).bin'

    if before and after:
        return f'bin/{instrument}-({before.strftime("%Y-%m-%d")})-({after.strftime("%Y-%m-%d")}).bin'


def data_to_float32(datapoint):
    timestamp = np.int64(datapoint['time'].timestamp() * 1000)
    bid = np.float32(datapoint['bid'])
    ask = np.float32(datapoint['ask'])

    return timestamp, bid, ask


def create_db(name: str='tidepool', cfg: str='cfg.ini'):
    cfg = helpers.load_config(cfg)
    client = pymongo.MongoClient(cfg['db_string'])
    return client[name]


def dump_array_to_file(array, file='bin/output.bin'):
    with open(file, 'wb+') as f:
        binary = array.tobytes()
        f.write(binary)


def append_array_to_file(array, file='bin/output.bin'):
    with open(file, 'ab+') as f:
        binary = array.tobytes()
        f.write(binary)


def gather_data(instrument: str, db, before: datetime.datetime = None, after: datetime.datetime = None, limit=100000):
    if before and after:
        return np.array(
            list(db[instrument].find({'time': {'$gt': after, '$lt': before}}, {'_id': False}).limit(100000)))

    if before is None and after:
        return np.array(
            list(db[instrument].find({'time': {'$gt': after}}, {'_id': False}).limit(100000)))

    if after is None and before:
        return np.array(
            list(db[instrument].find({'time': {'$lt': before}}, {'_id': False}).limit(100000)))

    if before is None and after is None:
        raise ValueError('Must specify either before or after date, or both.')


def process_data(data: np.ndarray):
    processed = np.vectorize(data_to_float32)(data)

    types = np.dtype([('timestamp', processed[0].dtype), ('bid', processed[1].dtype), ('ask', processed[2].dtype)])
    arr = np.empty(len(processed[0]), types)
    arr['timestamp'], arr['bid'], arr['ask'] = processed

    return arr


def file_exists(path):
    path = Path(path)

    return path.is_file()


def create_binary(instrument: str, db=create_db(), file: str = None, before: datetime.datetime = None, after: datetime.datetime = None, force=False):
    if not verify_instrument(instrument, db):
        raise ValueError(f'Invalid instrument "{instrument}"')

    if file is None:
        file = generate_file_path(instrument, before, after)

    if file_exists(file):
        print(f'File already exists: {file}.')
        if not force:
            print('Use force=True to forcefully overwrite file, or use update_binary() to update file instead.')
            return

    if before is None:
        before = datetime.datetime(9999, 12, 31)

    if after is None:
        after = datetime.datetime(1970, 1, 1)

    print(f'Saving binary at: {file}')
    total_processed = 0
    latest_timestamp = after
    while True:
        data = gather_data(instrument, db, before=before, after=latest_timestamp)
        if len(data) == 0:
            break

        processed_data = process_data(data)
        append_array_to_file(processed_data, file=file)

        total_processed += len(data)
        print(f'Processed {len(data):,} data points from {data[0]["time"]} to {data[-1]["time"]}. Processed {total_processed:,} data points in total for this instrument.')
        latest_timestamp = data[-1]['time']


def update_binary(instrument: str, file: str, db=create_db(), before:datetime.datetime = None):
    pass


def verify_instrument(instrument, db=create_db()):
    return instrument in list_instruments(db)


def list_instruments(db=create_db()):
    instruments = db.list_collection_names()
    instruments.remove('raw')
    return instruments


def main():
    for instrument in list_instruments():
        create_binary(instrument)


if __name__ == '__main__':
    main()
