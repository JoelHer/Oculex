#StreamManager
#Keeps track of all the active StreamHandler instances.
#   Each stream gets a unique ID (UUID or user-defined name).
#   Exposes methods: add_stream, remove_stream, get_stream, list_streams.


from backend.StreamHandler import StreamHandler
from backend.database.models import Stream, StreamSettings, SelectionBox

class StreamManager:
    def __init__(self, session):
        self.streams = {}
        print("[StreamManager] Loading streams from database...")
        self.load_streams_from_db(session)


    def add_stream(self, stream_id, rtsp_url, config, processingSettings, selectionBoxes):
        self.streams[stream_id] = StreamHandler(rtsp_url, config, processingSettings, selectionBoxes)
        print(f"[StreamManager] Added stream with ID: {stream_id}")

    def get_stream(self, stream_id):
        return self.streams.get(stream_id)

    def list_streams(self):
        return list(self.streams.keys())

    def load_streams_from_db(self, dbSession):
        db = dbSession()
        streams = db.query(Stream).all()
        for stream in streams:
            stream_id = str(stream.id)
            rtsp_url = stream.rtsp_url
            print(f"[StreamManager] Loading stream {rtsp_url} from database...")
            config = {}
            processingSettings = db.query(StreamSettings).filter(StreamSettings.stream_id == stream.id).first()
            selectionBoxes = db.query(SelectionBox).filter(SelectionBox.stream_id == stream.id).all()
            selectionBoxes = [box.to_dict() for box in selectionBoxes]
            
            self.add_stream(stream_id, rtsp_url, config, processingSettings, selectionBoxes)

        db.close()