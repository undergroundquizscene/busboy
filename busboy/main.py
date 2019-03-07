from sys import argv, warnoptions

import busboy.recording as rec


def main() -> None:
    if len(argv) == 1:
        rec.loop()
    else:
        rec.loop(argv[1:])


if __name__ == "__main__":
    if not warnoptions:
        import warnings

        warnings.simplefilter("ignore")

    main()
