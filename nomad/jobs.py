"""This module finds all Nomad jobs not in the AWS registry and still on Docker Hub.
It finds every job that has an image that contains 'edgelab/' and does not contain
'meta.container_registry' and by running jobs.py, the results will be printed"""

import requests
from tqdm import tqdm


def fetch_jobs():
    """Get the list of Nomad jobs in all namespace"""
    with requests.get(
        "http://nomad.service.consul:4646/v1/jobs", params={"namespace": "*"}
    ) as resp:
        resp.raise_for_status()
        return resp.json()


def fetch_job(job):
    name = job["Name"]
    namespace = job["JobSummary"]["Namespace"]

    """Read the job definition"""
    with requests.get(
        f"http://nomad.service.consul:4646/v1/job/{name}",
        params={"namespace": namespace},
    ) as resp:
        resp.raise_for_status()
        return resp.json()


def check_images(job):
    """Check Docker images of this job that are not yet on AWS container registry
    and return a dict like {group_name.task_name: image_name}.
    """
    job = fetch_job(job)
    images = {}
    for group in job["TaskGroups"]:
        for task in group["Tasks"]:
            if task["Driver"] != "docker":
                continue

            image = task["Config"]["image"]
            if "edgelab/" in image and "meta.container_registry" not in image:
                images[f"{group['Name']}.{task['Name']}"] = image

    return images


def main():
    jobs = fetch_jobs()
    results = {}
    for job in tqdm(jobs):
        results[job["Name"]] = check_images(job)

    for job_name, images in results.items():
        if not images:
            continue
        print(f"Job {job_name}:")
        for job, image in images.items():
            print(f"  {job.ljust(30)}: {image}")
        print()


if __name__ == "__main__":
    main()
