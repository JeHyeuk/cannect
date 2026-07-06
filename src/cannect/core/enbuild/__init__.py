__all__ = [
    "SQLBaselineDB",
    "PipelineEnv",
    "EngBuild",
]


def __getattr__(name):
    if name in {"SQLBaselineDB", "PipelineEnv", "EngBuild"}:
        from .engbuild import SQLBaselineDB, PipelineEnv, EngBuild
        return {
            "SQLBaselineDB": SQLBaselineDB,
            "PipelineEnv": PipelineEnv,
            "EngBuild": EngBuild,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
