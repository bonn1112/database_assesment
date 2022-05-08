import csv

from django.http import HttpResponse


def csv_reader(file):
    return list(csv.DictReader(file.read().decode('utf-8-sig').splitlines()))
