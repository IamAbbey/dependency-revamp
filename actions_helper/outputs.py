from dataclasses import dataclass


@dataclass
class CreateTaskDefinitionOutput:
    previous_task_definition_arn: str
    latest_task_definition_arn: str


@dataclass
class GetImageUriOutput:
    image_uri: str


@dataclass
class RunPreflightOutput:
    preflight_task_arn: str
    previous_task_definition_arn: str
    latest_task_definition_arn: str
