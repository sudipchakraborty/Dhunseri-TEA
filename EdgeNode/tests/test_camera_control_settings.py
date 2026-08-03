from SciCam.camera_control_settings import CameraControlSettings


def test_camera_controls_round_trip(tmp_path):
    path = tmp_path / "camera_controls.json"
    settings = CameraControlSettings(path)
    values = settings.values.copy()
    values.update({
        "exposure": 72,
        "temperature": 83,
        "averaging_window": 35,
        "auto_white_balance": True,
    })

    settings.save(values)
    loaded = CameraControlSettings(path)

    assert loaded.values == values
