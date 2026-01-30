from io import StringIO
import logging, time, os


class Logger(logging.Logger):

    _timer = None

    @classmethod
    def kst(cls, *args):
        return time.localtime(time.mktime(time.gmtime()) + 9 * 3600)

    def __init__(self, file:str='', clean_record:bool=False):

        formatter = logging.Formatter(
            fmt=f"%(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        formatter.converter = self.kst

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        self._buffer = StringIO()
        memory = logging.StreamHandler(stream=self._buffer)
        memory.setLevel(logging.INFO)
        memory.setFormatter(formatter)

        super().__init__(name='pyems', level=logging.DEBUG)

        self.file = file
        self.propagate = False
        self.addHandler(console_handler)
        self.addHandler(memory)
        if file:
            if os.path.exists(file) and clean_record:
                os.remove(file)
            file_handler = logging.FileHandler(file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)
        self._held = ''
        return

    def __call__(self, io:str):
        return self.info(io)

    @property
    def stream(self) -> str:
        return self._buffer.getvalue()

    def log(self, msg:str='', *args, **kwargs):
        if self._held:
            msg = self._held + msg
        super().info(msg, *args, **kwargs)
        self._held = ''
        return

    def read(self, file:str=''):
        if not file:
            file = self.file
        with open(file, 'r', encoding="utf-8") as f:
            return f.read()

    def hold(self, msg:str):
        self._held += msg

    def run(self, context:str=''):
        if context:
            self.info(context)
        self._timer = time.perf_counter()
        return

    def end(self, context:str=''):
        try:
            context = f'{context} {time.perf_counter() - self._timer:.2f}s'
            self.info(context)
        except (AttributeError, TypeError, Exception):
            raise RuntimeError('Logger is not started. Please call .run() method first.')
        return
