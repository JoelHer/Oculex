#StreamHandler
#    Manages one RTSP stream.
#    Has its own:
#        Frame grabber
#        Processing pipeline
#        Config

import cv2
import av
import numpy as np

class StreamHandler:
    def __init__(self, rtsp_url, config, processingSettings, selectionBoxes):
        self.rtsp_url = rtsp_url
        self.config = config
        self.processingSettings = processingSettings
        self.selectionBoxes = selectionBoxes
        self.frame = None
        # Init grabbing, OCR, etc.

    async def grab_frame_raw(self):
        print(f"[StreamHandler] Trying to open the RTSP stream at {self.rtsp_url}")
        
        if self.rtsp_url.startswith("file://"):
            file_path = self.rtsp_url[7:]
            print(f"[StreamHandler] Opening file {file_path} instead of RTSP stream")
            
            try:
                container = av.open(file_path)
                frame = None
                for packet in container.demux(video=0):
                    for frame in packet.decode():
                        img = frame.to_image()  # Convert frame to PIL Image
                        frame = np.array(img)   # Convert to NumPy array
                        break  # Grab only one frame
                    if frame is not None:
                        break

                if frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame)
                    return buffer.tobytes()
                else:
                    print(f"[StreamHandler] No frames found in the file {file_path}")
                    return None

            except Exception as e:
                print(f"[StreamHandler] Error opening file {file_path}: {e}")
                return None

        else:
            try:
                container = av.open(self.rtsp_url, options={"rtsp_transport": "tcp"})
                frame = None
                for packet in container.demux(video=0):
                    for frame in packet.decode():
                        img = frame.to_image()  # Convert frame to PIL Image
                        frame = np.array(img)   # Convert to NumPy array
                        break  # Just grab one frame
                    if frame is not None:
                        break

                if frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame)
                    return buffer.tobytes()
                else:
                    print(f"[StreamHandler] No frames found in the RTSP stream at {self.rtsp_url}")
                    return None

            except Exception as e:
                print(f"[StreamHandler] Error opening RTSP stream with url {self.rtsp_url}: {e}")
                return None

    async def grab_frame(self, displayBoxes=True):
        print(f"[StreamHandler] Trying to open the RTSP stream at {self.rtsp_url}")
        try:
            # Use av.open with RTSP options
            container = av.open(self.rtsp_url, options={"rtsp_transport": "tcp"})
            frame = None
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()  # Convert frame to PIL Image
                    frame = np.array(img)   # Convert to NumPy array
                    break  # Just grab one frame
                if frame is not None:
                    break

            if self.processingSettings["rotation"] != 0 and frame is not None:
                (h, w) = frame.shape[:2]
                center = (w // 2, h // 2)
                matrix = cv2.getRotationMatrix2D(center, self.processingSettings["rotation"], 1.0)
                frame = cv2.warpAffine(frame, matrix, (w, h))

            # Apply contrast & brightness
            if frame is not None:
                frame = cv2.convertScaleAbs(frame, alpha=self.processingSettings["contrast"], beta=self.processingSettings["brightness"])

            # Apply cropping
            if frame is not None:
                h, w, _ = frame.shape
                top = min(self.processingSettings["crop_top"], h)
                bottom = max(h - self.processingSettings["crop_bottom"], 0)
                left = min(self.processingSettings["crop_left"], w)
                right = max(w - self.processingSettings["crop_right"], 0)
                frame = frame[top:bottom, left:right]

            # Draw self.selectionBoxes on the image
            if frame is not None:
                if self.selectionBoxes is not None and len(self.selectionBoxes) > 0:
                    for box in self.selectionBoxes:
                        box_top = box["box_top"]
                        box_left = box["box_left"]
                        box_width = box["box_width"]
                        box_height = box["box_height"]
                        color = (0, 255, 0)  # Default color
                        if displayBoxes:
                            cv2.rectangle(frame, (box_left, box_top), (box_left + box_width, box_top + box_height), color, 2)
                            cv2.putText(frame, f'ID: {box["id"]}', (box_left, box_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


            
            
            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                return buffer.tobytes()
            else:
                print(f"[StreamHandler] No frames found in the RTSP stream at {self.rtsp_url}")
                return None

        except Exception as e:
            print(f"[StreamHandler] Error opening RTSP stream with url {self.rtsp_url}: {e}")
            return None

    async def grab_computed_freme(self):
        frame = await self.grab_frame(displayBoxes=False)  # Add 'await' here
        if frame is None:
            return "Error: Could not retrieve frame", 500

        np_frame = np.frombuffer(frame, np.uint8)
        image = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        if image is None:
            return "Error: Could not decode frame", 500

        snippets = []
        for box in self.selectionBoxes:
            box_top = box["box_top"]
            box_left = box["box_left"]
            box_width = box["box_width"]
            box_height = box["box_height"]

            snippet = image[box_top:box_top + box_height, box_left:box_left + box_width]
            if snippet.size > 0:
                snippets.append(snippet)

        if not snippets:
            return "Error: No valid boxes to process", 400

        target_height = max(snippet.shape[0] for snippet in snippets)
        resized_snippets = [cv2.resize(snippet, (snippet.shape[1], target_height)) for snippet in snippets]

        stitched_image = cv2.hconcat(resized_snippets)

        _, buffer = cv2.imencode(".jpg", stitched_image)
        return buffer.tobytes()

    def process_frame(self):
        # Return image with overlay
        pass

    def get_settings(self):
        return self.processingSettings
    
    def set_settings(self, settings):
        self.processingSettings = settings

    def get_boxes(self):
        return self.selectionBoxes
    
    def set_boxes(self, boxes):
        self.selectionBoxes = boxes
