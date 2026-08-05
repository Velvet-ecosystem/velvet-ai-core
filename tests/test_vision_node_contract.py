import unittest

from velvet.core.vision_node_contract import (
    CameraChannelStatus,
    VisionHealth,
    assess_vision_node,
)


class TestVisionNodeContract(unittest.TestCase):
    def test_one_camera_loss_degrades_without_collapsing_node(self):
        result = assess_vision_node(
            (
                CameraChannelStatus("front", True, 0.99, 0.01, 0, 45.0),
                CameraChannelStatus("rear", False, 0.0, 1.0, 3, 30.0),
            )
        )
        self.assertEqual(result.health, VisionHealth.DEGRADED)
        self.assertEqual(result.available_cameras, ("front",))
        self.assertIn("rear", result.degraded_cameras)
        self.assertFalse(result.raw_stream_default)
        self.assertFalse(result.authority_granted)

    def test_all_cameras_offline_fails_node(self):
        result = assess_vision_node(
            (CameraChannelStatus("front", False, 0.0, 1.0, 1, 30.0),)
        )
        self.assertEqual(result.health, VisionHealth.FAILED)


if __name__ == "__main__":
    unittest.main()
