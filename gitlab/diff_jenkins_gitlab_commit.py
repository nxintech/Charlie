import gitlab
from urllib.parse import urlparse
from nx_project.client import Proj
from jenkinsapi.jenkins import Jenkins

proj = Proj(username='admin', password='')
git = gitlab.Gitlab('https://gitlab.nxin.com', private_token='')
jen = Jenkins('http://jenkins.p.nxin.com', username='nx_admin', password='')


def get_gitlab_project(name):
    project = proj.get_project(name)
    repo = project['buildInfo']['repo']
    if not repo:
        raise ValueError('project [{}] not config repo on proj.'.format(name))

    # repo 'https://gitlab.nxin.com/yiyoutao/passport.git'
    parsed = urlparse(repo)
    if not parsed.netloc.startswith('gitlab.nxin.com'):
        raise ValueError('project [{}] repo is not a gitlab repo.'.format(name))
    # remove '/' and '.git'  yiyoutao/passport
    project_space_and_name = parsed.path[1:-4]
    git_project = git.projects.get(project_space_and_name)
    return git_project


def get_git_project_master_head_commit(name):
    project = get_gitlab_project(name)
    # latest commit on master
    commit = project.commits.get('master')
    return commit.id


def get_jenkins_project_build_commit(name):
    job = jen.get_job(name)
    build = job.get_last_good_build()
    return build.get_revision()


def diff_project_jenkins_gitlab_commit(name):
    j = get_jenkins_project_build_commit('passport-account')
    g = get_git_project_master_head_commit('passport-account')
    print('jenkins job revision: {}'.format(j))
    print('gitlab master commit: {}'.format(g))


# diff_project_jenkins_gitlab_commit('passport-account')

if __name__ == '__main__':
    import sys
    diff_project_jenkins_gitlab_commit(sys.argv[1])
