#!/usr/bin/python2

DOCUMENTATION = '''
---
module: cm_config
short_description: Config Cloudera services and roles via Cloudera Manager Api
'''

EXAMPLES = '''
- name: Enable autorestart for all roles
  cm_config:
    cm_host: "10.0.0.1"
    cm_pass: "mydummypassword"
    service_type: "*"
    role_type: "*"
    parameter: "process_auto_restart"
    value: "true"
  register: result
'''

import logging
from cm_api.api_client import ApiResource
from ansible.module_utils.basic import *


def xstr(s):
    if s is None:
        return ''
    return str(s)


def get_config_fixed(resource):
    # horrible fix, however there seems to be some inconsistency with the object produced by Cloudera API
    config = resource.get_config(view='full')
    if isinstance(config, tuple):
        config = config[0]
    return config


def get_parameter_value(config, parameter):
    if parameter not in config.keys():
        return None
    if config[parameter].value is not None:
        return config[parameter].value
    elif config[parameter].default is not None:
        return config[parameter].default
    logging.warning("Parameter {0} found but no current value or default value found!".format(
        parameter))
    return None


def change_parameter_value(cluster, service, role, config, parameter, value):
    if parameter not in config.keys():
        return
    cur_value = get_parameter_value(config, parameter)
    # cloudera json is somewhat inconsistent for default value, i.e. default values are written as strings, so we cast to string and compare in lowercase
    if str(cur_value).lower() != str(value).lower():
        update = {parameter: value}
        if role:
            # update the current configuration group, not the single role configuration
            config_name = role.roleConfigGroupRef.roleConfigGroupName
            config = service.get_role_config_group(config_name)
            resp = config.update_config(update)
        elif service:
            resp = service.update_config(update)
        else:
            resp = cluster.update_config(update)
        if isinstance(resp, tuple):
            resp = resp[0]
        if str(resp[parameter]).lower() == str(value).lower():
            logging.info("Value of parameter {0} changed to {1}".format(
                parameter, value))
        else:
            logging.error("Unable to change value for parameter {0} to {1}!".format(
                parameter, value))
            logging.error(resp)
            raise Exception("Unable to change value for parameter {0} to {1}!".format(
                parameter, value))
        return (xstr(cluster), xstr(service), xstr(role), update)


def check_cloudera_settings(api, cloudera_settings):
    updates = []
    for cluster in api.get_all_clusters():
        for service in cluster.get_all_services():
            for role in service.get_all_roles():
                # Specific role configuration for CDH service
                config = get_config_fixed(role)
                for setting in cloudera_settings:
                    if (setting.get("service_type", None) == service.type or setting.get("service_type", None) == "*") and (setting.get("role_type", None) == role.type or setting.get("role_type", None) == "*"):
                        update = change_parameter_value(
                            cluster, service, role, config, setting.get("parameter", None), setting.get("value", None))
                        if update:
                            updates.append(update)
            # Service-wide configuration for CDH service
            config = get_config_fixed(service)
            for setting in cloudera_settings:
                if (setting.get("service_type", None) == service.type or setting.get("service_type", None) == "*") and setting.get("role_type", None) is None:
                    update = change_parameter_value(
                        cluster, service, None, config, setting.get("parameter", None), setting.get("value", None))
                    if update:
                        updates.append(update)
    cm = api.get_cloudera_manager()
    service = cm.get_service()
    mgmt_roles = service.get_all_roles()
    for role in mgmt_roles:
        # Specific role configuration for Cloudera Management Services
        config = get_config_fixed(role)
        for setting in cloudera_settings:
            if (setting.get("service_type", None) == "MGMT" or setting.get("service_type", None) == "*") and (setting.get("role_type", None) == role.type or setting.get("role_type", None) == "*"):
                update = change_parameter_value(
                    None, service, role, config, setting.get("parameter", None), setting.get("value", None))
                if update:
                    updates.append(update)
    # Service-wide configuration for Cloudera Management Services
    for setting in cloudera_settings:
        if (setting.get("service_type", None) == "MGMT" or setting.get("service_type", None) == "*") and setting.get("role_type", None) is None:
            update = change_parameter_value(
                None, service, None, config, setting.get("parameter", None), setting.get("value", None))
            if update:
                updates.append(update)
        elif setting.get("service_type", None) is None and setting.get("role_type", None) is None:
            update = change_parameter_value(
                None, None, None, config, setting.get("parameter", None), setting.get("value", None))
            if update:
                updates.append(update)
    return updates


def github_repo_absent(data=None):
    has_changed = False
    meta = {"absent": "not yet implemented"}


def main():

    fields = {
        "cm_host": {"required": True, "type": "str"},
        "cm_port": {"default": 7180, "type": "int"},
        "cm_user": {"default": "admin", "type": "str"},
        "cm_pass": {"required": True, "type": "str", "no_log": True},
        "cm_api_version": {"default": 13, "type": "int"},
        "service_type": {"required": True, "type": "str"},
        "role_type": {"type": "str"},
        "parameter": {"required": True, "type": "str"},
        "value": {"required": False}
    }

    global module
    module = AnsibleModule(argument_spec=fields)

    api = ApiResource(module.params["cm_host"], module.params["cm_port"], module.params["cm_user"],
                      module.params["cm_pass"], version=module.params["cm_api_version"])
    settings = []
    settings.append(module.params)
    updates = check_cloudera_settings(api, settings)
    changed = False
    if updates:
        changed = True
    module.exit_json(changed=changed, meta=updates)


if __name__ == '__main__':
    main()
