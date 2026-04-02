from time import sleep
import json
from lib.console_colored_text import ConsoleColor, ConsoleStyle, ConsoleBackground, print_colored
from lib.plc_log_reader import PlcMultiServerManager

# Execute
if __name__ == "__main__":
  
  # Show welcome message
  print_colored(' ############################# ', color=ConsoleColor.BLUE, styles=ConsoleStyle.BOLD, background=ConsoleBackground.WHITE)
  print_colored('  PLC Log Reader Application!  ', color=ConsoleColor.BLUE, styles=ConsoleStyle.BOLD, background=ConsoleBackground.WHITE)
  print_colored(' ############################# ', color=ConsoleColor.BLUE, styles=ConsoleStyle.BOLD, background=ConsoleBackground.WHITE)
  
  # Load configuration
  with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

  # Process server configurations
  servers = config.get('servers', [])
  for server in servers:
    if 'console_color' in server:
      server['console_color'] = ConsoleColor[server['console_color']]
  
  # Multiple server manager
  manager = PlcMultiServerManager()
  
  # Add servers to manager
  for server in servers:
    manager.add_server(
      fragmented_log = server.get('fragmented_log', False),
      host = server["host"],
      port = server["port"],
      server_name = server["name"],
      console_color = server['console_color'],
      show_messages = server.get("show_messages"),
      replaces = server.get("replaces"),
      discard_messages = server.get("discard_messages")
    )
  
  try:
    # Start all connections
    manager.start_all()
    
    # Keep the program running until interrupted
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
