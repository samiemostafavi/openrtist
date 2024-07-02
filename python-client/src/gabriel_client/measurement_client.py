from gabriel_client.websocket_client import WebsocketClient
from gabriel_client.websocket_client import ProducerWrapper
import time
import logging
import os # code modified

MAX_TS_ENTRIES = 100000
TS_RECV_FILE = '/tmp/recv_timestamps_client'

logger = logging.getLogger(__name__)

class MeasurementClient(WebsocketClient):
    def __init__(self, host, port, producer_wrappers, consumer, output_freq=1, rate=None):
        super().__init__(host, port, producer_wrappers, consumer, rate)

        # code modified
        self._recv_timestamp_file = None
        self._recv_timestamp_entries = 0

        self._source_measurements = {}
        self._output_freq = output_freq

    def _process_welcome(self, welcome):
        super()._process_welcome(welcome)
        start_time = time.time()
        for source_name in welcome.sources_consumed:
            source_measurement = _SourceMeasurement(
                start_time, self._output_freq)
            self._source_measurements[source_name] = source_measurement

    def _process_response(self, response):
        response_time = time.time()
        if response.return_token:
            source_measurement = self._source_measurements[response.source_name]
            source_measurement.process_response(
                response.frame_id, response.source_name, response_time)
            measurements = [
                source_measurement._overall_fps,
                source_measurement._interval_fps,
                source_measurement._avg_rtt,
            ]

        # code modified
        if self._recv_timestamp_entries == MAX_TS_ENTRIES:
            # clean the file
            self._recv_timestamp_file = open(self._recv_tsfile_str, 'w').close()
            self._recv_timestamp_file = open(self._recv_tsfile_str, 'a')
            self._recv_timestamp_entries = 0

        if self._recv_timestamp_file is None:
            # address_str = f"{self._websocket.local_address[0]}_{self._websocket.local_address[1]}"
            # self._recv_tsfile_str = TS_RECV_FILE+address_str.replace(".", "_").replace(":", "_") + ".txt"
            # self._recv_timestamp_file = open(self._recv_tsfile_str, 'w+').close()
            self._recv_tsfile_str = TS_RECV_FILE + ".txt"
            self._recv_timestamp_file = open(self._recv_tsfile_str, 'a')

        remote_port = self._websocket.remote_address[1]
        self._recv_timestamp_file.write(f"{remote_port} {response.frame_id} {time.time_ns()}\n")
        self._recv_timestamp_file.flush()
        self._recv_timestamp_entries += 1

        # print(f"send a frame at {time.time_ns()}, frame_id: {source.get_frame_id()}")
        # code modified END

        # print(f"got a response at {time.time_ns()}, frame_id: {response.frame_id}")
        super()._process_response(response,measurements)

    async def _send_from_client(self, from_client):
        await super()._send_from_client(from_client)
        send_time = time.time()
        source_measurement = self._source_measurements[from_client.source_name]
        source_measurement.log_send(from_client.frame_id, send_time)

class _SourceMeasurement:
    def __init__(self, start_time, output_freq):
        self._count = 0
        self._send_timestamps = {}
        self._recv_timestamps = {}
        self._start_time = start_time
        self._interval_start_time = start_time
        self._output_freq = output_freq
        self._source_name = ""
        self._overall_fps = 0.0
        self._interval_fps = 0.0
        self._avg_rtt = 0.0

    def process_response(self, frame_id, source_name, response_time):
        self._recv_timestamps[frame_id] = response_time
        self._count += 1

        if (self._count % self._output_freq) == 0:
            self._compute_and_print(source_name, response_time)
            self._interval_start_time = time.time()

    def _compute_and_print(self, source_name, response_time):
        self._source_name = source_name
        #print('Measurements for source:', source_name)
        overall_fps = _compute_fps(self._count, response_time, self._start_time)
        self._overall_fps = overall_fps
        #print('Overall FPS:', overall_fps)
        interval_fps = _compute_fps(
            self._output_freq, response_time, self._interval_start_time)
        self._interval_fps = interval_fps
        #print('Interval FPS:', interval_fps)

        total_rtt = 0
        for frame_id, received in self._recv_timestamps.items():
            sent = self._send_timestamps[frame_id]
            total_rtt += (received - sent)
            del self._send_timestamps[frame_id]

        #print('Average RTT for interval:', total_rtt / self._output_freq)
        self._avg_rtt = total_rtt / self._output_freq
        self._recv_timestamps.clear()

    def log_send(self, frame_id, send_time):
        self._send_timestamps[frame_id] = send_time


def _compute_fps(num_frames, current_time, start_time):
    return num_frames / (current_time - start_time)
