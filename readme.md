

`[show|discard]_messages : [[a OR b OR c] AND [d] AND [e OR f OR ... OR n]]`
`[show|discard]_messages : [[a, b, c], [d], [e, f, ..., n]]`

```python

plc_log_servers = 
[
  {
    'name': 'Flapper', 'host': '172.16.0.20', 'port': 2000,
    'console_color' : ConsoleColor.BLUE,
    'show_messages' : [':CA:', ':IC:', ':RR:', ':ES:', ':VE:']
    'replaces' : [('\r\n', ''), ('//\\', '\n')]
  },
     
  {
    'name': 'Master*', 'host': '172.16.2.20', 'port': 2000, 
    'console_color' : ConsoleColor.GREEN,
    #'show_messages' : ['position', 'p-alarms', 'release', 'p-empty', 'p-inmode','p-opmode', 'p-enable', 'p-in-en'],
    'show_messages' : ['position'],
    'and_show_messages' : ['S03I14'],
    'discard_messages' :  ['ACK'],
    'replaces' : [('\r\n', ''), ('}{', '\n')]
  }
]

```