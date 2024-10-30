import requests

from src.models import LoggerInterface
from src.subprocess_util import SubProcess

class EcrRegistryPublic:
    def __init__(self, logger: LoggerInterface, public_ecr_uri_alias, ecr_repository_name):
        self.logger = logger
        self.ecr_public_alias = public_ecr_uri_alias
        self.ecr_repository_name = ecr_repository_name

    def get_aws_alias_uri(self):
        return f"public.ecr.aws/{self.ecr_public_alias}"

    def get_repo_url(self):
        image_url = f"{self.get_aws_alias_uri()}/{self.ecr_repository_name}"
        return image_url

    def get_full_push_url(self, image_tag_name):
        image_url = f"public.ecr.aws/{self.ecr_public_alias}/{self.ecr_repository_name}:{image_tag_name}"
        return image_url

    def validate_params(self, params: dict):
        for k, v in params.items():
            if not v:
                self.logger.warning(f"parameter '{k}' is required")
                return False
        return True

    def push_image(self, local_image_tag, remote_image_tag_name: str, docker_client):
        if not docker_client.image_exists(local_image_tag):
            self.logger.info("Bridge image is missing. Please build first ...")
            return
        if not self.validate_params({
                "ecr_public_alias": self.ecr_public_alias,
                "ecr_repository_name": self.ecr_repository_name,
                "local_image_tag": local_image_tag,
                "remote_image_tag_name": remote_image_tag_name}):
            return

        self.logger.info("Pushing bridge image to ECR (note you must have local AWS credentials for pushing to ECR)")
        full_remote_image_url = self.get_full_push_url(remote_image_tag_name) # f'{self.public_ecr_uri_alias}/{self.ecr_tableau_bridge_repo}:{image_tag_name}'
        self.logger.info(f"remote_image_url: {full_remote_image_url}")
        cmds = [
            f'aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin {self.get_aws_alias_uri()}',
            f'docker tag {local_image_tag} {full_remote_image_url}',
            f'docker push {full_remote_image_url}']
        SubProcess(self.logger).run_cmd(cmds, name = f'push docker image', display_output= True)
        return full_remote_image_url

    def get_ecr_auth_token(self):
        """
        Get an authorization token for public ECR access.
        """
        response = requests.get('https://public.ecr.aws/token?service=ecr-public&scope=repository:*:*:pull')
        response.raise_for_status()
        return response.json()['token']

    def list_ecr_repository_tags(self):
        """
        List tags for a given repository in the public ECR using the provided auth token.
        """
        auth_token = self.get_ecr_auth_token()

        base_url = "https://public.ecr.aws/v2"
        tags_list_url = f"{base_url}/{self.ecr_public_alias}/{self.ecr_repository_name}/tags/list"
        headers = {'Authorization': f'Bearer {auth_token}'}

        try:
            response = requests.get(tags_list_url, headers=headers)
            response.raise_for_status()
        except Exception as ex:
            self.logger.error(f"Error trying to list tags: {ex}")
            return [], str(ex)
        tags = response.json().get('tags', [])
        tags.sort(reverse=True)
        return tags, None

    # def pull_bridge_image_from_ecr(self):
    #     self.logger.info(f"pull bridge image version {self.bridge_rpm_version} from ECR")
    #     url = f"{self.webapp_url}/api/registry/build/{self.bridge_rpm_version}"
    #     response = requests.get(url)
    #     if response.status_code != 200:
    #         self.logger.error(f"Error trying to check for rpm: {response.reason}")
    #         return
    #
    #     data = response.json()
    #     img_url = data.get('img_url')
    #     self.logger.info(f"resolved image url: {img_url}, pulling ...")
    #     cmds = [
    #         f'docker pull {img_url}',
    #         f'docker tag {img_url} {self.bridge_rpm_version}:{self.bridge_image_name}',
    #         ]
    #     SubProcess(self.logger).run_cmd(cmds, display_output= True)

