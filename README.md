Role Name
=========
 
WORK IN PROGRESS - EXPERIMENTAL

Ansible role to change Cloudera CDH via CM api

Requirements
------------

cm-api (https://pypi.org/project/cm-api/)

Role Variables
--------------

- cm_host - address of the Cloudera Manager server, e.g. "10.0.0.1"
- cm_port - port that the Cloudera Manager server uses, default 7180
- cm_user - username of the user that authenticates with the CM API, default "admin"
- cm_pass - password of the above user
- cm_api_version - which API version should be used, default 13
- service_type - which service type should be configured, e.g. "HDFS" or "HIVE" or "MGMT" or "*" to impact all. *MGMT* indicates the Cloudera Management Services (Report Monitor, Service Monitor and so on). _Please note that the configuration change will affect all services of that type_.
- role_type - which role type should be configred. Do not specify this if you want to change a Service-wide configuration. Possible values are NAMENODE, HIVE_METASTORE and so on.
- parameter - parameter to be changed
- value - actual new value for the parameter

Dependencies
------------

-

Example Playbook
----------------

- name: Enable autorestart for all roles
  cm_config:
    cm_host: "10.0.0.1"
    cm_pass: "mydummypassword"
    service_type: "*"
    role_type: "*"
    parameter: "process_auto_restart"
    value: "true"
  register: result

License
-------

Apache 2.0

Author Information
------------------

-
