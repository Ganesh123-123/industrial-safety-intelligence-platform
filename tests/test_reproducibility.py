import pytest
from backend.app.services.generator import SyntheticDataGenerator

def test_deterministic_generator_reproducibility():
    seed = 20261022
    profile = "starter"

    gen1 = SyntheticDataGenerator(seed=seed, profile=profile)
    res1 = gen1.run(db=None, export_files=False)

    gen2 = SyntheticDataGenerator(seed=seed, profile=profile)
    res2 = gen2.run(db=None, export_files=False)

    assert res1["canonical_checksum"] == res2["canonical_checksum"]
    assert res1["ground_truth_count"] == res2["ground_truth_count"]
    assert res1["summary"] == res2["summary"]


def test_full_profile_alarm_definitions_are_unique_and_cover_safety_categories():
    generator = SyntheticDataGenerator(profile="full")
    generator._generate_alarm_definitions()

    definitions = generator.alarm_defs
    assert len(definitions) == 200
    assert len({definition.alarm_definition_id for definition in definitions}) == 200
    assert len({definition.alarm_code for definition in definitions}) == 200
    assert len({definition.alarm_name for definition in definitions}) == 200
    severities = {definition.severity for definition in definitions}
    assert severities <= {
        "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    }
    assert "INFO" in severities

    names_and_descriptions = " ".join(
        f"{definition.alarm_name} {definition.description}".lower()
        for definition in definitions
    )
    for category in (
        "emergency stop",
        "interlock",
        "guard door",
        "safety zone",
        "overtemperature",
        "pressure",
        "vibration",
        "motor thermal overload",
        "sensor",
        "alarm flood",
        "nuisance alarm",
        "communication",
        "telemetry",
    ):
        assert category in names_and_descriptions
