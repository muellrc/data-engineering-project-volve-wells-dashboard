"""Luigi tasks."""
# How to run Luigi
# PYTHONPATH='.' luigi --module tasks UploadTask --fname "./data/sample.csv" --local-scheduler

import os
import json
import csv
from abc import ABC

import luigi
from luigi.contrib import postgres
from luigi.util import requires, inherits, common_params


class ResourceTask(luigi.Task):
    """Task to require the existence of a file."""

    fname = luigi.Parameter()

    def output(self):
        # This task outpus a local file, but it could be elsewhere, like
        # AWS s3 (luigi.contrib.aws.S3Target) or GCS (luigi.contrib.gcs.GCSTarget)
        return luigi.LocalTarget(self.fname)


@requires(ResourceTask)
class AbstractParseTask(ABC, luigi.Task):
    pass


class ParseJSONTask(AbstractParseTask):
    """Task to parse a JSON array of objects into a consistent format."""

    def run(self):
        # Format the input, and write to the output
        with self.input().open() as f:
            data = json.load(f)
        header = list(data[0].keys())
        header.insert(0, "id")
        parsed_data = [[i, *obj.values()] for i, obj in enumerate(data)]
        with self.output().open(mode="w") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(parsed_data)

    def output(self):
        # This task writes its output to a local file
        return luigi.LocalTarget(self.task_id + ".csv")


class ParseCSVTask(AbstractParseTask):
    """Task to parse a CSV into a consistent format."""

    def run(self):
        # Format the input, and write to the output
        with self.input().open() as f:
            reader = csv.reader(f)
            parsed_data = [[i, *row] for i, row in enumerate(reader)]
            parsed_data[0][0] = "id"
        with self.output().open(mode="w") as f:
            writer = csv.writer(f)
            writer.writerows(parsed_data)

    def output(self):
        # This task writes its output to a local file
        return luigi.LocalTarget(self.task_id + ".csv")


@inherits(AbstractParseTask)
class ParseTask(luigi.Task):
    """Parse a CSV or JSON resource into a consistent format."""

    def run(self):
        # Naively check file type
        ext = self.fname.split(".")[-1]
        params = common_params(self, AbstractParseTask)
        if ext == "csv":
            local_target = yield ParseCSVTask(**params)
        elif ext == "json":
            local_target = yield ParseJSONTask(**params)
        else:
            raise Exception("Not sure how to handle that file type...")
        with local_target.open() as inf, self.output().open("w") as outf:
            outf.write(inf.read())

    def output(self):
        # This task writes its output to a local file
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(ParseTask)
class TransformTask(luigi.Task):
    """Transform the consistently formatted data."""

    def run(self):
        with self.input().open() as f:
            reader = csv.reader(f)
            data = list(reader)

        # Do some awesome transforms...
        data[0].insert(1, "full_name")
        for row in data[1:]:
            full_name = " ".join(row[1:3])
            row.insert(1, full_name)

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerows(data[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".tsv")


@requires(TransformTask)
class UploadTask(postgres.CopyToTable):
    """Upload the data to a postgres instance."""

    host = os.environ.get("POSTGRES_HOST", "localhost")
    database = os.environ.get("POSTGRES_DATABASE", "postgres")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "password")
    table = "people"
    columns = (
        ("id", "BIGINT"),
        ("full_name", "TEXT"),
        ("first_name", "TEXT"),
        ("last_name", "TEXT"),
        ("company_name", "TEXT"),
        ("address", "TEXT"),
        ("city", "TEXT"),
        ("county", "TEXT"),
        ("state", "TEXT"),
        ("zip", "TEXT"),
        ("phone1", "TEXT"),
        ("phone2", "TEXT"),
        ("email", "TEXT"),
        ("web", "TEXT"),
    )
