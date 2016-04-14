# -*- coding:utf-8 -*-

"""
add/update a jenkins job through jenkins job builder
"""
import sys
import logging
from six.moves import configparser
from jenkins_jobs.builder import Builder


logger = logging.getLogger("jenkins_jobs.builder")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

jenkins_url = "http://jenkins:8080"
jenkins_user = "jenkins"
jenkins_password = "jenkins"

# create a ConfigParser object by hand
config = configparser.ConfigParser()
config.add_section("job_builder")
config.set("job_builder", "keep_descriptions", "False")
config.set("job_builder", "ignore_cache", "False")
config.set("job_builder", "recursive", "False")
config.set("job_builder", "exclude", ".*")
config.set("job_builder", "allow_duplicates", "False")
config.set("job_builder", "allow_empty_variables", "False")
config.add_section("jenkins")
config.set("jenkins", "url", jenkins_url)
config.set("jenkins", "user", jenkins_user)
config.set("jenkins", "password", jenkins_password)
config.set("jenkins", "query_plugins_info", "False")

user = config.get('jenkins', 'user')
password = config.get('jenkins', 'password')

builder = Builder(jenkins_url, user, password, config,
                  jenkins_timeout=10,
                  ignore_cache=True,
                  flush_cache=True,
                  plugins_list={})

jobs, num_updated_jobs = builder.update_jobs(
    ["test.yml"], [], n_workers=2)
