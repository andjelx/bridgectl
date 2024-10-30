import re


class ValidK8sNodeOS:
    Ubuntu20_04 = "Ubuntu20.04"
    RELH_8 = "RELH-8"


class Validation:
    @staticmethod
    def is_valid_email(email):
        if not email:
            return False
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    @staticmethod
    def is_valid_ipaddress(ipaddress):
        return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ipaddress)

    @staticmethod
    def is_valid_guid(guid):
        return re.match(r"^[a-f\d]{8}(-[a-f\d]{4}){4}[a-f\d]{8}$", guid)

    @staticmethod
    def is_property_not_null(data: dict, key: str):
        val = data.get(key)
        if not val:
            raise Exception(f"property {key} is null")
        return val

    valid_docker_image_pattern = r"^[a-zA-Z0-9_.-]*$"

    @classmethod
    def is_valid_docker_image_name(cls, name):
        return re.match(cls.valid_docker_image_pattern, name)

    @classmethod
    def is_valid_host(cls, host):
        return re.match(r"^[a-zA-Z0-9.-]*$", host)
