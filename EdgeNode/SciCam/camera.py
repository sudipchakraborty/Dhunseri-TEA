class Camera:
    """
    Camera Model
    Stores all camera configuration and runtime objects.
    """

    def __init__(
        self,
        camera_index: int = 0,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30
    ):
        # Camera Object
        self.cap = None

        # Camera Configuration
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps

        # Camera Controls (for future use)
        self.exposure = -6
        self.gain = 0
        self.brightness = 128
        self.contrast = 128
        self.saturation = 128
        self.gamma = 100

        # Auto Controls
        self.auto_exposure = False
        self.auto_white_balance = False
        self.auto_focus = False

        # Runtime Information
        self.is_open = False