from abc import ABC
from abc import abstractmethod
from gabriel_protocol import gabriel_pb2

class CognitiveEngine():

    @staticmethod
    def create_result_wrapper(status):
        result_wrapper = gabriel_pb2.ResultWrapper()
        result_wrapper.status = status
        return result_wrapper

    @staticmethod
    def unpack_extras(extras_class, input_frame):
        extras = extras_class()
        input_frame.extras.Unpack(extras)
        return extras


class Engine(ABC):
    @abstractmethod
    def handle(self, input_frame):
        '''Process a single gabriel_pb2.InputFrame().

        Return an instance of gabriel_pb2.ResultWrapper().'''
        pass
