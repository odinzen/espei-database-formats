"""``espei-dat``: ESPEI's own command line, with the ``.datfit`` format registered first."""
import espei_dat  # noqa: F401  (registers the format)


def main():
    from espei.espei_script import main as espei_main
    return espei_main()


if __name__ == "__main__":
    main()
