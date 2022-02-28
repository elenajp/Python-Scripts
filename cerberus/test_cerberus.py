# Compute the mean duration of all requests done on Cerberus (FrontendName="cerberus" )
# if the request is a GET and status is 2xx (between 200 and 299)

import json


def main():
    with open("traefik.json", "r") as f:
        logs = json.loads(f.read())

    mean = compute_mean(logs)
    print(f"Mean of duration is: {mean:.2f}ms")


def compute_mean(traefik_logs):
    durations = 0
    counter = 0

    for log in traefik_logs["hits"]:
        log = log.get("_source")
        if log is None:
            continue

        if (
            log.get("FrontendName") == "cerberus"
            and log["RequestMethod"] == "GET"
            and 200 <= log["DownstreamStatus"] < 300
        ):
            durations += log["Duration"]
            counter += 1

    if counter == 0:
        return 0

    mean = durations / counter * 0.000001

    return mean


if __name__ == "__main__":
    main()
