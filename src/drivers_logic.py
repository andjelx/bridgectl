# from dataclasses import dataclass
# from typing import List
# import os
#
# from src import bridge_container_builder
#
#
# @dataclass
# class DriverSetup:
#     name: str
#     type: str  # type of driver: 'jar' or 'rpm'
#     copy: str = None  # Docker copy command
#     install: str = None  # custom Docker install script
#
#
# class DriverType:
#     jar = "jar"
#     rpm = "rpm"
#
#
# class DriverLogic:  # FutureDev: finish implementing
#     def __init__(self, logger):
#         self.logger = logger
#         self.DRIVERS_PATH = bridge_container_builder.driver_files_path
#         if not os.path.exists(self.DRIVERS_PATH):  # FutureDev: create this directory at startup, for user.
#             os.makedirs(self.DRIVERS_PATH)
#
#     def discover_additional_drivers(self) -> List[DriverSetup]:
#         # STEP - load customer drivers
#         additional_drivers = os.listdir(self.DRIVERS_PATH)
#         valid_found = additional_drivers.copy()
#
#         driver_setup_list = []
#         for f in additional_drivers:
#             if f.endswith(".jar"):
#                 d = DriverSetup(f, DriverType.jar, "")
#                 driver_setup_list.append(d)
#             elif f.endswith(".rpm"):
#                 d = DriverSetup(f, DriverType.rpm, "")
#                 driver_setup_list.append(d)
#             else:
#                 valid_found.remove(f)
#                 print(f"WARNING: file {f} in {self.DRIVERS_PATH} is not a recognized driver")
#         # if not valid_found:
#         #     self.logger.info(f"No additional drivers found in {self.DRIVERS_PATH}")
#         # else:
#         #     self.logger.info(f"Additional drivers found in {self.DRIVERS_PATH}: {additional_drivers}")
#         return driver_setup_list
#
#     @staticmethod
#     def write_dockerfile_lines(drivers: List[DriverSetup]) -> List[str]:
#         lines = []
#         for driver in drivers:
#             base_name = driver.name.split('/')[-1]
#             local_folder = f"./additional_drivers/"
#             if driver.type == DriverType.jar:
#                 lines.append(f"COPY {local_folder}{base_name} /opt/tableau/tableau_driver/jdbc/")
#             elif driver.type == DriverType.rpm:
#                 lines.append(f"COPY {local_folder}{base_name} .")
#                 lines.append(f"RUN yum install -y {base_name} && rm {base_name}")
#         return lines
