import json
from typing import List

from src.models import LoggerInterface, AppSettings
from src.subprocess_util import SubProcess
from dataclasses import dataclass

@dataclass
class EcrImage:
    tags: List[str]
    imageDigest: str
    size: int

class EcrRegistryPrivate:
    def __init__(self, logger: LoggerInterface, aws_account_id, ecr_repository_name, aws_region = "us-west-2"):
        self.logger = logger
        self.aws_account_id = aws_account_id
        self.ecr_repository_name = ecr_repository_name
        self.aws_region = aws_region

    def get_registry_url(self):
        return f"{self.aws_account_id}.dkr.ecr.{self.aws_region}.amazonaws.com"

    def get_repo_url(self):
        return f"{self.get_registry_url()}/{self.ecr_repository_name}"

    def get_remote_image_url(self, image_tag_name):
        return f"{self.get_repo_url()}:{image_tag_name}"

    @staticmethod
    def get_image_url_static(logger: LoggerInterface, image_tag_name: str):
        app = AppSettings.load_static()
        reg = EcrRegistryPrivate(logger, app.ecr_private_aws_account_id, app.ecr_private_repository_name, app.aws_region)
        return reg.get_remote_image_url(image_tag_name)

    def validate_params(self, params: dict):
        for k, v in params.items():
            if not v:
                raise Exception(f"parameter '{k}' is required")
        return True

    def push_image(self, local_image_tag, docker_client, just_show_script: bool):
        local_image_tag = local_image_tag.split(":")[0] # strip off the ":latest" part
        image_push_url = self.get_remote_image_url(local_image_tag)
        cmds = [
            f'aws ecr get-login-password --region {self.aws_region} | docker login --username AWS --password-stdin {self.get_registry_url()}',
            f'docker tag {local_image_tag} {image_push_url}',
            f'docker push {image_push_url}']
        if just_show_script:
            return None, cmds
        if not docker_client.image_exists(local_image_tag):
            self.logger.warning(f"Local image {local_image_tag} not found")
            return
        if not self.validate_params({
                "aws_account_id": self.aws_account_id,
                "ecr_repository_name": self.ecr_repository_name,
                "local_image_tag": local_image_tag}):
            return
        self.logger.info("Pushing bridge image to ECR (note you must have local AWS credentials for pushing to ECR)")
        self.logger.info(f"remote_image_url: {image_push_url}")
        SubProcess(self.logger).run_cmd(cmds, name = f'push docker image', display_output= True)
        return image_push_url, None

    def pull_image(self, remote_image_tag_name: str):
        if not self.validate_params({
                "aws_account_id": self.aws_account_id,
                "ecr_repository_name": self.ecr_repository_name,
                "remote_image_tag_name": remote_image_tag_name}):
            return
        self.logger.info("Pulling bridge image from ECR")
        image_pull_url = self.get_remote_image_url(remote_image_tag_name)
        self.logger.info(f"remote_image_url: {image_pull_url}")
        cmds = [
            f'aws ecr get-login-password --region {self.aws_region} | docker login --username AWS --password-stdin {self.get_registry_url()}',
            f'docker pull {image_pull_url}']
        SubProcess(self.logger).run_cmd(cmds, name = f'pull docker image', display_output= True)
        return image_pull_url

    # def list_ecr_images(self) -> List[EcrImage]:
    #     import boto3
    #     ecr_client = boto3.client('ecr', region_name=self.aws_region)
    #     response = ecr_client.describe_images(repositoryName=self.ecr_repository_name, registryId=self.aws_account_id)
    #     img_list = []
    #     for img in response['imageDetails']:
    #         pi = EcrImage(img.get('imageTags', []), img['imageDigest'], img['imageSizeInBytes'])
    #         img_list.append(pi)
    #     return img_list

    def check_connection_to_ecr(self) -> (bool, str):
        cmd = f'aws ecr describe-repositories --repository-names {self.ecr_repository_name} --registry-id {self.aws_account_id} --region {self.aws_region}'
        stdout, stderr, return_code = SubProcess.run_cmd_light(cmd)
        return return_code == 0, stderr

    def list_images(self) -> List[EcrImage]:
        cmd = f'aws ecr describe-images --repository-name {self.ecr_repository_name} --registry-id {self.aws_account_id} --region {self.aws_region}'
        stdout, stderr, return_code = SubProcess.run_cmd_light(cmd)
        if return_code != 0:
            raise Exception(f"Error listing images: {stderr}")
        response = json.loads(stdout)
        img_list = []
        for img in response['imageDetails']:
            pi = EcrImage(img.get('imageTags',[]), img['imageDigest'], img['imageSizeInBytes'])
            img_list.append(pi)
        return img_list

    def list_ecr_repository_tags(self):
        try:
            img_list = self.list_images()
        except Exception as ex:
            self.logger.error(f"Error trying to list tags: {ex}")
            return [], str(ex)
        tags = []
        for img in img_list:
            tags.extend(img.tags)
        tags.sort(key=str.lower, reverse=True)
        return tags, None

    def get_image_detail(self, image_tag: str) -> EcrImage:
        img_list = self.list_images()
        for img in img_list:
            if image_tag in img.tags:
                return img
        return None

    def login_to_ecr(self):
        if not self.validate_params({
                "aws_account_id": self.aws_account_id,
                "aws_region": self.aws_region,
                }):
            return False
        cmds = [
            f'aws ecr get-login-password --region {self.aws_region} | docker login --username AWS --password-stdin {self.get_registry_url()}']
        SubProcess(self.logger).run_cmd(cmds, name = f'docker login', display_output= True)
        return True

