## @file __main__.py
## @brief Entry point: python -m sanslsp

from .server import create_server


def main():
    server = create_server()
    server.start_io()


if __name__ == "__main__":
    main()
