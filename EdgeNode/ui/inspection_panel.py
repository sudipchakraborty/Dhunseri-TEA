from .base_panel import BasePanel
from .image_viewer import ImageViewer


class InspectionPanel(BasePanel):
    """
    Displays inspection images.
    """

    def __init__(self):
        super().__init__("Visual AI")

        self._build_ui()

    def _build_ui(self):
        self.original_viewer = ImageViewer("AI Camera")
        self.content_layout.addWidget(self.original_viewer)

    # -------------------------------------------------

    def set_original_image(self, image):
        self.original_viewer.set_image(image)
