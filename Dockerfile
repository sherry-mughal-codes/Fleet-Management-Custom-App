FROM frappe/bench:v15 AS dev

USER frappe
WORKDIR /home/frappe/frappe-bench

# Ensure custom app directory is initialized properly
RUN mkdir -p apps/fleet_management

COPY --chown=frappe:frappe . /home/frappe/frappe-bench/apps/fleet_management

# Default entrypoint relies on bench CLI
CMD ["bench", "start"]
