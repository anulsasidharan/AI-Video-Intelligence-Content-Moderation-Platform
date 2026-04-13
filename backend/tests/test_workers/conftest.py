"""
test_workers conftest — mock cv2 before any app module imports it.

cv2 (OpenCV) may not be available in all test environments. Pre-registering
a MagicMock in sys.modules ensures worker tests that import app.ai.tools
do not fail on the OpenCV binary bootstrap.
"""

import sys
from unittest.mock import MagicMock

if "cv2" not in sys.modules:
    cv2_mock = MagicMock()
    cv2_mock.CAP_PROP_FPS = 0
    cv2_mock.CAP_PROP_FRAME_COUNT = 7
    cv2_mock.IMWRITE_JPEG_QUALITY = 1
    sys.modules["cv2"] = cv2_mock
