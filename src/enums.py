from pathlib import Path


class ImageRegistryType:
    local_docker = "Local Docker"
    aws_ecr = "AWS ECR"

BRIDGE_CONTAINER_PREFIX = 'bridge_'

DEFAULT_BASE_IMAGE = "registry.access.redhat.com/ubi9/ubi:latest" #futuredev: move to ContainerRepoURIs

class ContainerRepoURI:
    # amazonlinux2023 = "public.ecr.aws/amazonlinux/amazonlinux:2023"
    redhat_ubi8_DEFAULT = "registry.access.redhat.com/ubi9/ubi:latest"
    #ubuntu22 = "docker.io/library/ubuntu:22.04"

DEFAULT_LINUX_DISTRO = "rhel9"

LINUX_DISTROS = ["rhel9"] #"rhel8" , "ubuntu22", "amazonlinux2023"

ADMIN_PAT_PREFIX = "admin-pat"

DEFAULT_BRIDGE_LOGS_PATH = "~/Documents/My Tableau Bridge Repository/Logs"

AMD64_PLATFORM = 'linux/amd64'

VALID_DOCKER_NETWORK_MODES = ["bridge", "host"]
DEFAULT_DOCKER_NETWORK_MODE = "bridge"
DEFAULT_POOL = "(default pool)"

SCRATCH_DIR =  Path(__file__).parent.parent / 'scratch'

class PropNames:
    host_mount_path = "host_mount_path"
    container_mount_path = "container_mount_path"

class RunContainerAsUser:
    root = "root"
    tableau = "tableau"