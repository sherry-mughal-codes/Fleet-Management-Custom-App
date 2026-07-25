FROM frappe/bench:latest AS dev

USER frappe

WORKDIR /home/frappe

RUN bench init \
    --skip-redis-config-generation \
    --frappe-branch version-15 \
    frappe-bench

WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe . apps/fleet_management

RUN bench setup requirements

# Docker Redis configuration
RUN echo "redis_cache: redis://redis-cache:6379" > sites/common_site_config.json && \
    echo "redis_queue: redis://redis-queue:6379" >> sites/common_site_config.json && \
    echo "redis_socketio: redis://redis-queue:6379" >> sites/common_site_config.json

CMD ["bench", "start"]