import datetime as dt
from dataclasses import dataclass, asdict


@dataclass(frozen=True, slots=True)
class RuntimeProfilingSnapshot:
    snapshot_at: dt.datetime
    cpu_percent: float
    virtual_memory_percent: float
    swap_memory_percent: float
    disk_usage_percent: float

    @classmethod
    def auto(cls) -> 'RuntimeProfilingSnapshot':
        import psutil

        return cls(
            snapshot_at=dt.datetime.utcnow(),
            cpu_percent=psutil.cpu_percent(interval=1),
            virtual_memory_percent=psutil.virtual_memory().percent,
            swap_memory_percent=psutil.swap_memory().percent,
            disk_usage_percent=psutil.disk_usage("/").percent,
        )
    
    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["snapshot_at"] = self.snapshot_at.isoformat()
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeInfo:
    snapshot_at: dt.datetime
    python_version: str
    platform: str
    processor: str
    modules: list[str]
    profiling_snaphots: list[RuntimeProfilingSnapshot]


    @classmethod
    def auto(cls, exclude_initial_profile: bool = False) -> 'RuntimeInfo':
        import platform

        return cls(
            python_version=platform.python_version(),
            platform=platform.platform(),
            processor=platform.processor(),
            modules=sorted(cls.get_modules()),
            snapshot_at=dt.datetime.utcnow(),
            profiling_snaphots=[] if exclude_initial_profile else [
                RuntimeProfilingSnapshot.auto()
            ],
        )
    
    def take_profiling_snapshot(self) -> 'RuntimeInfo':
        return self.profiling_snaphots.append(
            RuntimeProfilingSnapshot.auto()
        )

    @staticmethod
    def get_modules():
        import sys
        import pkgutil

        return {
            module.name
            for module in pkgutil.iter_modules()
        }.union(sys.builtin_module_names)
    
    def to_dict(
            self,
            exclude_modules: bool = False,
            exclude_profiling_snapshots: bool = False,
        ) -> dict:
        payload = asdict(self)
        payload["snapshot_at"] = self.snapshot_at.isoformat()
        payload["profiling_snaphots"] = [
            snapshot.to_dict() for snapshot in self.profiling_snaphots
        ]
        if exclude_modules:
            payload.pop("modules", None)
        if exclude_profiling_snapshots:
            payload.pop("profiling_snaphots", None)
        return payload