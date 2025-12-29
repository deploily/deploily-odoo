FROM odoo:18.0-20251008

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER root

# Fix APT issues with Ubuntu Noble
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get update --allow-releaseinfo-change \
       --option Acquire::http::No-Cache=true \
       --option Acquire::Retries=5

# Install dependencies
RUN apt-get install -y curl software-properties-common

# Upgrade Python tools
RUN pip3 install --break-system-packages --ignore-installed --upgrade pip setuptools wheel \
 && pip3 install --break-system-packages pyOpenSSL

COPY src /mnt/deploily-addons

RUN mkdir -p /var/lib/odoo/.local/share/Odoo/addons/18.0 \
 && chown -R odoo:odoo /var/lib/odoo/.local

USER odoo

ENTRYPOINT [ "/entrypoint.sh", "odoo" ]
