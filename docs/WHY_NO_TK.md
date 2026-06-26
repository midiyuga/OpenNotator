# Why this build avoids Tk

Some macOS Python installations print:

`DEPRECATION WARNING: The system version of Tk is deprecated...`

and then fail to show a window. This build avoids Tkinter and opens an HTML report in Safari/your default browser instead.
