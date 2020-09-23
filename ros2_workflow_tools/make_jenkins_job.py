import argparse
import jenkins
import logging
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def is_response_yes(text) -> bool:
    while True:
        answer = input(text + "\n >>> ").strip().lower()
        if answer in ['yes', 'y', 'yup', 'yeah']:
            return True
        elif answer in ['no', 'n', 'nope']:
            return False


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=str, help='The package name')
    parser.add_argument('branch', type=str, help='The branch name')
    parser.add_argument('--is-test-above',
                        default=False, action='store_true',
                        help='Should packages above the current package be tested?')
    parser.add_argument('--is-skip-confirm',
                        default=False, action='store_true',
                        help='Should the request be confirmed before it is sent?')
    parser.add_argument('--dry-run', '-d',
                        default=False, action='store_true',
                        help="Output what would be used in building a job")
    parser.add_argument('--jenkins-url', default='https://ci.ros2.org/', type=str,
                        help="The link to the Jenkin's CI")
    parser.add_argument('--jenkins-job-name', default='ci_launcher', type=str,
                        help="The name of the job to run")

    args = parser.parse_args()

    package = args.package
    branch = args.branch
    is_test_above = args.is_test_above
    is_skip_confirm = args.is_skip_confirm
    is_dry_run = args.dry_run
    jenkins_url = args.jenkins_url
    job_name = args.jenkins_job_name

    username = os.environ.get('JENKINS_USERNAME')
    if not username:
        raise EnvironmentError("Environment must have JENKINS_USERNAME variable")
    login_token = os.environ.get('JENKINS_TOKEN')
    if not login_token:
        raise EnvironmentError("Environment must have JENKINS_TOKEN variable")

    if is_test_above:
        build_args = f'--packages-above-and-dependencies {package}'
        test_args = f'--packages-above {package}'
    else:
        build_args = f'--packages-up-to {package}'
        test_args = f'--packages-select {package}'

    parameters = {
        'CI_BRANCH_TO_TEST': branch,
        'CI_SCRIPTS_BRANCH': 'master',
        'CI_UBUNTU_DISTRO': 'focal',
        'CI_ROS_DISTRO': 'rolling',
        'CI_COLCON_MIXIN_URL': 'https://raw.githubusercontent.com/colcon/'
                               'colcon-mixin-repository/master/index.yaml',
        'CI_BUILD_ARGS': f'--event-handlers console_cohesion+ '
                         f'console_package_list+ --cmake-args '
                         f'-DINSTALL_EXAMPLES=OFF -DSECURITY=ON {build_args}',
        'CI_ISOLATED': True,
        'CI_USE_WHITESPACE_IN_PATHS': False,
        'CI_USE_CONNEXT_STATIC': True,
        'CI_USE_CONNEXT_DEBS': False,
        'CI_USE_CYCLONEDDS': True,
        'CI_USE_FASTRTPS_STATIC': True,
        'CI_USE_FASTRTPS_DYNAMIC': False,
        'CI_USE_OPENSPLICE': False,
        'CI_COMPILE_WITH_CLANG': False,
        'CI_ENABLE_COVERAGE': False,
        'CI_TEST_ARGS': f'--event-handlers console_direct+ --executor '
                        f'sequential --retest-until-pass 2 --ctest-args '
                        f'-LE xfail --pytest-args -m "not xfail" {test_args}',
    }

    if not is_skip_confirm or is_dry_run:
        for key, value in parameters.items():
            print(f"{key + ': ':<15}{value}")
        if is_dry_run or not is_response_yes('Proceed to sending? Y/n'):
            logger.info('Exiting without creating job')
            return

    server = jenkins.Jenkins(jenkins_url, username, login_token)
    server.build_job(job_name, parameters)
    logging.info('created a job')


if __name__ == '__main__':
    main()
