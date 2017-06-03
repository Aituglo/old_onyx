#!/usr/bin/env bash

set -Ee

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

TOP=$(cd $(dirname $0) && pwd -L)

VIRTUALENV_ROOT="${TOP}/venv-prod"

if [ ! -d ${VIRTUALENV_ROOT} ]; then
   mkdir -p $(dirname ${VIRTUALENV_ROOT})
  virtualenv -p python2.7 ${VIRTUALENV_ROOT}
fi
source ${VIRTUALENV_ROOT}/bin/activate
cd ${TOP}

pip install --upgrade pip
pip install --upgrade virtualenv
pip install -r requirements.txt

if [ ! -f ${TOP}/onyx/app_config.py ]; then
    echo "App Config not found!"
    echo "Create App Config"
    cp ${TOP}/onyx/config_example.py ${TOP}/onyx/app_config.py
fi

if [ ! -f ${TOP}/onyx/config/onyx.cfg ]; then
    echo "Config not found!"
    echo "Create Config"
    cp ${TOP}/onyx/config/onyx_example.cfg ${TOP}/onyx/config/onyx.cfg
fi

make compilelang

arch=$(arch)
os=$(uname -s)

cd ${TOP}/onyx/client/speech/assets

if [ ! -f ${TOP}/onyx/client/speech/assets/_snowboydetect.so ] || [ ! -f ${TOP}/onyx/client/speech/assets/snowboydetect.py ]; then
    echo "Snowboy not found not found!"
    echo "Download Snowboy"
    wget http://download.onyxlabs.fr/snowboy/snowboy_${os}_${arch}.tar.gz
    tar zxvf snowboy_${os}_${arch}.tar.gz
    rm snowboy_${os}_${arch}.tar.gz
fi

cd ${TOP}

echo "Setup Finished"