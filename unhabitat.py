#!/usr/bin/python
"""
UNHabitat:
------------

Reads UNHabitat inputs and creates datasets.

"""
import logging

from hdx.data.dataset import Dataset
from hdx.location.country import Country
from hdx.utilities.dictandlist import dict_of_lists_add, write_list_to_csv
from hdx.data.resource import Resource
from os.path import join
from pandas import DataFrame, ExcelWriter
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

    def get_data(self, datasets=None):
        if not datasets:
            datasets = self.configuration["datasets"]
        for dataset_name in datasets:
            dataset_info = self.configuration["datasets"][dataset_name]
            base_url = dataset_info["base_url"]
            headers, iterator = self.retriever.get_tabular_rows(
                base_url,
                headers=dataset_info.get("header", 1),
                format=dataset_info.get("format"),
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
        dataset["methodology"] = "Other"
        dataset["methodology_other"] = dataset_info["methodology"]
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
        self.generate_resource(dataset, country_iso3, rows, dataset_info, "csv")
        self.generate_resource(dataset, country_iso3, rows, dataset_info, "xlsx")
        return dataset

    def generate_resource(self, dataset, country_iso3, rows, dataset_info, file_format):
        headers = list(rows[0].keys())
        filename = f"{dataset_info['filename']}_{country_iso3}"
        filepath = join(self.folder, f"{filename}.{file_format}")
        resource = Resource(
            {
                "name": f"{filename} ({file_format})",
                "description": dataset_info["resource_notes"],
            }
        )
        if file_format == "csv":
            write_list_to_csv(filepath, rows, columns=headers, encoding="utf-8")
        if file_format == "xlsx":
            df = DataFrame(rows)
            writer = ExcelWriter(filepath, engine="xlsxwriter")
            df.to_excel(writer, sheet_name=filename, index=False)
            if dataset_info["value_header"]:
                workbook = writer.book
                worksheet = writer.sheets[filename]
                num_format = workbook.add_format({"num_format": "0.0"})
                for header in dataset_info["value_header"]:
                    worksheet.set_column(headers.index(header), headers.index(header), None, num_format)
            writer.close()

        resource.set_format(file_format)
        resource.set_file_to_upload(filepath)
        dataset.add_update_resource(resource)
        return resource
