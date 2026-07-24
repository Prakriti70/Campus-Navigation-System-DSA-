#!/usr/bin/env python3
"""
main.py
-------
Entry point for the Pulchowk Smart Campus Navigation System.

Usage:
    python main.py
"""

import tkinter as tk
from gui import App


def _show_splash(root: tk.Tk) -> tk.Toplevel:
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    width, height = 480, 260
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    splash.configure(bg="#1F1E1C")

    tk.Label(
        splash, text="Pulchowk Smart\nCampus Navigation System",
        bg="#1F1E1C", fg="white", font=("Segoe UI", 18, "bold"), justify="center",
    ).pack(expand=True)
    tk.Label(
        splash, text="Graphs  •  Linked Lists  •  Queues  •  Stacks  •  Min-Heaps  •  BFS  •  DFS  •  Dijkstra",
        bg="#1F1E1C", fg="#A8A7A3", font=("Segoe UI", 9), justify="center",
    ).pack(pady=(0, 20))

    return splash


def main() -> None:
    root = tk.Tk()
    root.withdraw()  # hide main window until splash finishes

    splash = _show_splash(root)

    def launch():
        splash.destroy()
        root.deiconify()
        root.title("Pulchowk Smart Campus Navigation System")
        root.geometry("1300x750")
        App(root)

    root.after(1400, launch)
    root.mainloop()


if __name__ == "__main__":
    main()
