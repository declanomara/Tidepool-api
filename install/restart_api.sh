#!/usr/bin/env bash

cd /usr/share/Tidepool-frontend &&
  uvicorn main:app --host 0.0.0.0 \
                   --port 443 \
                   --ssl-keyfile=/etc/letsencrypt/live/api.tidepool.finance/privkey.pem \
                   --ssl-certfile=/etc/letsencrypt/live/api.tidepool.finance/fullchain.pem