import socket
from Lib.console_colored_text import ConsoleColor, ConsoleStyle, ConsoleBackground, colored_text, red_text

class TCPClientBase:
  """Clase base para los clientes TCP con gestión de conexión
  """
    
  def __init__(self, host: str, port: int, name: str, console_color: ConsoleColor, timeout: float = 5.0, show_timeout_message: bool= False):
    """Constructor
    """
    self.host = host
    self.port = port
    self.name = name
    self.console_color = console_color
    self.timeout = timeout
    self.socket = None
    self.connected = False
    self.show_timeout_message = show_timeout_message
    
  def __enter__(self):
    """Enter
    """
    self.connect()
    return self
  
  def __exit__(self, exc_type, exc_val, exc_tb):
    """Exit
    """
    self.close()
    if exc_type is not None:
      print(colored_text(f"{self.name} >>> Error:", color=self.console_color), red_text(exc_val))
    return False  # No manejamos la excepción, la propagamos
  
  def connect(self):
    """Establece la conexión con el servidor
    """
    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.settimeout(self.timeout)
      self.socket.connect((self.host, self.port))
      self.connected = True
      print(colored_text(f'{self.name} >>> Connected to {self.host}:{self.port}', color= self.console_color))
      
    except socket.error as e:
      self.connected = False
      print(colored_text(f"{self.name} >>> Connection error:", color=self.console_color), red_text(e.strerror))
      raise
  
  def close(self):
    """Cierra la conexión
    """
    if self.socket:
      try:
        self.socket.close()
        print(colored_text(f"{self.name} >>> Connection closed!", color=self.console_color))
        
      except socket.error as e:
        print(colored_text(f"{self.name} >>> Error closing connection:", color=self.console_color), red_text(e.strerror))
        
      finally:
        self.socket = None
        self.connected = False
  
  def _send(self, data: str):
    """Envía datos al servidor
    """
    if not self.connected:
      raise ConnectionError(f"{self.name} >>> It is not connected to Server")
    
    try:
      self.socket.sendall(data.encode('utf-8'))
      
    except socket.error as e:
      self.connected = False
      print(colored_text(f"{self.name} >>> Error sending data:", color=self.console_color), red_text(e.strerror))
      raise
  
  def _receive(self, buffer_size: int = 4096) -> str:
    """Recibe datos del servidor
    """
    if not self.connected:
      raise ConnectionError(f"{self.name} >>> It is not connected to Server")
    
    try:
      data = self.socket.recv(buffer_size)
      if not data:
        self.connected = False
        raise ConnectionError(f"{self.name} >>> Connection closed by Server")
      return data.decode('utf-8')
    
    except socket.timeout:
      if self.show_timeout_message:
        print(colored_text(f"{self.name} >>> Timeout while receiving data", color=self.console_color))
      raise
    
    except socket.error as e:
      self.connected = False
      print(colored_text(f"{self.name} >>> Error receiving data:", color=self.console_color), red_text(e.strerror))
      raise
