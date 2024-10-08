import logging
from functools import cache
from pathlib import Path

import jinja2

JINJA_UNDEFINED_HANDLER = jinja2.make_logging_undefined(
    logger=logging.getLogger(__file__),
    base=jinja2.StrictUndefined,
)

BASE_DIR = Path(__file__).resolve().parent.parent


@cache
def _get_environment() -> jinja2.Environment:
    loader = jinja2.FileSystemLoader(BASE_DIR / "templates")
    env = jinja2.Environment(
        loader=loader,
        undefined=JINJA_UNDEFINED_HANDLER,
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=["jinja2.ext.loopcontrols"],
    )
    return env


@cache
def get_template_from_string(content: str) -> jinja2.Template:
    return jinja2.Template(content, undefined=JINJA_UNDEFINED_HANDLER)


def render_template_from_string(content: str, data: dict) -> str:
    return get_template_from_string(content).render(**data)


def render_string_from_template(
    template_name: str,
    context: dict,
) -> str:
    env = _get_environment().get_template(template_name)
    return env.render(**context)
