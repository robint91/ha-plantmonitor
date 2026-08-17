import importlib.metadata

from packaging.requirements import Requirement

requirements = [
    Requirement(value)
    for distribution in (
        "homeassistant",
        "pytest-homeassistant-custom-component",
    )
    for value in (importlib.metadata.requires(distribution) or ())
]
print(
    "\n".join(
        str(requirement)
        for requirement in requirements
        if requirement.name.lower() not in {"homeassistant", "lru-dict"}
    )
)
