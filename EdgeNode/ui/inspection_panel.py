from PySide6.QtWidgets import QGridLayout

from .base_panel import BasePanel
from .image_viewer import ImageViewer


class InspectionPanel(BasePanel):
    """
    Displays inspection images.
    """

    def __init__(self):
        super().__init__("Inspection Area")

        self._build_ui()

    def _build_ui(self):

        layout = QGridLayout()

        self.original_viewer = ImageViewer("Original")
        self.white_balance_viewer = ImageViewer("Adjusted Colour")
        self.mask_viewer = ImageViewer("Brown Mask")
        self.histogram_viewer = ImageViewer("Histogram")

        # Show the raw feed and the slider-adjusted result side by side. Keep
        # mask and histogram viewers available for future diagnostics only.
        layout.addWidget(self.original_viewer, 0, 0)
        layout.addWidget(self.white_balance_viewer, 0, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        self.content_layout.addLayout(layout)

    # -------------------------------------------------

    def set_original_image(self, image):
        self.original_viewer.set_image(image)

    def set_white_balance_image(self, image):
        self.white_balance_viewer.set_image(image)

    def set_mask_image(self, image):
        self.mask_viewer.set_image(image)

    def set_histogram_image(self, image):
        self.histogram_viewer.set_image(image)
