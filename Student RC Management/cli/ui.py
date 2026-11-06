"""
Terminal UI Styling & User Interaction Utilities.
Provides formatted banners, styled messages, safe inputs, and menu navigation helpers.
"""

import os
import sys
from typing import List, Optional, Any

# Optional colorama integration with graceful fallback
try:
    import colorama
    colorama.init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

# ANSI Color Codes
CYAN = "\033[96m" if HAS_COLOR or os.name != "nt" else ""
GREEN = "\033[92m" if HAS_COLOR or os.name != "nt" else ""
YELLOW = "\033[93m" if HAS_COLOR or os.name != "nt" else ""
RED = "\033[91m" if HAS_COLOR or os.name != "nt" else ""
BLUE = "\033[94m" if HAS_COLOR or os.name != "nt" else ""
MAGENTA = "\033[95m" if HAS_COLOR or os.name != "nt" else ""
BOLD = "\033[1m" if HAS_COLOR or os.name != "nt" else ""
RESET = "\033[0m" if HAS_COLOR or os.name != "nt" else ""


def clear_screen() -> None:
    """Clears terminal console window."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Displays the system title and header art."""
    banner = f"""{CYAN}{BOLD}
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            🎓  STUDENT RECORDS MANAGEMENT SYSTEM (SRMS)  🎓               ║
║                                                                           ║
║            Enterprise Edition • Python • SQL • SQLite • MySQL             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


def print_header(title: str) -> None:
    """Renders a styled section header."""
    print(f"\n{BLUE}{BOLD}=== {title.upper()} ==={RESET}\n")


def print_success(message: str) -> None:
    """Displays success notice."""
    print(f"{GREEN}✔ [SUCCESS] {message}{RESET}")


def print_error(message: str) -> None:
    """Displays error notice."""
    print(f"{RED}✖ [ERROR] {message}{RESET}")


def print_warning(message: str) -> None:
    """Displays warning notice."""
    print(f"{YELLOW}▲ [WARNING] {message}{RESET}")


def print_info(message: str) -> None:
    """Displays information notice."""
    print(f"{CYAN}ℹ [INFO] {message}{RESET}")


def prompt_string(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
    """Prompts user for non-empty text input with default fallback."""
    while True:
        default_hint = f" [{default}]" if default is not None else ""
        raw = input(f"{BOLD}{prompt}{default_hint}: {RESET}").strip()
        if not raw and default is not None:
            return default
        if not raw and required:
            print_error("Input cannot be empty. Please enter a value.")
            continue
        return raw


def prompt_int(prompt: str, min_val: Optional[int] = None, max_val: Optional[int] = None, default: Optional[int] = None) -> Optional[int]:
    """Prompts for an integer within an optional range."""
    while True:
        default_hint = f" [{default}]" if default is not None else ""
        raw = input(f"{BOLD}{prompt}{default_hint}: {RESET}").strip()
        if not raw and default is not None:
            return default
        if not raw:
            return None
        try:
            val = int(raw)
            if min_val is not None and val < min_val:
                print_error(f"Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value cannot exceed {max_val}.")
                continue
            return val
        except ValueError:
            print_error("Invalid number. Please enter a valid integer.")


def prompt_float(prompt: str, min_val: Optional[float] = None, max_val: Optional[float] = None, default: Optional[float] = None) -> Optional[float]:
    """Prompts for a floating-point number within an optional range."""
    while True:
        default_hint = f" [{default}]" if default is not None else ""
        raw = input(f"{BOLD}{prompt}{default_hint}: {RESET}").strip()
        if not raw and default is not None:
            return default
        if not raw:
            return None
        try:
            val = float(raw)
            if min_val is not None and val < min_val:
                print_error(f"Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value cannot exceed {max_val}.")
                continue
            return val
        except ValueError:
            print_error("Invalid number. Please enter a numeric value.")


def prompt_choice(prompt: str, choices: List[str], default: Optional[str] = None) -> str:
    """Prompts user to select from a strict set of choices."""
    choice_map = {str(i + 1): c for i, c in enumerate(choices)}
    print(f"{prompt}")
    for idx, choice in enumerate(choices, 1):
        def_tag = " (default)" if choice == default else ""
        print(f"  [{idx}] {choice}{def_tag}")

    while True:
        raw = input(f"{BOLD}Select an option [1-{len(choices)}]: {RESET}").strip()
        if not raw and default:
            return default
        if raw in choice_map:
            return choice_map[raw]
        # Check direct string match
        for c in choices:
            if raw.lower() == c.lower():
                return c
        print_error(f"Invalid selection. Please choose a number between 1 and {len(choices)}.")


def pause(message: str = "Press [Enter] to continue...") -> None:
    """Pauses terminal output for user confirmation."""
    input(f"\n{YELLOW}{message}{RESET}")
