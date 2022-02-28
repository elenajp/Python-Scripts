import requests_mock


def test_check_images():

    job = {"Name": "fake", "JobSummary": {"Namespace": "test"}}

    with requests_mock.Mocker() as m:
        m.get("http://nomad.service.consul:4646/v1/job/fake?namespace=test", json={
            "Name": "fake",
            "TaskGroups": [
                    {
                        "Name": "g1",  # g1 = TaskGroups['Name']
                        "Tasks": [
                            {
                                "Name": "t1",
                                "Driver": "docker",
                                "Config": {
                                    "image": "edgelab/fake",
                                }
                            },

                            {
                                "Name": "t2",
                                "Driver": "exec",
                            },
                        ]
                    },

                {
                        "Name": "g2",
                        "Tasks": [
                            {
                                "Name": "t3",
                                "Driver": "docker",
                                "Config": {
                                    "image": "${meta.container_registry}/edgelab/other_group",
                                }
                            },

                            {
                                "Name": "t4",
                                "Driver": "docker",
                                "Config": {
                                    "image": "edgelab/repo:v2",
                                }
                            },
                        ]
                    },
            ]
        })

        from jobs import check_images

        assert {
            "g1.t1": "edgelab/fake",
            "g2.t4": "edgelab/repo:v2",
        } == check_images(job)
