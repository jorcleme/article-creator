# template_python_fastapi

## Config files that can be customized by the user

* config/ (if you need to change the kubernetes manifests)
* Jenkinsfile
* Dockerfile
* SonarQube Related files

---

1. Dockerfile:
Dockerfile must be created having the desired image and exposing the desired port, with the correct entrypoint and build step

2. Jenkinsfile:
Stages may be added/removed as per user's preference.
By default, the Dockerfile will be built and pushed. Dockerfile.test will be built for testing.

3. config/cae-np-alln-\<namespace\>-dev.yaml
    * This file is deploying all the necessary objects to Openshift/CAE, exposing the service and creating a route where the application would be live.
    * Container related fields can be edited, app names can be changed.
    * While creation of route, domain name of choice can be specified against 'host' with the associated 'path' (default: /). The target ports can be changed as per the need.

4. For Sonar related dependencies to run a sonar scan
refer to <https://confluence-eng-rtp1.cisco.com/conf/pages/viewpage.action?pageId=171475189>

---

Python, FastAPI & MongoDB External resources:

<https://fastapi.tiangolo.com/tutorial/>
<https://github.com/naikshubham/Introudction-to-MongoDB-in-Python/blob/master/README.md>
<https://github.com/mher/pymongo/blob/master/README.rst>
<https://www.mongodb.com/blog/post/getting-started-with-python-and-mongodb>

Sonar Requirements & Onboarding

<https://confluence-eng-rtp1.cisco.com/conf/pages/viewpage.action?pageId=171475189>

---

### Testcases

Create a virtual environment for testcases and install requirements 
  
``` 
python3 -m venv envname
pip install -r test_requirement.txt 
```

For running testcases
``` 
pytest
```