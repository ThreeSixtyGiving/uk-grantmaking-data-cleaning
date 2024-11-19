from itertools import islice
from typing import Dict, Generator

from django.db import models

DEFAULT_BATCH_SIZE = 10_000


def batched(iterable, n: int = DEFAULT_BATCH_SIZE):
    "Batch data into lists of length n. The last batch may be shorter."
    # https://stackoverflow.com/a/8290490/715621
    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            return
        yield batch


def do_batched_update(
    model: models.Model,
    iterable: Generator[Dict, None, None],
    unique_fields: list[str],
    update_fields: list[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
):
    def inner_iterable():
        for record in iterable:
            yield model(**record)

    for batch in batched(inner_iterable(), batch_size):
        model.objects.bulk_create(
            batch,
            batch_size,
            update_conflicts=True,
            unique_fields=unique_fields,
            update_fields=update_fields,
        )
