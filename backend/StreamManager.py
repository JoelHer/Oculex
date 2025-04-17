#StreamManager
#Keeps track of all the active StreamHandler instances.
#   Each stream gets a unique ID (UUID or user-defined name).
#   Exposes methods: add_stream, remove_stream, get_stream, list_streams.


from backend.StreamHandler import StreamHandler

class StreamManager:
    def __init__(self):
        self.streams = {}

    def add_stream(self, stream_id, rtsp_url, config, processingSettings, selectionBoxes):
        self.streams[stream_id] = StreamHandler(rtsp_url, config, processingSettings, selectionBoxes)

    def get_stream(self, stream_id):
        return self.streams.get(stream_id)

    def list_streams(self):
        return list(self.streams.keys())
