#!/usr/bin/python
"""
UNHabitat:
------------

Reads UNHabitat inputs and creates datasets.

"""
import logging

from hdx.data.dataset import Dataset
from hdx.location.country import Country
from hdx.utilities.dictandlist import dict_of_dicts_add, dict_of_lists_add, dict_of_sets_add, write_list_to_csv
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
        self.files = {}

    def get_data(self, datasets=None):
        if not datasets:
            datasets = self.configuration["datasets"]
        for dataset_name in datasets:
            dataset_info = self.configuration["datasets"][dataset_name]

            if dataset_info.get("global"):
                resource_infos = dataset_info["resources"]
                for resource, resource_info in resource_infos.items():
                    base_url = resource_info["base_url"]
                    file_path = self.retriever.download_file(
                        base_url,
                        filename=f"{resource_info['filename']}.{resource_info['format']}",
                    )
                    dict_of_dicts_add(self.files, dataset_name, resource, file_path)
                    dict_of_sets_add(self.dates, dataset_name, dataset_info["date_min"])
                    dict_of_sets_add(self.dates, dataset_name, dataset_info["date_max"])
                continue

            base_url = dataset_info["base_url"]
            headers, iterator = self.retriever.get_tabular_rows(
                base_url,
                headers=dataset_info.get("header", 1),
                format=dataset_info.get("format"),
                dict_form=True,
                encoding="utf-8"
            )

            for row in iterator:
                country_name = row[dataset_info["country_header"]]
                if not country_name:
                    continue
                iso3 = Country.get_iso3_country_code(country_name)

                if iso3 in self.configuration["countries"]:
                    dict_of_lists_add(self.data, f"{dataset_name}_{iso3}", row)
                    if dataset_info.get("date_header"):
                        for date_header in dataset_info["date_header"]:
                            if row[date_header]:
                                dict_of_sets_add(self.dates, f"{dataset_name}_{iso3}", row[date_header])
                    else:
                        dict_of_sets_add(self.dates, f"{dataset_name}_{iso3}", dataset_info["date_min"])
                        dict_of_sets_add(self.dates, f"{dataset_name}_{iso3}", dataset_info["date_max"])

                dict_of_lists_add(self.data, f"{dataset_name}_world", row)
                if dataset_info.get("date_header"):
                    for date_header in dataset_info["date_header"]:
                        if row[date_header]:
                            dict_of_sets_add(self.dates, f"{dataset_name}_world", row[date_header])
                else:
                    dict_of_sets_add(self.dates, f"{dataset_name}_world", dataset_info["date_min"])
                    dict_of_sets_add(self.dates, f"{dataset_name}_world", dataset_info["date_max"])

        return [{"name": dataset_name} for dataset_name in sorted(self.data)] + [{"name": dataset_name} for dataset_name in sorted(self.files)]

    def generate_dataset(self, dataset_name):
        if dataset_name in self.files:
            dataset_info = self.configuration["datasets"][dataset_name]
            iso3 = "world"
        else:
            dataset_info = self.configuration["datasets"][dataset_name.rsplit("_", 1)[0]]
            iso3 = dataset_name.rsplit("_", 1)[1]
        if iso3 == "world":
            country_name = "world"
            title = dataset_info["title"]
        else:
            country_name = Country.get_country_name_from_iso3(iso3)
            title = f"{country_name} - {dataset_info['title']}"
        dataset = Dataset({"name": slugify(dataset_name), "title": title})
        dataset["notes"] = dataset_info["notes"]
        dataset.set_time_period_year_range(
            min(self.dates[dataset_name]),
            max(self.dates[dataset_name]),
        )
        if iso3 == "world":
            dataset.add_other_location(country_name)
        else:
            dataset.add_country_location(country_name)
        dataset.add_tags(self.configuration["tags"])

        filepaths = self.files.get(dataset_name)
        if filepaths:
            for resource in filepaths:
                resource_info = dataset_info["resources"][resource]
                self.generate_resource(dataset, resource_info, resource_info["format"], filepath=filepaths[resource])
            return dataset

        rows = self.data[dataset_name]
        self.generate_resource(dataset, dataset_info, "csv", iso3=iso3, rows=rows)
        self.generate_resource(dataset, dataset_info, "xlsx", iso3=iso3, rows=rows)
        return dataset

    def generate_resource(self, dataset, dataset_info, file_format, iso3=None, rows=None, filepath=None):
        if filepath:
            filename = dataset_info["filename"]
        if rows:
            headers = list(rows[0].keys())
            filename = f"{dataset_info['filename']}_{iso3}"
            if iso3 == "world":
                filename = dataset_info["filename"]
            filepath = join(self.folder, f"{filename}.{file_format}")
            if file_format == "csv":
                write_list_to_csv(filepath, rows, columns=headers, encoding="utf-8")
            if file_format == "xlsx":
                df = DataFrame(rows)
                writer = ExcelWriter(filepath, engine="xlsxwriter")
                df.to_excel(writer, sheet_name=filename[:24], index=False)
                float_headers = df.select_dtypes(include=['float64']).columns
                if len(float_headers) > 0:
                    workbook = writer.book
                    worksheet = writer.sheets[filename[:24]]
                    num_format = workbook.add_format({"num_format": "0.0"})
                    for header in float_headers:
                        worksheet.set_column(headers.index(header), headers.index(header), None, num_format)
                writer.close()
        resource = Resource(
            {
                "name": f"{filename} ({file_format})",
                "description": dataset_info["resource_notes"],
            }
        )

        resource.set_format(file_format)
        resource.set_file_to_upload(filepath)
        dataset.add_update_resource(resource)
        return resource
