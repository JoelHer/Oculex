# backend/ocr/ocr_worker.py
import threading
import queue
import asyncio
import traceback
from typing import Any, Callable


class OcrWorker:
    """
    Background OCR worker queue.

    Usage:
      - Instantiate once (global)
      - Call: results = await ocr_worker.submit(engine, images, config)
    """

    def __init__(self, num_workers: int = 1):
        self._task_queue: queue.Queue = queue.Queue()
        self._threads = []
        self._stop_event = threading.Event()
        self.num_workers = max(1, num_workers)

        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"OCR-Worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)

    async def submit(self, engine: Any, images: list, config: dict):
        """
        Called from asyncio code. Returns OCR results (awaitable).
        engine: instance returned by your factory (per-request)
        images: list of np.ndarray or image-like objects
        config: dict
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        # Put tuple (engine, images, config, future, loop) into queue for worker
        self._task_queue.put((engine, images, config, future, loop))
        return await future

    def stop(self, timeout: float = 2.0):
        """Stop all worker threads cleanly."""
        self._stop_event.set()
        # Put None items to wake up threads
        for _ in self._threads:
            self._task_queue.put(None)
        for t in self._threads:
            t.join(timeout)

    def _worker_loop(self):
        """
        Worker thread loop. Runs OCR tasks pulled from the queue.
        We handle engines that provide:
         - a synchronous `recognize_sync(images, config)` -> call directly
         - a synchronous `recognize(images, config)` -> call directly
         - an async `recognize(images, config)` coroutine function -> run with asyncio.run()
        """
        thread_name = threading.current_thread().name
        while not self._stop_event.is_set():
            try:
                task = self._task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if task is None:
                # sentinel to exit
                break

            engine, images, config, future, loop = task
            try:
                # Choose how to run the engine's recognize method
                results = None

                # prefer explicit sync method if engine provides it
                if hasattr(engine, "recognize_sync") and callable(getattr(engine, "recognize_sync")):
                    results = engine.recognize_sync(images, config)

                # next: plain synchronous recognize (not coroutine)
                elif hasattr(engine, "recognize") and callable(getattr(engine, "recognize")):
                    recognize_attr = getattr(engine, "recognize")
                    # If it's a coroutine/function, run it accordingly
                    if asyncio.iscoroutinefunction(recognize_attr):
                        # run coroutine in this worker thread's event loop (blocking)
                        # Use asyncio.run so we don't interfere with the main loop
                        results = asyncio.run(recognize_attr(images, config))
                    else:
                        # synchronous function, call directly
                        results = recognize_attr(images, config)
                else:
                    raise AttributeError("OCR engine has neither 'recognize_sync' nor 'recognize' method")

                # Post the result back to the original asyncio loop/future thread-safely
                def _set_result():
                    if not future.done():
                        future.set_result(results)

                loop.call_soon_threadsafe(_set_result)

            except Exception as e:
                traceback.print_exc()

                def _set_exc():
                    if not future.done():
                        future.set_exception(e)

                try:
                    loop.call_soon_threadsafe(_set_exc)
                except RuntimeError:
                    # The loop may be closed; just ignore if can't set future
                    pass
            finally:
                try:
                    self._task_queue.task_done()
                except Exception:
                    pass
