import unittest
from unittest.mock import MagicMock, patch
import socket
from outbound_tester import OutboundTester


# import your class
# from outbound_tester import OutboundTester


class TestOutboundTester(unittest.TestCase):

    def setUp(self):
        # Create instance without calling __init__ (avoids Tkinter)
        self.tester = OutboundTester.__new__(OutboundTester)

        # Mock UI-related attributes for state testing
        self.tester.is_running = False
        self.tester.stop_flag = False

        self.tester.start_btn = MagicMock()
        self.tester.stop_btn = MagicMock()
        self.tester.clear_btn = MagicMock()
        self.tester.progress_label = MagicMock()

    # ------------------------------------------------
    # Test 1: Open Port Detection
    # ------------------------------------------------
    @patch("socket.socket")
    def test_open_port(self, mock_socket):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock

        status, elapsed, message = self.tester.test_port("youtube.com", 80, 1)

        self.assertEqual(status, "open")
        self.assertEqual(message, "Connection successful")
        self.assertGreaterEqual(elapsed, 0)

    # ------------------------------------------------
    # Test 2: Closed Port Detection
    # ------------------------------------------------
    @patch("socket.socket")
    def test_closed_port(self, mock_socket):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111
        mock_socket.return_value = mock_sock

        status, _, message = self.tester.test_port("youtube.com", 81, 1)

        self.assertEqual(status, "closed")
        self.assertEqual(message, "Connection refused")

    # ------------------------------------------------
    # Test 3: Filtered Port Detection (Timeout)
    # ------------------------------------------------
    @patch("socket.socket")
    def test_filtered_port_timeout(self, mock_socket):
        mock_sock = MagicMock()
        mock_sock.connect_ex.side_effect = socket.timeout
        mock_socket.return_value = mock_sock

        status, _, message = self.tester.test_port("example.com", 82, 1)

        self.assertEqual(status, "filtered")
        self.assertEqual(message, "Connection timeout")

    # ------------------------------------------------
    # Test 4: Hostname Resolution Failure
    # ------------------------------------------------
    @patch("socket.socket")
    def test_hostname_resolution_failure(self, mock_socket):
        mock_sock = MagicMock()
        mock_sock.connect_ex.side_effect = socket.gaierror
        mock_socket.return_value = mock_sock

        status, elapsed, message = self.tester.test_port("invalid.host", 80, 1)

        self.assertEqual(status, "error")
        self.assertEqual(elapsed, 0)
        self.assertEqual(message, "Hostname resolution failed")

    # ------------------------------------------------
    # Test 5: Application State Management (Non-GUI)
    # ------------------------------------------------
    def test_application_state_management(self):
        # Start test
        self.tester.start_test()

        self.assertTrue(self.tester.is_running)
        self.tester.start_btn.config.assert_called_with(state="disabled")
        self.tester.stop_btn.config.assert_called_with(state="normal")

        # Reset UI
        self.tester.reset_ui()

        self.assertFalse(self.tester.is_running)
        self.tester.start_btn.config.assert_called_with(state="normal")
        self.tester.stop_btn.config.assert_called_with(state="disabled")


if __name__ == "__main__":
    unittest.main()
