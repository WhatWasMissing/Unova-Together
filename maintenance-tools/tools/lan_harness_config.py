"""Helpers for preparing isolated melonDS configurations in LAN tests."""

import re


_INSTANCE_TABLE = re.compile(r"^\[(Instance\d+)(?:\.(.+))?\]$")


def make_instance_parent_tables_explicit(config: str) -> str:
    """Promote implicit InstanceN tables before adding per-instance values.

    melonDS reads per-instance defaults into the InstanceN table itself. When
    the packaged TOML starts with a nested section such as
    ``[Instance0.Keyboard]``, toml11 marks ``Instance0`` as implicit and its
    serializer rejects later scalar defaults under that parent. Declaring the
    parent first preserves the same TOML data while making subsequent saves
    serializable.
    """
    output: list[str] = []
    explicit_parents: set[str] = set()

    for line in config.splitlines():
        match = _INSTANCE_TABLE.fullmatch(line.strip())
        if match:
            parent, child = match.groups()
            if child is None:
                explicit_parents.add(parent)
            elif parent not in explicit_parents:
                output.append(f"[{parent}]")
                explicit_parents.add(parent)
        output.append(line)

    result = "\n".join(output)
    return result + ("\n" if config.endswith(("\n", "\r")) else "")
