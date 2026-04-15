import sys
import time

loading_chars = list("▖▘▝▗")


def main_loop() -> None:
    sys.stdout.flush()
    while True:
        for char in loading_chars:
            print(f"\r\b{char}", end="")
            sys.stdout.flush()
            time.sleep(0.1)
if __name__ == "__main__":
    main_loop()
