import importlib.util
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import accumulate, batched, chain, count, repeat
from operator import itemgetter, lshift, or_

if platform.system() == "Windows" and platform.machine() == "AMD64":
    from recognition import screen_capture
    from recognition._image_recognition import image_recognition
    from recognition.character_recognition import text_recognition

module_name, file_path = "ailib", r"2048-ai-master\ailib.py"
spec = importlib.util.spec_from_file_location(module_name, file_path)
assert spec is not None, f"Cannot find module at {file_path}"
ailib_2048 = importlib.util.module_from_spec(spec)
os.chdir("2048-ai-master")
print("Changed directory to 2048-ai-master")
assert spec.loader is not None, f"Cannot load module {module_name}"
spec.loader.exec_module(ailib_2048)
os.chdir("..")
print("Changed directory back to the root")


class GameControl:
    execute_move = ailib_2048.ailib.execute_move
    score_toplevel_move = ailib_2048.ailib.score_toplevel_move
    executor = ThreadPoolExecutor(max_workers=4)
    move_names = ['up', 'down', 'left', 'right']

    def __init__(self, manual: bool = True) -> None:
        self.manual = manual
        self.exponents: list[list[int]] = [[0] * 4 for _ in range(4)]
        if self.manual:
            print("Enter board one row at a time, with entries separated by spaces")
            for idx, row in enumerate(self.exponents, start=1):
                # board.append([GameControl.from_pow_to_exp(int(c)) for c in input(f"Row {idx}: ").split()])
                row[:] = [*map(GameControl.from_pow_to_exp, map(int, input(f"Row {idx}: ").split()))]
        else:
            assert platform.system() == "Windows" and platform.machine() == "AMD64", "Unsupported platform"
            image, frame = screen_capture.grab(show=True)
            result = image_recognition.detect_objects(frame)
            print("Detected objects:", result)
            result = text_recognition.get_text_positions(frame)
            print("Detected text positions:", result)

    def __str__(self) -> str:
        lines = (" ".join(f"{cell:^5d}" for cell in map(GameControl.from_exp_to_pow, row)) for row in self.exponents)
        return "\n".join(lines)

    def get_board(self) -> None:
        if self.manual:
            updates = input("Enter update in the form r,c,n (1-indexed row/column): ")
            for item in updates.split():
                row, col, num = map(int, item.split(","))
                self.exponents[row - 1][col - 1] = GameControl.from_pow_to_exp(num)
        else:
            assert platform.system() == "Windows" and platform.machine() == "AMD64", "Unsupported platform"

    def play(self) -> None:
        start = time.time()
        for moveno in count(1):
            print("Current board:", self, sep="\n")
            self.get_board()
            if (move := self.find_best_move()) == -1:
                break
            print(f"Move {moveno}:", self.move_names[move], f"({time.time() - start:010.6f} s)")
            print("EXECUTE MOVE:", self.move_names[move])
            curr_mask = self.convert_board_to_mask()
            next_mask = GameControl.execute_move(move, curr_mask)
            self.convert_mask_to_board(next_mask)
        print("Game over.")

    def find_best_move(self) -> int:
        print(self)
        mask = self.convert_board_to_mask()
        scores = GameControl.executor.map(GameControl.score_toplevel_move, repeat(mask), range(4))
        best_move, best_score = max(enumerate(scores), key=itemgetter(1))
        return -1 if best_score == 0 else best_move

    def convert_board_to_mask(self) -> int:
        print(self.exponents)
        *_, mask = accumulate(map(lshift, chain.from_iterable(self.exponents), range(0, 64, 4)), or_)
        return mask

    def convert_mask_to_board(self, mask: int) -> None:
        cells = ((mask >> i) & 0xF for i in range(0, 64, 4))
        self.exponents = [*map(list, batched(cells, 4))]

    from_pow_to_exp = [0, *map(lshift, repeat(1), range(1, 16))].index

    @staticmethod
    def from_exp_to_pow(idx: int) -> int:
        return 0 if idx == 0 else 1 << idx


match platform.system(), platform.machine():
    case "Windows", "ARM64":
        manual = True
    case "Windows", "AMD64":
        manual = False
    case _:
        raise NotImplementedError("The platform is not supported yet!")
game2048 = GameControl(manual=manual)
if __name__ == '__main__':
    game2048.play()
