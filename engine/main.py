import os
import uvicorn


def main():
    host = os.environ["APP_HOST"] if "APP_HOST" in os.environ else "0.0.0.0"
    port = int(os.environ["APP_PORT"]) if "APP_PORT" in os.environ else 8080
    log = os.environ["APP_LOG"] if "APP_LOG" in os.environ else "info"

    uvicorn.run("api.api:app", host=host, port=port, log_level=log)


if __name__ == "__main__":
    main()
