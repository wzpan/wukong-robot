# -*- coding: utf-8-*-
import pkgutil
from . import constants
from . import config
from robot import logging

_logger = logging.getLogger(__name__)
_has_init = False

# plugins run at query
_plugins_query = []

def init_plugins():
    """
    Dynamically loads all the plugins in the plugins folder and sorts
    them by the PRIORITY key. If no PRIORITY is defined for a given
    plugin, a priority of 0 is assumed.
    """

    global _has_init
    locations = [
        constants.PLUGIN_PATH,
        constants.CONTRIB_PATH,
        constants.CUSTOM_PATH
    ]
    _logger.debug("Looking for plugins in: %s",
                  ', '.join(["'%s'" % location for location in locations]))

    global _plugins_query
    nameSet = set()

    # plugins that are not allow to be call via Wechat or Email
    for finder, name, ispkg in pkgutil.walk_packages(locations):
        try:
            loader = finder.find_module(name)
            mod = loader.load_module(name)
        except Exception:
            _logger.warning("Skipped plugin '%s' due to an error.", name,
                            exc_info=True)
            continue

        # check slug
        if not hasattr(mod, 'SLUG'):
            mod.SLUG = name

        # check conflict
        if mod.SLUG in nameSet:
            _logger.warning("plugin '%s' SLUG(%s) has repetition", name,
                            mod.SLUG)
            continue
        nameSet.add(mod.SLUG)

        # whether a plugin is enabled
        if config.has(mod.SLUG) and 'enable' in config.get(mod.SLUG):
            if not config.get(mod.SLUG)['enable']:
                _logger.info("plugin '%s' is disabled", name)
                continue

        # plugins run at query
        if hasattr(mod, 'SLUG'):
            if not hasattr(mod, 'handle') or not hasattr(mod, 'isValid'):
                _logger.debug("Query plugin '%s' missing handle or isValid",
                              name)
            else:
                _logger.debug("Found query plugin '%s' with SLUG: %r",
                              name, mod.SLUG)
                _plugins_query.append(mod)

    def sort_priority(m):
        if hasattr(m, 'PRIORITY'):
            return m.PRIORITY
        return 0

    _plugins_query.sort(key=sort_priority, reverse=True)
    _has_init = True


def get_plugins():
    if not _has_init:
        init_plugins()
    return _plugins_query

