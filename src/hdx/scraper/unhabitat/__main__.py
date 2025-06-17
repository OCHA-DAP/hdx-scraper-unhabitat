#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this
script then creates in HDX.

"""

import logging
from os.path import dirname, expanduser, join

from hdx.api.configuration import Configuration
from hdx.data.user import User
from hdx.facades.infer_arguments import facade
from hdx.utilities.downloader import Download
from hdx.utilities.errors_onexit import ErrorsOnExit
from hdx.utilities.path import tempdir_batch
from hdx.utilities.retriever import Retrieve

from hdx.scraper.unhabitat import UNHabitat

logger = logging.getLogger(__name__)

_USER_AGENT_LOOKUP = "hdx-scraper-unhabitat"
_SAVED_DATA_DIR = "saved_data"  # Keep in repo to avoid deletion in /tmp
_UPDATED_BY_SCRIPT = "HDX Scraper: UNHabitat"


def main(
    save: bool = True,
    use_saved: bool = False,
) -> None:
    """Generate datasets and create them in HDX

    Args:
        save (bool): Save downloaded data. Defaults to True.
        use_saved (bool): Use saved data. Defaults to False.

    Returns:
        None
    """
    configuration = Configuration.read()
    User.check_current_user_write_access("unhabitat-das")

    with ErrorsOnExit() as errors:
        with tempdir_batch(_USER_AGENT_LOOKUP) as info:
            temp_dir = info["folder"]
            with Download() as downloader:
                retriever = Retrieve(
                    downloader=downloader,
                    fallback_dir=temp_dir,
                    saved_dir=_SAVED_DATA_DIR,
                    temp_dir=temp_dir,
                    save=save,
                    use_saved=use_saved,
                )
                folder = info["folder"]
                unhabitat = UNHabitat(configuration, retriever, folder, errors)
                dataset_names = unhabitat.get_data(
                    datasets=[
                        "open_spaces",
                        "urban_transport",
                        "spatial_growth_cities",
                        "housing_slums",
                        "basic_services",
                    ]
                )
                logger.info(f"Number of datasets to upload: {len(dataset_names)}")

                for dataset_name in dataset_names:
                    dataset = unhabitat.generate_dataset(dataset_name)
                    if dataset:
                        dataset.update_from_yaml(
                            path=join(
                                dirname(__file__), "config", "hdx_dataset_static.yaml"
                            )
                        )
                        dataset["notes"] = dataset["notes"].replace(
                            "\n", "  \n"
                        )  # ensure markdown has line breaks
                        dataset.create_in_hdx(
                            remove_additional_resources=True,
                            match_resource_order=False,
                            hxl_update=False,
                            updated_by_script=_UPDATED_BY_SCRIPT,
                            batch=info["batch"],
                        )


if __name__ == "__main__":
    facade(
        main,
        hdx_site="dev",
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_USER_AGENT_LOOKUP,
        project_config_yaml=join(
            dirname(__file__), "config", "project_configuration.yaml"
        ),
    )
