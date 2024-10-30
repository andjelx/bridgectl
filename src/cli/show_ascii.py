from prompt_toolkit.styles import Style

custom_style = Style([
    ("qmark", "fg:#02abab bold"),
    ("question", "bold"),
    ("answer", "fg:#02abab bold"),
    ("pointer", "fg:#02abab bold"),
    ("highlighted", "fg:#02abab bold"),
    ("selected", "fg:#02abab"),
    ("separator", "fg:#02abab"),
    ("instruction", ""),
    ("text", ""),
])

LOGOS = [
r"""
___________     ___.   .__                                
\__    ___/____ \_ |__ |  |   ____ _____   __ __ 
  |    |  \__  \ | __ \|  | _/ __ \\__  \ |  |  \ 
  |    |   / __ \| \_\ \  |_\  ___/ / __ \|  |  /
  |____|  (____  /___  /____/\___  >____  /____/ 
               \/    \/          \/     \/ 
"""
]
