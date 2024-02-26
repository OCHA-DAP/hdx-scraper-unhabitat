#!/usr/bin/python
"""
UNHabitat:
------------

Reads UNHabitat inputs and creates datasets.

"""
import logging

from hdx.data.dataset import Dataset
from hdx.location.country import Country
from hdx.utilities.dictandlist import dict_of_lists_add
from slugify import slugify

logger = logging.getLogger(__name__)


class UNHabitat:
    def __init__(self, configuration, retriever, folder, errors):
        self.configuration = configuration
        self.retriever = retriever
        self.folder = folder
        self.errors = errors
        self.data = {}
        self.dates = {}

    def get_data(self):
        for dataset_name in self.configuration["datasets"]:
            dataset_info = self.configuration["datasets"][dataset_name]
            base_url = dataset_info["base_url"]
            headers, iterator = self.retriever.get_tabular_rows(
                base_url,
                format="xlsx",
                dict_form=True,
                encoding="utf-8"
            )

            for row in iterator:
                row = {key: row[key] for key in row if key in dataset_info["headers"]}
                year = row[dataset_info["date_header"]]
                country_name = row[dataset_info["country_header"]]
                country_iso3 = Country.get_iso3_country_code(country_name)

                if country_iso3 in self.configuration["countries"]:
                    dict_of_lists_add(self.data, f"{dataset_name}_{country_iso3}", row)
                    dict_of_lists_add(self.dates, f"{dataset_name}_{country_iso3}", year)

                dict_of_lists_add(self.data, f"{dataset_name}_world", row)
                dict_of_lists_add(self.dates, f"{dataset_name}_world", year)

        return [{"name": dataset_name} for dataset_name in sorted(self.data)]

    def generate_dataset(self, dataset_name):
        dataset_info = self.configuration["datasets"][dataset_name.rsplit("_", 1)[0]]
        country_iso3 = dataset_name.rsplit("_", 1)[1]
        if country_iso3 == "world":
            country_name = "world"
            title = dataset_info["title"].replace("country - ", "")
        else:
            country_name = Country.get_country_name_from_iso3(country_iso3)
            title = dataset_info["title"].replace("country", country_name)
        dataset = Dataset({"name": slugify(dataset_name), "title": title})
        dataset["notes"] = dataset_info["notes"]
        dataset.set_time_period_year_range(
            min(self.dates[dataset_name]),
            max(self.dates[dataset_name]),
        )
        if country_iso3 == "world":
            dataset.add_other_location(country_name)
        else:
            dataset.add_country_location(country_name)
        dataset.add_tags(dataset_info["tags"])

        rows = self.data[dataset_name]
        filename = f"{dataset_info['filename']}_{country_iso3}.csv"
        resourcedata = {
            "name": filename,
            "description": dataset_info["notes"],
        }
        dataset.generate_resource_from_rows(
            folder=self.folder,
            filename=filename,
            rows=rows,
            resourcedata=resourcedata,
            headers=list(rows[0].keys()),
            encoding="utf-8",
        )

        return dataset
