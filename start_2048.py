import platform
import subprocess
import sys


def start_game() -> None:
    match platform.system(), platform.machine():
        case "Windows", "ARM64":
            subprocess.run([sys.executable, "control_2048.py"])
        case "Windows", "AMD64":
            from control_2048 import game2048

            game2048.play()
        case _:
            raise NotImplementedError("The platform is not supported yet!")
