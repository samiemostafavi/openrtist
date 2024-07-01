import asyncio
import time
import logging
import socket
import websockets
import websockets.client
from gabriel_protocol import gabriel_pb2
from collections import namedtuple
import os # code modified


# code modified
MAX_TS_ENTRIES = 100000
TS_SENT_FILE = '/tmp/sent_timestamps_client'

URI_FORMAT = 'ws://{host}:{port}'

logger = logging.getLogger(__name__)
websockets_logger = logging.getLogger(websockets.__name__)

# The entire payload will be printed if this is allowed to be DEBUG
websockets_logger.setLevel(logging.INFO)


ProducerWrapper = namedtuple('ProducerWrapper', ['producer', 'source_name'])


# It isn't necessary to do this as of Python 3.6 because
# "The socket option TCP_NODELAY is set by default for all TCP connections"
# per https://docs.python.org/3/library/asyncio-eventloop.html
# However, this seems worth keeping in case the default behavior changes.
class NoDelayProtocol(websockets.client.WebSocketClientProtocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        super().connection_made(transport)
        sock = transport.get_extra_info('socket')
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


class WebsocketClient:
    def __init__(self, host, port, producer_wrappers, consumer, rate=None):
        '''
        producer should take no arguments and return an instance of
        gabriel_pb2.InputFrame.
        consumer should take one gabriel_pb2.ResultWrapper and does not need to
        return anything.
        '''

        self._welcome_event = asyncio.Event()
        self._sources = {}
        self._running = True
        self._uri = URI_FORMAT.format(host=host, port=port)
        self.producer_wrappers = producer_wrappers
        self.consumer = consumer

        self._sent_timestamp_entries = 0

        if rate is not None:
            self._rate = rate

    def launch(self, message_max_size=None):
        event_loop = asyncio.get_event_loop()

        try:
            self._websocket = event_loop.run_until_complete(
                websockets.connect(self._uri, create_protocol=NoDelayProtocol,
                                   max_size=message_max_size))
        except ConnectionRefusedError:
            logger.error('Could not connect to server')
            return

        address_str = f"{self._websocket.local_address[0]}_{self._websocket.local_address[1]}"
        # self._sent_tsfile_str = TS_SENT_FILE+address_str.replace(".", "_").replace(":", "_") + ".txt"
        self._sent_tsfile_str = TS_SENT_FILE + ".txt"

        # self._sent_timestamp_file =  open(self._sent_tsfile_str, "w+").close()  # start with a blank file
        self._sent_timestamp_file = open(self._sent_tsfile_str, 'a')

        # We don't waste time checking TCP_NODELAY in production.
        # Note that websocket.transport is an undocumented property.
        # sock = self._websocket.transport.get_extra_info('socket')
        # assert(sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) == 1)

        consumer_task = asyncio.ensure_future(self._consumer_handler())
        tasks = [
            asyncio.ensure_future(self._producer_handler(
                producer_wrapper.producer, producer_wrapper.source_name))
            for producer_wrapper in self.producer_wrappers
        ]
        tasks.append(consumer_task)

        _, pending = event_loop.run_until_complete(asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED))
        for task in pending:
            task.cancel()
        logger.info('Disconnected From Server')

    def get_source_names(self):
        return self._sources.keys()

    def stop(self):
        self._running = False
        logger.info('stopping server')

    async def _consumer_handler(self):
        while self._running:
            try:
                raw_input = await self._websocket.recv()
            except websockets.exceptions.ConnectionClosed:
                return  # stop the handler
            logger.debug('Received input from server')

            to_client = gabriel_pb2.ToClient()
            to_client.ParseFromString(raw_input)

            if to_client.HasField('welcome'):
                self._process_welcome(to_client.welcome)
            elif to_client.HasField('response'):
                self._process_response(to_client.response)
            else:
                raise Exception('Empty to_client message')

    def _process_welcome(self, welcome):
        for source_name in welcome.sources_consumed:
            self._sources[source_name] = _Source(welcome.num_tokens_per_source)
        self._welcome_event.set()

    def _process_response(self, response, measurements=None):
        result_wrapper = response.result_wrapper
        if (result_wrapper.status == gabriel_pb2.ResultWrapper.SUCCESS):
            if measurements:
                self.consumer(result_wrapper, measurements)
            else:
                self.consumer(result_wrapper)

        elif (result_wrapper.status ==
              gabriel_pb2.ResultWrapper.NO_ENGINE_FOR_SOURCE):
            raise Exception('No engine for source')
        else:
            status = result_wrapper.Status.Name(result_wrapper.status)
            logger.error('Output status was: %s', status)

        if response.return_token:
            self._sources[response.source_name].return_token()

    async def _producer_handler(self, producer, source_name):
        '''
        Loop waiting until there is a token available. Then calls producer to
        get the gabriel_pb2.InputFrame to send.
        '''

        await self._welcome_event.wait()
        source = self._sources.get(source_name)
        assert source is not None, (
            "No engines consume frames from source: {}".format(source_name))

        while self._running:
            await source.get_token()
            
            # adjust the rate
            if self._rate is not None:
                await asyncio.sleep(1.0/self._rate)

            input_frame = await producer()
            if input_frame is None:
                source.return_token()
                logger.info('Received None from producer')
                continue
            
            # code modified
            if self._sent_timestamp_entries == MAX_TS_ENTRIES:
                self._sent_timestamp_file = open(self._sent_tsfile_str, 'w').close()
                self._sent_timestamp_file = open(self._sent_tsfile_str, 'a')
                self._sent_timestamp_entries = 0
                
            self._sent_timestamp_file.write(f"{self._websocket.local_address} {source.get_frame_id()} {time.time_ns()}\n")
            self._sent_timestamp_file.flush()
            self._sent_timestamp_entries += 1
            # print(f"send a frame at {time.time_ns()}, frame_id: {source.get_frame_id()}")
            # code modified END

            from_client = gabriel_pb2.FromClient()
            from_client.frame_id = source.get_frame_id()
            from_client.source_name = source_name
            from_client.input_frame.CopyFrom(input_frame)

            try:
                await self._send_from_client(from_client)
            except websockets.exceptions.ConnectionClosed:
                return  # stop the handler

            logger.debug('num_tokens for %s is now %d', source_name,
                         source.get_num_tokens())
            source.next_frame()

    async def _send_from_client(self, from_client):
        # Removing this method will break measurement_client

        await self._websocket.send(from_client.SerializeToString())


class _Source:
    def __init__(self, num_tokens):
        self._num_tokens = num_tokens
        self._event = asyncio.Event()
        self._frame_id = 0

    def return_token(self):
        self._num_tokens += 1
        self._event.set()

    async def get_token(self):
        while self._num_tokens < 1:
            logger.debug('Waiting for token')
            self._event.clear()  # Clear because we definitely want to wait
            await self._event.wait()

        self._num_tokens -= 1

    def get_num_tokens(self):
        return self._num_tokens

    def get_frame_id(self):
        return self._frame_id

    def next_frame(self):
        self._frame_id += 1
