# -*- coding:utf-8 -*-
import re
from lxml import etree

p = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def find_ip(string):
    return re.findall(p, string)


def transform(original, target, job_name):
    config = original.get_job_config(job_name)
    config = modify_config(config)
    target.create_job(job_name, config)
    print("{0} transformed".format(job_name))


def modify_config(config):
    xml = etree.fromstring(config.encode('utf-8'))

    # use lxml and write your custom changes here

    return etree.tostring(xml, encoding='unicode')
