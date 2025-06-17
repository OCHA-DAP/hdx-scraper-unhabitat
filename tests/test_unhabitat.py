from os.path import join

from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.errors_onexit import ErrorsOnExit
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve
from pandas import read_excel, testing

from hdx.scraper.unhabitat.unhabitat import UNHabitat


class TestUNHabitat:
    dataset_open_spaces = {
        "name": "open-spaces-afg",
        "title": "Afghanistan - Open spaces and green areas",
        "notes": "Data on a) Average share of urban areas allocated to streets and open public spaces, and b) Share of "
        "urban population with convenient access to an open public space (defined as share of urban "
        "population within 400 meters walking distance along the street network to an open public space). \n"
        "Data on a) Average share of cities/urban areas in green areas (%), and b) Green area per capita "
        "(m2/person) for the periods 1990, 2000, 2010 and 2020.",
        "groups": [{"name": "afg"}],
        "tags": [
            {
                "name": "urban",
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            },
            {
                "name": "sustainable development goals-sdg",
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            },
        ],
        "package_creator": "briar-mills",
        "dataset_source": "UNHabitat",
        "owner_org": "unhabitat-das",
        "maintainer": "denmwa02",
        "data_update_frequency": "365",
        "dataset_date": "[2020-01-01T00:00:00 TO 2020-12-31T23:59:59]",
        "license_id": "hdx-pddl",
        "methodology": "Other",
        "methodology_other": "The data referenced herein is calculated using urban boundaries defined using the Degree "
        "of Urbanization approach to defining cities and urban areas, which may be larger or "
        "smaller than the official municipality boundaries.  Within each city/urban area, the "
        "green areas are extracted using satellite imagery analysis for four time periods 1990, "
        "2000, 2010 and 2020 based on the Normalized Difference Vegetation Index (NDVI), which "
        "assesses the level of greenness from satellite imagery. In this analysis, green areas "
        "are defined as parts of the city that are green for most parts of the year, and include "
        "individual trees, forests or forested areas, shrubs, perennial grasses and such other "
        "types of long-term vegetation. Waterbodies are not considered as green areas in this "
        "assessment. Since the stability the input data can be affected by climatic conditions "
        "such as long-term drought or rain, a median image was created over a three-year period, "
        "reducing thousands of images available for each point(pixel) to the most stable pixel. "
        "The median was used as opposed to the mean, because the median is less influenced by "
        "extremes (in this case extreme rains or drought). \n"
        "Unlike majority of the existing datasets which use basic NDVI thresholds, the most "
        "common of which include values of -1 to <0.2 for non-vegetated pixels, >=0.2 – 0.5 for "
        "low vegetation and >0.5 for high vegetation , the premise of this new analysis was that "
        "each city is unique, and using a constant NDVI threshold would work to the disadvantage "
        "of cities in drier regions. As such, NDVI thresholds were manually defined for each city "
        "per year by GIS experts at UN-Habitat. The analysis framework – including selection and "
        "mosaicking of images from the Landsat and Sentinel missions, pre-processing and NDVI "
        "analysis and thresholding was based on the Google Earth Engine platform. \n"
        "The results from this analysis were then used to calculate two indicators: a) the "
        "average share of green area in city/urban area (percentage) and  b) the green are per "
        "capita (m2 per person). Population data used to calculate the green area per capita is "
        "sourced from GHS-Pop for 1990, 2000, 2010 and 2020. \n"
        "The calculation of global and regional averages for the indicator on share of green area "
        "in city/urban areas are based on simple averages, while those on green area per capita "
        "are based on population weighted averages per analysis year.",
        "caveats": "Read more at https://unhabitat.org/knowledge/data-and-analytics",
        "subnational": "1",
        "private": False,
    }

    resource_open_spaces_csv = {
        "name": "SDG_11-7-1_AFG (csv)",
        "description": "SDG 11.7.1: Average share of the built-up area of cities that is open space for public use for "
        "all, by sex, age and persons with disabilities",
        "format": "csv",
        "resource_type": "file.upload",
        "url_type": "upload",
    }
    resource_open_spaces_xlsx = {
        "name": "SDG_11-7-1_AFG (xlsx)",
        "description": "SDG 11.7.1: Average share of the built-up area of cities that is open space for public use for "
        "all, by sex, age and persons with disabilities",
        "format": "xlsx",
        "resource_type": "file.upload",
        "url_type": "upload",
    }

    def test_unhabitat(self, configuration, fixtures_dir, input_dir, config_dir):
        with temp_dir(
            "Testunhabitat",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                retriever = Retrieve(
                    downloader=downloader,
                    fallback_dir=tempdir,
                    saved_dir=input_dir,
                    temp_dir=tempdir,
                    save=False,
                    use_saved=True,
                )
                configuration["countries"] = ["AFG"]
                unhabitat = UNHabitat(configuration, retriever, tempdir, ErrorsOnExit())
                dataset_names = unhabitat.get_data(datasets=["open_spaces"])
                assert dataset_names == [
                    "open_spaces_AFG",
                    "open_spaces_world",
                ]

                dataset = unhabitat.generate_dataset("open_spaces_AFG")
                dataset.update_from_yaml(
                    path=join(config_dir, "hdx_dataset_static.yaml")
                )
                assert dataset == self.dataset_open_spaces
                resources = dataset.get_resources()
                assert len(resources) == 4
                assert resources[0] == self.resource_open_spaces_csv
                file = "SDG_11-7-1_AFG.csv"
                assert_files_same(join(fixtures_dir, file), join(tempdir, file))
                assert resources[1] == self.resource_open_spaces_xlsx
                file = "SDG_11-7-1_AFG.xlsx"
                testing.assert_frame_equal(
                    read_excel(join(fixtures_dir, file)),
                    read_excel(join(tempdir, file)),
                )
