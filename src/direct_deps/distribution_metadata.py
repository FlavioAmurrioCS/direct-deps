from __future__ import annotations

import glob
import os
from typing import NamedTuple


class DistributionMetadata(NamedTuple):
    name: str
    top_level: list[str]

    @classmethod
    def from_dist_info_dir(cls, dist_info_dir: str) -> DistributionMetadata:
        top_level_file = os.path.join(dist_info_dir, "top_level.txt")
        record_file = os.path.join(dist_info_dir, "RECORD")
        metadata_file = os.path.join(dist_info_dir, "METADATA")

        with open(metadata_file) as f:
            for line in f:
                if line.startswith("Name: "):
                    name = line.split(": ")[1].strip()
                    break
            else:
                msg = "No name found in METADATA"
                raise ValueError(msg)

        top_level: set[str] = set()
        with open(record_file) as f:
            for line in f:
                file = line.split(",")[0]
                if file.endswith(".py"):
                    top_level.add(file.split(os.sep)[0])

        if os.path.exists(top_level_file):
            with open(top_level_file) as f:
                top_level.update(x.strip() for x in f)

        return cls(name, list(top_level))


def _get_dist_info_dirs(site_packages_dirs: list[str]) -> list[str]:
    return [
        dist_info_dir
        for site_package_dir in site_packages_dirs
        for dist_info_dir in glob.glob(os.path.join(site_package_dir, "*.dist-info"))
    ]


def get_dependency_lookup_table(site_packages_dirs: list[str]) -> dict[str, DistributionMetadata]:
    ret = {}
    for dist_info_dir in _get_dist_info_dirs(site_packages_dirs):
        p = DistributionMetadata.from_dist_info_dir(dist_info_dir)
        for top_level in p.top_level:
            ret[top_level] = p
    return ret
