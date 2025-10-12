FROM odoo:18.0-20251008

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1


USER root

RUN apt-get update && apt-get install -y curl software-properties-common

# Install dependencies
RUN apt-get update && apt-get install -y curl software-properties-common

# Upgrade Python tools safely inside Docker
RUN pip3 install --break-system-packages --ignore-installed --upgrade pip setuptools wheel \
 && pip3 install --break-system-packages  pyOpenSSL


COPY src /mnt/extra-addons


ENTRYPOINT [ "/entrypoint.sh", "odoo" ]