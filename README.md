### Collector for UN Habitat datasets
[![Build Status](https://github.com/OCHA-DAP/hdx-scraper-unhabitat/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-scraper-unhabitat/actions/workflows/run-python-tests.yaml) [![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-scraper-unhabitat/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-scraper-unhabitat?branch=main)

This script downloads data from the [UN Habitat site](https://data.unhabitat.org/) and creates global and country level datasets in HDX.


### Usage

    python run.py

For the script to run, you will need to have a file called .hdx_configuration.yaml in your home directory containing your HDX key eg.

    hdx_key: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    hdx_read_only: false
    hdx_site: prod
    
 You will also need to supply the universal .useragents.yaml file in your home directory as specified in the parameter *user_agent_config_yaml* passed to facade in run.py. The collector reads the key **hdx-scraper-unhabitat** as specified in the parameter *user_agent_lookup*.
 
 Alternatively, you can set up environment variables: USER_AGENT, HDX_KEY, HDX_SITE, LOG_FILE_ONLY