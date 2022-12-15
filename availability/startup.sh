#!/bin/bash

python -m availability.adapters.event_processor &

python -m availability.adapters.restapi &

wait -n

exit $?
