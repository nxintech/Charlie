# -*- coding:utf-8 -*-
import os
import ConfigParser


config = ConfigParser.ConfigParser()
config.read(os.path.join("".join(__file__.split('/')[:-1]), "jenkins.conf"))


def parse_section(section):
    url = config.get(section, "url")
    user = config.get(section, "user")
    password = config.get(section, "password")
    return url, user, password
