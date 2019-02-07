from sys import argv

import busboy.recording as rec


def main() -> None:
    if len(argv) == 1:
        rec.loop()
    else:
        rec.loop(argv[1:])


if __name__ == "__main__":
    main()
