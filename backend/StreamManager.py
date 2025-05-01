#StreamManager
#Keeps track of all the active StreamHandler instances.
#   Each stream gets a unique ID (UUID or user-defined name).
#   Exposes methods: add_stream, remove_stream, get_stream, list_streams.


from backend.StreamHandler import StreamHandler
import json

class StreamManager:
    """
    StreamManager
    Keeps track of all the active StreamHandler instances.
    """
    def __init__(self, ws_manager=None, verbose_logging=False):
        self.streams = {}
        self.ws_manager = ws_manager
        self.VERBOSE_LOGGING = verbose_logging
        self.store_location = "/data/streams.json"

    def add_stream(self, stream_id, rtsp_url, config, processingSettings, selectionBoxes):
        self.streams[stream_id] = StreamHandler(stream_id, rtsp_url, config, processingSettings, selectionBoxes, ws_manager=self.ws_manager)
        if self.VERBOSE_LOGGING:
            print(f"[StreamManager] Added stream with ID: {stream_id}")

    def get_stream(self, stream_id):
        """Return the stream handler for the given stream ID."""
        return self.streams.get(stream_id)

    def set_store_location(self, filepath):
        self.store_location = filepath

    def list_streams(self):
        return list(self.streams.keys())

    def store_streams(self, filename=None):
        if not filename:
            filename = self.store_location
        """Store the current streams to the specified file."""
        data = {}
        for stream_id, handler in self.streams.items():
            data[stream_id] = {
                "rtsp_url": handler.rtsp_url,
                "config": handler.config,
                "processingSettings": handler.processingSettings,
                "selectionBoxes": handler.selectionBoxes
            }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        if self.VERBOSE_LOGGING:
            print(f"[StreamManager] Stored {len(self.streams)} streams to {filename}")

    def load_streams(self, filename):
        """Load streams from the specified file."""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            for stream_id, info in data.items():
                rtsp_url = info.get("rtsp_url", "")
                config = info.get("config", {})
                processingSettings = info.get("processingSettings", {})
                selectionBoxes = info.get("selectionBoxes", {})  # maybe old saves don't have this

                self.add_stream(
                    stream_id,
                    rtsp_url,
                    config,
                    processingSettings,
                    selectionBoxes
                )
            if self.VERBOSE_LOGGING:
                print(f"[StreamManager] Loaded {len(data)} streams from {filename}")
        except FileNotFoundError:
            if self.VERBOSE_LOGGING:
                print(f"[StreamManager] No previous streams file found ({filename}). Starting fresh.")
