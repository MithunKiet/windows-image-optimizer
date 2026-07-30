"""Entry point for the CImageOptimizer desktop application.

Kept as a standalone root-level script (rather than moved into the
`cimageoptimizer` package) so that both `python main.py` and
`pyinstaller --noconsole --onefile main.py` keep working unchanged.
"""

import tkinter as tk

from cimageoptimizer.infrastructure.logging_config import configure_logging
from cimageoptimizer.presentation.gui.app import App


def main() -> None:
    configure_logging()
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
