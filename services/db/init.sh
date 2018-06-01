#!/bin/bash

set -e

gosu postgres psql -d template1 -c 'create extension hstore;'
