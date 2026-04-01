from time import sleep
import threading
import socket
from Lib.console_colored_text import ConsoleColor, ConsoleStyle, colored_text, red_text
from Lib.tcp_client_base import TCPClientBase

# Function
def findSubstring(text, substrings):
  for substring in substrings:
    if substring in text:
      return True
  return False

class PlcLogReader(TCPClientBase):
  """TCP Client to read PLC Log
  """
  
  def __init__(self, host: str, port: int, name: str, console_color: ConsoleColor, timeout: float = 5.0, show_timeout_message: bool= False):
    """Constructor
    """
    super().__init__(host, port, name, console_color, timeout, show_timeout_message)
    self.name = name
    self.console_color = console_color
  
  def run(self, discard_messages = None, show_messages: list[str] | None = None, and_show_messages: list[str] | None = None, replaces = None):
    """Receive data
    """
    try:
      while self.connected:
        try:
          # Receive message
          message = self._receive()

          # Check if message must be discarted
          if discard_messages:
            if findSubstring(message, discard_messages):
              continue
            
          # Check if message must be showed
          if show_messages:
            if not findSubstring(message, show_messages):
              continue
          
          if and_show_messages:
            if not findSubstring(message, and_show_messages):
              continue
          
          # Replace characters in message
          if replaces:
            for find, replace_with in replaces:
              message = message.replace(find, replace_with)
            
          # Show message
          print(colored_text(f'{self.name} >>> {message}', color= self.console_color))
          
        except socket.timeout as e:
          continue  # Continue loop if timeout
        
        except ConnectionError as e:
          break  # Exit loop if connection error
    
    except Exception as e:
      print(colored_text(f"{self.name} >>> Error on main loop:", color=self.console_color), red_text(e.strerror))
      raise
      
class PlcLogReaderThread(threading.Thread):
  """Thread para manejar la conexión a un servidor PLC
  """
  
  def __init__(self, host: str, port: int, server_name: str = None, console_color = None,
              discard_messages=None, show_messages=None, and_show_mesages=None, replaces=None,
              timeout: float = 5.0, show_timeout_message: bool = False):
    
    threading.Thread.__init__(self)
    self.host = host
    self.port = port
    self.server_name = server_name or f"{host}:{port}"
    self.console_color = console_color
    self.discard_messages = discard_messages
    self.show_messages = show_messages
    self.and_show_messages = and_show_mesages
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
              discard_messages=self.discard_messages,
              show_messages=self.show_messages,
              and_show_messages=self.and_show_messages,
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
  
  def add_server(self, host: str, port: int, server_name: str = None, console_color = None,
                discard_messages=None, show_messages=None, and_show_messages=None, replaces=None,
                timeout: float = 5.0, show_timeout_message: bool = False):
    """Añade un servidor a la lista de conexiones
    """
    thread = PlcLogReaderThread(
      host=host,
      port=port,
      server_name=server_name,
      console_color = console_color,
      discard_messages=discard_messages,
      show_messages=show_messages,
      and_show_mesages=and_show_messages,
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

