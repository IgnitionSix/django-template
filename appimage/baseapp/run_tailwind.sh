#!/bin/sh
set -e

cd /code/baseapp/core/static_src

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

npm run dev
