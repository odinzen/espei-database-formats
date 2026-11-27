"""``espei-database-formats``: ESPEI's own command line, with the ``.dbfit`` format registered first."""
import espei_database_formats  # noqa: F401  (registers the format)


def main():
    from espei.espei_script import main as espei_main
    return espei_main()


if __name__ == "__main__":
    main()
