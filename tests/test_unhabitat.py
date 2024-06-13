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
    dataset_green_areas = {
        "name": "green-areas-afg",
        "title": "Afghanistan - Open spaces and green areas",
        "notes": "Data on a) Average share of urban areas allocated to streets and open public spaces, and b) Share of "
                 "urban population with convenient access to an open public space (defined as share of urban "
                 "population within 400 meters walking distance along the street network to an open public space).",
        "groups": [{"name": "afg"}],
        "tags": [
            {"name": "urban", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"},
            {"name": "sustainable development goals-sdg", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"},
        ],
        "package_creator": "briar-mills",
        "dataset_source": "UNHabitat",
        "owner_org": "unhabitat-das",
        "maintainer": "denmwa02",
        "data_update_frequency": "365",
        "dataset_date": "[2020-01-01T00:00:00 TO 2020-12-31T23:59:59]",
        "license_id": "hdx-pddl",
        "methodology": "Other",
        "methodology_other": "See methodology at https://data.unhabitat.org/pages/guidance",
        "caveats": "Read more at https://unhabitat.org/knowledge/data-and-analytics",
        "subnational": "1",
        "private": False,
    }

    resource_green_areas_csv = {
        "name": "SDG_11-7-1_AFG (csv)",
        "description": "SDG 11.7.1: Average share of the built-up area of cities that is open space for public use for "
                       "all, by sex, age and persons with disabilities",
        "format": "csv",
        "resource_type": "file.upload",
        "url_type": "upload",
    }
    resource_green_areas_xlsx = {
        "name": "SDG_11-7-1_AFG (xlsx)",
        "description": "SDG 11.7.1: Average share of the built-up area of cities that is open space for public use for "
                       "all, by sex, age and persons with disabilities",
        "format": "xlsx",
        "resource_type": "file.upload",
        "url_type": "upload",
    }

    dataset_housing_slums = {
        "name": "housing-slums",
        "title": "Housing, slums and informal settlements",
        "notes": "The share of urban population living in slum households per country and region, based on 4 out of 5 household shelter deprivations defined by UN-Habitat as indicators of informality: lack of access to improved water, lack of access to improved sanitation, lack of sufficient living area and quality/durability of structure. Security of tenure is the fifth deprivation that is not included due to data limitations.",
        "methodology": "Other",
        "methodology_other": "See methodology at https://data.unhabitat.org/pages/guidance",
        "dataset_date": "[2000-01-01T00:00:00 TO 2020-12-31T23:59:59]",
        "groups": [{"name": "world"}],
        "tags": [
            {"name": "urban", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"},
            {"name": "sustainable development goals-sdg", "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1"}
        ],
        "package_creator": "briar-mills",
        "dataset_source": "UNHabitat",
        "owner_org": "unhabitat-das",
        "maintainer": "denmwa02",
        "data_update_frequency": "365",
        "license_id": "hdx-pddl",
        "caveats": "Read more at https://unhabitat.org/knowledge/data-and-analytics",
        "subnational": "1",
        "private": False,
    }

    resource_housing_slums = {
        "name": "Slum_Estimates_2000-2020 (xlsx)",
        "description": "Proportion of Urban Population Living in Slum Households by Country or area 2000 - 2020 (Percent)",
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
        configuration["countries"] = ["AFG"]
        with temp_dir(
                "test_unhabitat", delete_on_success=True, delete_on_failure=False
        ) as folder:
            with Download() as downloader:
                retriever = Retrieve(downloader, folder, fixtures, folder, False, True)
                unhabitat = UNHabitat(configuration, retriever, folder, ErrorsOnExit())
                dataset_names = unhabitat.get_data(datasets=["green_areas", "housing_slums"])
                assert dataset_names == [
                    {"name": "green_areas_AFG"},
                    {"name": "green_areas_world"},
                    {"name": "housing_slums"}
                ]

                dataset = unhabitat.generate_dataset("green_areas_AFG")
                dataset.update_from_yaml()
                assert dataset == self.dataset_green_areas
                resources = dataset.get_resources()
                assert resources[0] == self.resource_green_areas_csv
                file = "SDG_11-7-1_AFG.csv"
                assert_files_same(join("tests", "fixtures", file), join(folder, file))
                assert resources[1] == self.resource_green_areas_xlsx
                file = "SDG_11-7-1_AFG.xlsx"
                testing.assert_frame_equal(
                    read_excel(join("tests", "fixtures", file)),
                    read_excel(join(folder, file)),
                )

                dataset = unhabitat.generate_dataset("housing_slums")
                dataset.update_from_yaml()
                assert dataset == self.dataset_housing_slums
                resources = dataset.get_resources()
                assert resources[0] == self.resource_housing_slums
