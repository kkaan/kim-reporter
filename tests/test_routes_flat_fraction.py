from fastapi import HTTPException

from kim_app.api.routes import _load_fraction_payload
from kim_app.api.schema import FractionRequest


def test_load_fraction_payload_accepts_flat_fraction_layout(tmp_path):
    patient_dir = tmp_path / "Patient_258215"
    fx_dir = patient_dir / "FX03"
    fx_dir.mkdir(parents=True)

    centroid_file = tmp_path / "Centroid_Patient_258215.txt"
    centroid_file.write_text(
        "\n".join(
            [
                "Seed 1, X=0.0, Y=0.0, Z=0.0",
                "Seed 2, X=0.0, Y=0.0, Z=0.0",
                "Isocenter (cm), X=0.0, Y=0.0, Z=0.0",
            ]
        ),
        encoding="utf-8",
    )

    trajectory_file = fx_dir / "MarkerLocationsGA_CouchShift_0.txt"
    trajectory_file.write_text(
        "\n".join(
            [
                (
                    "Frame No,Time (sec),Gantry,"
                    "Marker_0_AP,Marker_0_LR,Marker_0_SI,"
                    "Marker_1_AP,Marker_1_LR,Marker_1_SI"
                ),
                "1,10.0,0.0,0.1,0.2,0.3,0.1,0.2,0.3",
                "2,10.5,0.0,0.1,0.2,0.3,0.1,0.2,0.3",
            ]
        ),
        encoding="utf-8",
    )

    req = FractionRequest(
        patient_dir=str(patient_dir),
        fraction_id="FX03",
        centroid_file=str(centroid_file),
    )

    try:
        payload = _load_fraction_payload(req)
    except HTTPException as exc:
        raise AssertionError(f"flat fraction layout should load, got {exc.detail}") from exc

    assert payload.patient_id == "Patient_258215"
    assert payload.fraction_id == "FX03"
    assert payload.time_real_s == [0.0, 0.5]
    assert payload.detected_markers == [0, 1]
