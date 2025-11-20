## producer
- get data from openwheater api
- throw into rabbitmq

## consumer
- reads from rabbitmq
- send to api

## api
- get post data
- write into database

## dashboard
- get data from api
- show in dashboard
