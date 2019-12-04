############################################
# ________      ________    ________       #
# |\   __  \    |\   __  \  |\   __  \     #
# \ \  \|\  \   \ \  \|\  \ \ \  \|\  \    #
#  \ \  \\\  \   \ \   ____\ \ \   __  \   #
#   \ \  \\\  \   \ \  \___|  \ \  \ \  \  #
#    \ \_______\   \ \__\      \ \__\ \__\ #
#     \|_______|    \|__|       \|__|\|__| #
############################################

import requests
import urllib3
import codecs
import json
from user_agent import generate_user_agent
from OpaExceptions.OpaExceptions import (
    CheckPermissionError,
    ConnectionsError,
    DeleteDataError,
    DeletePolicyError,
    PathNotFoundError,
    PolicyNotFoundError,
    RegoParseError,
    SSLError,
)

json_reader = codecs.getreader("utf-8")


__version__ = "1.0.5"


class OpaClient:

    """ OpaClient client object to connect and manipulate OPA service.
        
        The class object holds session information necesseary to connect OPA service.
        param :: host : to connect OPA service ,defaults to localhost
        type  :: host: str
        param :: port : to connect OPA service ,defaults to 8181
        type  :: port : str or int
        param :: version : provided REST API version by OPA,defaults to v1
        type  :: version : str
        param :: ssl : verify ssl certificates for https requests,defaults to False
        type  :: ssl : bool
        param :: cert : path to client certificate information to use for mutual TLS authentification
        type  :: cert : str
        param :: headers :  dictionary of headers to send, defaults to None

    """

    def __init__(
        self,
        host="localhost",
        port=8181,
        version="v1",
        ssl=False,
        cert=None,
        headers=None,
        **kwargs,
    ):
        host = host.lstrip()
        self.__port = port
        self.__version = version
        self.__policy_root = "{}/policies/{}"
        self.__data_root = "{}/data/{}"
        self.__secure = False
        self.__schema = "http://"

        if ssl:
            self.__ssl = ssl
            self.__cert = cert
            self.__secure = True
            self.__schema = "https://"

        if not cert:
            if ssl:
                raise SSLError("ssl=True", "Make sure you  provide cert file")

        if host.startswith("https://"):
            self.__host = host
            self.__root_url = "{}:{}/{}".format(
                self.__host, self.__port, self.__version
            )

        elif host.startswith("http://"):
            self.__host = host
            if self.__secure:
                raise SSLError(
                    "ssl=True",
                    "With ssl enabled not possible to have connection with http",
                )

            self.__root_url = "{}:{}/{}".format(
                self.__host, self.__port, self.__version
            )

        else:
            self.__host = host

            self.__root_url = "{}{}:{}/{}".format(
                self.__schema, self.__host, self.__port, self.__version
            )

        if headers:
            self.__headers = requests.utils.default_headers()
            self.__headers.update({**headers})
        else:
            self.__headers = requests.utils.default_headers()

            self.__headers.update({"User-Agent": generate_user_agent()})
        if self.__secure:
            https = urllib3.PoolManager(
                cert_reqs="CERT_REQUIRED",
                assert_hostname=False,
                ca_certs=self.__cert,
                headers=self.__headers,
            )
            self.__session = https.request
        else:
            self.__session = requests.Session()

    def check_connection(self):
        """ Checks whether established connection config True or not.   
            if not properly configured will raise an ConnectionError.
        """

        url = self.__policy_root.format(self.__root_url, "")
        try:
            if not self.__secure:
                response = self.__session.get(url, timeout=(3), headers=self.__headers)
                if response.status_code == 200:
                    return "Yes I'm here :) "

                raise ConnectionsError(
                    "service unreachable", "check config and try again"
                )

            response = self.__session("GET", url, retries=2, timeout=1.5)
            if response.status == 200:
                return "Yes I'm here :) "

        except Exception:
            raise ConnectionsError("service unreachable", "check config and try again")

        raise ConnectionsError("service unreachable", "check config and try again")

    def get_policies_list(self):

        """ Returns all  OPA policies in the service"""

        return self.__get_policies_list()

    def get_policies_info(self):
        """ Returns information about each policy, including
            policy path and policy rules
        """
        return self.__get_policies_info()

    def update_opa_policy_fromstring(self, new_policy, endpoint):

        """ Write your rego policy with using python string type and update your OPA policies.
            param :: new_policy : is the name of your new defined  rego policy. 
            param : endpoint : is the path of your new policy in OPA

            example:
                new_policy='''
                    package play

                    default hello = false

                    hello {
                        m := input.message
                        m == "world"
                    }
                '''
                client = OpaClient()
                client.update_opa_policy_fromstring(new_policy,'exampleapi')

        """

        return self.__update_opa_policy_fromstring(new_policy, endpoint)

    def update_opa_policy_fromfile(self, filepath, endpoint):
        return self.__update_opa_policy_fromfile(filepath, endpoint)

    def update_opa_policy_fromurl(self, url, endpoint):
        return self.__update_opa_policy_fromurl(url, endpoint)

    def update_or_create_opa_data(self, new_data, endpoint):

        """ Updates existing data or create new data for policy.

            param :: new_data : name of defined data
            type  :: new_data : dict
            param :: endpoint : is the path of your new data or existing one in OPA 
            type  :: policy_name : str
            example:
                my_policy_list = [
                    {"resource": "/api/someapi", "identity": "your_identity", "method": "PUT"},
                    {"resource": "/api/someapi", "identity": "your_identity", "method": "GET"},
                ]

                client = OpaClient()
                client.update_or_create_opa_data(my_policy_list,'exampledata/accesses')
        """

        return self.__update_opa_data(new_data, endpoint)

    def get_opa_raw_data(self, data_name):
        """Returns OPA raw data in string type """
        return self.__get_opa_raw_data(data_name)

    def opa_policy_to_file(self, policy_name, path=None, filename="opa_policy.rego"):

        """ Write OPA service policy to the  file.
            param :: policy_name : name of OPA policy
            type  :: policy_name : str

            param :: path : path to save file ,default current path
            type  :: path : str

            param :: filename : name of the file,default opa_policy.rego
            type  :: filename : str

        """
        return self.__opa_policy_to_file(policy_name, path, filename)

    def get_opa_policy(self, policy_name):

        """Returns full info about policy, provided OPA service """

        return self.__get_opa_policy(policy_name)

    def delete_opa_policy(self, policy_name):
        """ Deletes given OPA policy name """

        return self.__delete_opa_policy(policy_name)

    def delete_opa_data(self, data_name):

        """ Deletes given OPA policy data name """

        return self.__delete_opa_data(data_name)

    def check_permission(self, input_data, policy_name, rule_name):

        """
            params :: input_data    : data which you want check permission
                type   :: input_data  : dict

            params :: policy_name   : the name of policy resource 
                type   :: policy_name  : str

            params :: rule_name   : the name included in the policy  
                type   :: rule_name  : str

        """

        return self.__check(input_data, policy_name, rule_name)

    def __get_opa_raw_data(self, data_name):
        url = self.__data_root.format(self.__root_url, data_name)
        if not self.__secure:
            response = self.__session.get(url)
            code = response.status_code
            response = response.jsons()
        else:
            response = self.__session(
                "GET", url, headers=self.__headers, retries=2, timeout=1.5
            )
            code = response.status
            response = json.loads(response.data.decode("utf-8"))
        return response if code == 200 else (code, "not found")

    def __update_opa_data(self, new_data, endpoint):
        url = self.__data_root.format(self.__root_url, endpoint)
        if not self.__secure:
            response = self.__session.put(url, json=new_data)
            code = response.status_code
        else:
            encoded_json = json.dumps(new_data).encode("utf-8")
            response = self.__session(
                "PUT",
                url,
                body=encoded_json,
                headers=self.__headers,
                retries=2,
                timeout=1.5,
            )
            code = response.status
        return True if code == 204 else False

    def __update_opa_policy_fromfile(self, filepath, endpoint):
        if filepath:
            with open(filepath, "r") as rf:
                return self.__update_opa_policy_fromstring(rf.read(), endpoint)

    def __update_opa_policy_fromstring(self, new_policy, endpoint):
        if new_policy:
            url = self.__policy_root.format(self.__root_url, endpoint)
            if not self.__secure:
                response = self.__session.put(
                    url, data=new_policy.encode(), headers=self.__headers
                )
                if response.status_code == 200:
                    return True
                raise RegoParseError(
                    response.json().get("code"), response.json().get("message")
                )
            else:
                response = self.__session(
                    "PUT",
                    url,
                    body=new_policy.encode(),
                    headers=self.__headers,
                    retries=2,
                    timeout=1.5,
                )

                if response.status == 200:
                    return True

                raise RegoParseError(
                    json.loads(response.data.decode()).get("code"),
                    json.loads(response.data.decode()).get("message"),
                )

        return False

    def __get_opa_policy(self, policy_name):
        url = self.__policy_root.format(self.__root_url, policy_name)
        if not self.__secure:
            response = self.__session.get(url, headers=self.__headers)
            if response.status_code == 200:
                return response.json()

            raise PolicyNotFoundError(
                response.json().get("code"), response.json().get("message")
            )

        else:
            response = self.__session(
                "GET", url, headers=self.__headers, retries=2, timeout=1.5
            )
            data = json.loads(response.data.decode("utf-8"))
            if response.status == 200:

                return data

            raise PolicyNotFoundError(data.get("code"), data.get("message"))

    def __update_opa_policy_fromurl(self, url, endpoint):
        response = requests.get(url, headers=self.__headers)
        return self.__update_opa_policy_fromstring(response.text, endpoint)

    def __opa_policy_to_file(self, policy_name, path, filename):
        raw_policy = self.__get_opa_policy(policy_name)
        if isinstance(raw_policy, dict):
            try:
                if path:

                    with open(f"{path}/{filename}", "wb") as wr:
                        wr.write(raw_policy.get("result").get("raw").encode())
                else:
                    with open(filename, "wb") as wr:
                        wr.write(raw_policy.get("result").get("raw").encode())
                return True

            except:
                raise PathNotFoundError("error when write file", "path not found")

    def __delete_opa_policy(self, policy_name):
        url = self.__policy_root.format(self.__root_url, policy_name)
        if not self.__secure:
            response = self.__session.delete(url, headers=self.__headers)
            if response.status_code == 200:
                return True

            raise PolicyNotFoundError(
                response.json().get("code"), response.json().get("message")
            )

        else:
            response = self.__session(
                "DELETE", url, headers=self.__headers, retries=2, timeout=1.5
            )
            data = json.loads(response.data.decode("utf-8"))
            if response.status == 200:

                return True

            raise PolicyNotFoundError(data.get("code"), data.get("message"))

    def __get_policies_list(self):
        url = self.__policy_root.format(self.__root_url, "")
        temp = []
        if not self.__secure:
            response = self.__session.get(url, headers=self.__headers)
            response = response.json()
        else:
            response = self.__session(
                "GET", url, retries=2, timeout=1.5, headers=self.__headers
            )

            response = json.loads(response.data.decode())

        for policy in response.get("result"):
            if policy.get("id"):
                temp.append(policy.get("id"))

        return temp

    def __delete_opa_data(self, data_name):
        url = self.__data_root.format(self.__root_url, data_name)
        if not self.__secure:
            response = self.__session.delete(url, headers=self.__headers)
            if response.status_code == 204:
                return True

            raise DeleteDataError(
                response.json().get("code"), response.json().get("message")
            )

        else:
            response = self.__session(
                "DELETE", url, headers=self.__headers, retries=2, timeout=1.5
            )
            if response.data:
                data = json.loads(response.data.decode("utf-8"))
            if response.status == 204:

                return True

        raise DeleteDataError(data.get("code"), data.get("message"))

    def __get_policies_info(self):
        url = self.__policy_root.format(self.__root_url, "")
        if not self.__secure:
            policy = self.__session.get(url)
            result = policy.json().get("result")
        else:
            policy = self.__session(
                "GET", url, retries=2, timeout=1.0, headers=self.__headers
            )

            policy = json.loads(policy.data.decode())
            result = policy.get("result")

        permission_url = self.__root_url
        temp_dict = {}
        temp_policy = []
        temp_rules = []
        for policy in result:
            temp_policy = []
            temp_rules = []
            temp_url = ""
            permission_url = self.__root_url
            for path in policy.get("ast").get("package").get("path"):
                permission_url += "/" + path.get("value")
            temp_policy.append(permission_url)
            for rule in policy.get("ast").get("rules"):
                if not rule.get("default"):
                    continue
                temp_url = permission_url
                temp_url += "/" + rule.get("head").get("name")
                temp_rules.append(temp_url)
            temp_dict[policy.get("id")] = {"path": temp_policy, "rules": temp_rules}

        return temp_dict

    def __check(self, input_data, policy_name, rule_name):
        url = self.__policy_root.format(self.__root_url, policy_name)
        if not self.__secure:
            policy = self.__session.get(url)
            result = policy.json().get("result")
        else:
            policy = self.__session(
                "GET", url, headers=self.__headers, retries=2, timeout=1.5
            )
            policy = json.loads(policy.data.decode("utf-8"))
            result = policy.get("result")
        find = False
        permission_url = self.__root_url
        if result:
            for path in result.get("ast").get("package").get("path"):
                permission_url += "/" + path.get("value")

            for rule in result.get("ast").get("rules"):
                if not rule.get("default"):
                    continue
                if rule.get("head").get("name") == rule_name:

                    permission_url += "/" + rule.get("head").get("name")
                    find = True
        if find:
            if not self.__secure:
                response = self.__session.post(permission_url, json=input_data)
                return response.json()

            encoded_json = json.dumps(input_data).encode("utf-8")
            response = self.__session(
                "POST", permission_url, body=encoded_json, retries=2, timeout=1.5
            )
            if response.data:
                data = json.loads(response.data.decode("utf-8"))
                return data

        raise CheckPermissionError(
            f"{rule_name} rule not found", "policy or rule name not correct"
        )

