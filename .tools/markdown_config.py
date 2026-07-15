import os
import sys

config_file = sys.argv[1]

if not os.path.exists(config_file):
    raise Exception(f"Config file not found: {config_file}")

with open(config_file, encoding="utf-8") as file:

    for line in file:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        key, value = line.split("=", 1)

        with open(
            os.environ["GITHUB_ENV"],
            "a",
            encoding="utf-8"
        ) as env:

            env.write(f"{key}={value}\n")

print("Done")
