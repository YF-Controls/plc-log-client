from time import sleep
import threading
import socket
from lib.console_colored_text import ConsoleColor, ConsoleStyle, colored_text, red_text
from lib.tcp_client_base import TCPClientBase

# Function
def matches_filter(text: str, show_messages: list[list[str]]) -> bool:
  """Returns True if text satisfies all AND groups, each group being an OR of substrings."""
  return all(
    any(substring in text for substring in group)
    for group in show_messages
  )

class FragmentAssembler:
  """Reassembles fragmented PLC log messages.

  Header format (17 chars fixed):
    [0:5]  totalLength  - total length of the assembled message
    [5:8]  partLength   - payload length of this fragment
    [8:12] parts        - total number of fragments
    [12:16] part        - index of this fragment (base 1)
    [16]   ';'          - separator
    [17:]  payload      - fragment data (partLength chars)

  Fragments must arrive in order (part 1, 2, ..., parts).
  Out-of-sequence fragments discard the current buffer and
  return DISCARD. A new cycle starts when part == 1 arrives.
  """

  DISCARD = object()  # Sentinel: out-of-sequence fragment received

  def __init__(self):
    self._chunks: list[str] = []
    self._next_part: int = 1

  def feed(self, raw: str) -> str | None | object:
    """Process one received fragment.

    Returns:
      str              : complete assembled message (all parts received)
      None             : fragment accepted, waiting for more parts
      DISCARD sentinel : out-of-sequence fragment, current buffer discarded
    """
    parts       = int(raw[8:12])
    part        = int(raw[12:16])
    part_length = int(raw[5:8])
    payload     = raw[17:17 + part_length]

    if part != self._next_part:
      # Unexpected fragment: reset and signal caller
      self._chunks = []
      self._next_part = 1
      if part != 1:
        return FragmentAssembler.DISCARD
      # part == 1 after reset: start new cycle (fall through)

    if part == 1:
      self._chunks = []

    self._chunks.append(payload)
    self._next_part = part + 1

    if part == parts:
      message = ''.join(self._chunks)
      self._chunks = []
      self._next_part = 1
      return message

    return None  # Still waiting for more fragments


class PlcLogReader(TCPClientBase):
  """TCP Client to read PLC Log
  """
  
  def __init__(self, host: str, port: int, name: str, console_color: ConsoleColor, timeout: float = 5.0, show_timeout_message: bool= False):
    """Constructor
    """
    super().__init__(host, port, name, console_color, timeout, show_timeout_message)
    self.name = name
    self.console_color = console_color
  
  def run(self,
          fragmented_log: bool = False,
          discard_messages: list[str] | None = None,
          show_messages: list[list[str]] | None = None,
          replaces: list[list[str]] | None = None):
    """
    Receive data
    """
    assembler = FragmentAssembler() if fragmented_log else None

    try:
      while self.connected:
        try:
          # Receive raw fragment or full message
          raw = self._receive()

          if assembler:
            result = assembler.feed(raw)
            if result is FragmentAssembler.DISCARD:
              print(colored_text(f'{self.name} >>> Unknown fragmented message received', color=self.console_color))
              continue
            if result is None:
              continue  # Waiting for more fragments
            message = result
          else:
            message = raw

          # Check if message must be discarded
          if discard_messages:
            if any(s in message for s in discard_messages):
              continue

          # Check if message must be showed (AND of ORs)
          if show_messages:
            if not matches_filter(message, show_messages):
              continue

          # Replace characters in message
          if replaces:
            for find, replace_with in replaces:
              message = message.replace(find, replace_with)

          # Show message
          print(colored_text(f'{self.name} >>> {message}', color=self.console_color))

        except socket.timeout:
          continue  # Continue loop if timeout

        except ConnectionError:
          break  # Exit loop if connection error

    except Exception as e:
      print(colored_text(f"{self.name} >>> Error on main loop:", color=self.console_color), red_text(e.strerror))
      raise
      
class PlcLogReaderThread(threading.Thread):
  """Thread para manejar la conexión a un servidor PLC
  """
  
  def __init__(self, host: str,  fragmented_log: bool, port: int, server_name: str = None, console_color = None,
              discard_messages=None, show_messages=None, replaces=None,
              timeout: float = 5.0, show_timeout_message: bool = False):
    
    threading.Thread.__init__(self)
    self.host = host
    self.fragmented_log = fragmented_log
    self.port = port
    self.server_name = server_name or f"{host}:{port}"
    self.console_color = console_color
    self.discard_messages = discard_messages
    self.show_messages = show_messages
    self.replaces = replaces
    self.timeout = timeout
    self.show_timeout_message = show_timeout_message
    self.running = True
    self.daemon = True  # Hilo daemon para que termine con el programa principal
  
  def run(self):
    """Método principal del hilo
    """
    print(colored_text(f"{self.server_name} >>> Thread started", color= self.console_color))
    
    while self.running:
      try:
        with PlcLogReader(self.host, self.port, self.server_name, self.console_color,  
                        self.timeout, self.show_timeout_message) as plc:
          plc.run(
              fragmented_log=self.fragmented_log,
              discard_messages=self.discard_messages,
              show_messages=self.show_messages,
              replaces=self.replaces
          )
      
      except Exception as e:
        print(colored_text(f"{self.server_name} >>> Channel error:", color=self.console_color), red_text(e.__str__()))
      
      if self.running:
        print(colored_text(f"{self.server_name} >>> Wait 5 seconds!", color=self.console_color))
        sleep(5.0)
    
    print(colored_text(f"{self.server_name} >>> Thread stopped", color=self.console_color ))
  
  def stop(self):
    """Detiene el hilo
    """
    self.running = False

class PlcMultiServerManager:
  """Gestor para múltiples conexiones PLC
  """
  
  def __init__(self):
    self.threads = []
  
  def add_server(self, host: str, fragmented_log: bool,
                 port: int, server_name: str = None, console_color = None,
                 discard_messages=None, show_messages=None, replaces=None,
                 timeout: float = 5.0, show_timeout_message: bool = False):
    """Añade un servidor a la lista de conexiones
    """
    thread = PlcLogReaderThread(
      fragmented_log=fragmented_log,
      host=host,
      port=port,
      server_name=server_name,
      console_color = console_color,
      discard_messages=discard_messages,
      show_messages=show_messages,
      replaces=replaces,
      timeout=timeout,
      show_timeout_message=show_timeout_message
    )
    self.threads.append(thread)
    return thread
  
  def start_all(self):
    """Inicia todas las conexiones
    """
    print("Starting all PLC connections...")
    for thread in self.threads:
      thread.start()
  
  def stop_all(self):
    """Detiene todas las conexiones
    """
    print("Stopping all PLC connections...")
    for thread in self.threads:
      thread.stop()
    
    # Esperar a que terminen los hilos
    for thread in self.threads:
      thread.join(timeout=2)
  
  def is_any_alive(self):
    """Verifica si algún hilo sigue activo
    """
    return any(thread.is_alive() for thread in self.threads)

