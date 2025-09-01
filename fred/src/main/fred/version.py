import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Version:
    name: str
    value: str

    def get_upcoming_options(self) -> List['Version']:
        vals = self.components(as_int=True)
        return [
            Version(
                name=self.name,
                value=".".join(
                    str(v)
                    for j, v in enumerate(vals[:i] + [val+1] + (2-i)*[0])
                ),
            )
            for i, val in enumerate(vals)
        ]

    def get_upcoming_options_with_tag(self) -> Dict[str, Dict]:
        tags = ["major", "minor", "patch"]
        return {
            version.value: {
                "version": version,
                "scope": tags[index],
            }
            for index, version in enumerate(self.get_upcoming_options())
        }

    def upcoming(
            self,
            major: bool = False,
            minor: bool = False,
            patch: bool = False,
    ) -> 'Version':
        ver_maj, ver_min, ver_pat = self.get_upcoming_options()
        if sum([major, minor, patch]) != 1:
            raise ValueError
        return ver_maj if major else ver_min if minor else ver_pat

    def components(self, as_int: bool = False) -> list:
        return [int(val) if as_int else val for val in self.value.split(".")]

    @property
    def major(self) -> int:
        component, *_ = self.components(as_int=True)
        return component

    @property
    def minor(self) -> int:
        _, component, *_ = self.components(as_int=True)
        return component

    @property
    def patch(self) -> int:
        *_, component = self.components(as_int=True)
        return component

    @classmethod
    def from_path(cls, dirpath: str, name: str):
        for file in os.listdir(dirpath):
            if file.lower().endswith("version"):
                filepath = os.path.join(dirpath, file)
                break
        else:
            raise ValueError("Version file not found for package name: " + name)

        with open(filepath, "r") as version_file:
            version_value = version_file.readline().strip()  # TODO: Validate version pattern via regex
            return cls(name=name, value=version_value)


version = Version.from_path(name="fred", dirpath=os.path.dirname(__file__))
