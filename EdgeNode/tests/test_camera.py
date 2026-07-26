from SciCam.camera_manager import CameraManager

manager = CameraManager()

devices = manager.discover()

print(f"Found {len(devices)} camera(s)\n")

for device in devices:
    print(device)