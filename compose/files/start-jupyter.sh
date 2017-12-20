#!/bin/bash

echo "Adding local dev username=admin password=admin"

username="admin"
password="admin"
useradd -m -p $(openssl passwd -1 ${password}) -s /bin/bash -G sudo ${username}

/opt/conda/bin/conda install -yq psycopg2=2.7
/opt/conda/bin/conda clean -tipsy
/opt/conda/bin/pip install --no-cache-dir oauthenticator==0.7.* dockerspawner==0.9.* notebook

jupyterhub -f /data/jupyterhub_config.py

echo "exiting"
sleep 300
