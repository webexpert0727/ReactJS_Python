#!/bin/bash

set -e

if [[ ! -f "/var/www/src/webpack.manifest.app.json" ]]; then
    # for the first run in local env, when mounting volume "src" overwrites manifest files
    gosu $SYSTEM_USER bash -c "yarn run build"
fi

chown -R $SYSTEM_USER:$SYSTEM_GROUP /var/www/logs

if [[ "$1" = 'gunicorn' || "$3" == 'runserver' ]]; then
    gosu $SYSTEM_USER bash -c "\
        source /var/www/env/bin/activate && \
        python manage.py migrate --noinput && \
        python manage.py collectstatic --noinput && \
        touch /var/www/logs/{gunicorn.access.log,gunicorn.error.log,debug.log,order_processing.log}"
fi

tail -n 0 -f /var/www/logs/*.log &

case "$1" in
    gunicorn|python|celery)
        set -- gosu $SYSTEM_USER bash -c "source /var/www/env/bin/activate && $*"
    ;;
esac

exec "$@"
