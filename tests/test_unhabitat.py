#!/usr/bin/python
"""
Unit tests for unhabitat.

"""
from os.path import join
from pandas import read_excel, testing

import pytest
from hdx.api.configuration import Configuration
from hdx.data.vocabulary import Vocabulary
from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.errors_onexit import ErrorsOnExit
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve
from hdx.utilities.useragent import UserAgent

from unhabitat import UNHabitat


class TestUNHabitat:
    dataset = {
        "name": "green-areas-afg",
        "title": "Afghanistan - Open spaces and green areas",
        "notes": "An open public space (OPS) is defined as an area that openly and freely accessible space for all "
                 "(without any cost implication) for enjoyment of social services such as recreation. Identification "
                 "of open public spaces is based on data compiled from city land use plans and open sources including "
                 "OpenStreetMap and GoogleEarth; Data used to estimate population with access to open public spaces is "
                 "based on grid level population disaggregation directly from city/country data, or from the HRSL "
                 "(facebook and CIESIN) and WorldPop;  City/urban area used in the analyis has been generated using a "
                 "classification approach based on the Degree of Urbanization concept to city definition. As a result, "
                 "the urban/city area used for the indicator computation in this data table may be larger or smaller "
                 "than the official municipality boundaries. Designation and data provided by the country and compiled "
                 "by UNHabitat. The designations employed do not imply the expression of any opinion whatsoever on the "
                 "part of the Secretariat of the United Nations concerning the legal status of any country, territory, "
                 "city or area; or of its authorities, or concerning the delimitation of its frontiers or boundaries.",
        "dataset_date": "[2020-01-01T00:00:00 TO 2020-12-31T23:59:59]",
        "groups": [{"name": "afg"}],
        "tags": [
            {"name": "topography", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"},
            {"name": "urban", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"},
            {"name": "sustainable development goals-sdg", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"},
        ],
        "package_creator": "briar-mills",
        "dataset_source": "UNHabitat",
        "owner_org": "unhabitat-das",
        "maintainer": "denmwa02",
        "data_update_frequency": "365",
        "license_id": "hdx-pddl",
        "methodology": "Other",
        "methodology_other": "Full metadata available at "
                             "https://unstats.un.org/sdgs/metadata/files/Metadata-11-07-01.pdf",
        "caveats": "Read more at https://unhabitat.org/knowledge/data-and-analytics",
        "subnational": "1",
        "private": False,
    }

    resource_csv = {
        "name": "SDG_11_7_1_AFG (csv)",
        "description": "Average share of the built-up area of cities that is open space for public use for all (%)",
        "format": "csv",
        "resource_type": "file.upload",
        "url_type": "upload",
    }
    resource_xlsx = {
        "name": "SDG_11_7_1_AFG (xlsx)",
        "description": "Average share of the built-up area of cities that is open space for public use for all (%)",
        "format": "xlsx",
        "resource_type": "file.upload",
        "url_type": "upload",
    }

    @pytest.fixture(scope="function")
    def fixtures(self):
        return join("tests", "fixtures")

    @pytest.fixture(scope="function")
    def configuration(self):
        Configuration._create(
            hdx_read_only=True,
            user_agent="test",
            project_config_yaml=join("config", "project_configuration.yaml"),
        )
        UserAgent.set_global("test")
        tags = (
            "topography",
            "urban",
            "sustainable development goals-sdg",
        )
        Vocabulary._tags_dict = {tag: {"Action to Take": "ok"} for tag in tags}
        tags = [{"name": tag} for tag in tags]
        Vocabulary._approved_vocabulary = {
            "tags": tags,
            "id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            "name": "approved",
        }
        return Configuration.read()

    def test_generate_dataset(self, configuration, fixtures):
        with temp_dir(
                "test_unhabitat", delete_on_success=True, delete_on_failure=False
        ) as folder:
            with Download() as downloader:
                retriever = Retrieve(downloader, folder, fixtures, folder, False, True)
                unhabitat = UNHabitat(configuration, retriever, folder, ErrorsOnExit())
                dataset_names = unhabitat.get_data()
                assert dataset_names == [
                    {"name": "green_areas_AFG"},
                    {"name": "green_areas_world"},
                ]

                dataset = unhabitat.generate_dataset("green_areas_AFG")
                dataset.update_from_yaml()
                assert dataset == self.dataset
                resources = dataset.get_resources()
                assert resources[0] == self.resource_csv
                file = "SDG_11_7_1_AFG.csv"
                assert_files_same(join("tests", "fixtures", file), join(folder, file))
                assert resources[1] == self.resource_xlsx
                file = "SDG_11_7_1_AFG.xlsx"
                testing.assert_frame_equal(
                    read_excel(join("tests", "fixtures", file)),
                    read_excel(join(folder, file)),
                )
