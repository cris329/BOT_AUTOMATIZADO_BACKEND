FROM pyd4vinci/scrapling:0.4.13

WORKDIR /srv/sofia-consulta

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    SOFIA_HEADLESS=false

RUN apt-get update && apt-get install -y --no-install-recommends \
        procps \
        xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /srv/sofia-consulta/storage/sofia_diagnostico \
                 /srv/sofia-consulta/storage/betowa_diagnostico \
                 /srv/sofia-consulta/storage/sofia_session

COPY requirements.txt .
RUN uv pip install --python /app/.venv/bin/python --no-cache-dir -r requirements.txt
RUN /app/.venv/bin/python -m patchright install chromium

COPY app ./app
COPY server ./server
COPY entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' /srv/sofia-consulta/entrypoint.sh \
    && chmod +x /srv/sofia-consulta/entrypoint.sh

EXPOSE 8090
ENTRYPOINT []
CMD ["/srv/sofia-consulta/entrypoint.sh"]
