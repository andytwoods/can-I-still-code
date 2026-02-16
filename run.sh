#!/bin/bash
set -e
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8018} --log-file -
