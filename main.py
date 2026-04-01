from time import sleep
from Lib.console_colored_text import ConsoleColor, ConsoleStyle, ConsoleBackground, print_colored
from Lib.plc_log_reader import PlcMultiServerManager

# Execute
if __name__ == "__main__":
  
  print_colored(' ############################# ', color=ConsoleColor.BLUE, styles=ConsoleStyle.BOLD, background=ConsoleBackground.WHITE)
  print_colored('  PLC Log Reader Application!  ', color=ConsoleColor.BLUE, styles=ConsoleStyle.BOLD, background=ConsoleBackground.WHITE)
  print_colored(' ############################# ', color=ConsoleColor.BLUE, styles=ConsoleStyle.BOLD, background=ConsoleBackground.WHITE)
  
  
  
  servers = [
    {
      'name': 'Flapper', 'host': '172.16.0.20', 'port': 2000,
      'console_color' : ConsoleColor.BLUE,
      'show_messages' : [':CA:', ':IC:', ':RR:', ':ES:', ':VE:'],
      'replaces' : [('\r\n', ''), ('\\\\//', '\n')]
    },
    {
      'name': 'Master*', 'host': '172.16.2.20', 'port': 2000, 
      'console_color' : ConsoleColor.GREEN,
      #'show_messages' : ['position', 'p-alarms', 'release', 'p-empty', 'p-inmode','p-opmode', 'p-enable', 'p-in-en'],
      'show_messages' : ['position'],
      'and_show_messages' : ['S03I12'],
      'discard_messages' :  ['ACK'],
      'replaces' : [('\r\n', ''), ('}{', '\n')]
    }
  ]
  
  servers2 = [
    {'name': 'Flapper', 'host': '172.16.0.20', 'port': 2000,
     'console_color' : ConsoleColor.BLUE,
     'show_messages' : [':CA:', ':IC:', ':RR:', ':ES:', ':VE:']
    },

    {'name': 'Master*', 'host': '172.16.2.20', 'port': 2000, 
     'console_color' : ConsoleColor.GREEN,
     'discard_messages' : [',ACK,'],
     #'show_messages' : ['position', 'p-alarms', 'release', 'p-empty', 'p-inmode','p-opmode', 'p-enable', 'p-in-en'],
     'show_messages' : ['position'], 
     'and_show_messages' : ['S03I06'],
     'replaces' : [('\r\n', ''), ('}{', '}\r\n{')]
    }
  ]

  # Crear gestor de múltiples servidores
  manager = PlcMultiServerManager()
  
  # Añadir servidores
  for server in servers:
    manager.add_server(
      host = server["host"],
      port = server["port"],
      server_name = server["name"],
      console_color = server['console_color'],
      show_messages = server.get("show_messages"),
      and_show_messages = server.get('and_show_messages'),
      replaces = server.get("replaces"),
      discard_messages = server.get("discard_messages")
    )
  
  try:
    # Iniciar todas las conexiones
    manager.start_all()
    
    # Mantener el programa ejecutándose
    print("Press Ctrl+C to stop all connections...")
    while manager.is_any_alive():
      sleep(1)
  
  except KeyboardInterrupt:
    print("\nShutting down...")
    manager.stop_all()
    print("All connections stopped.")
  
  except Exception as e:
    print(f"Unexpected error: {e}")
    manager.stop_all()
  
  finally:
    print(f'Application closed!')
