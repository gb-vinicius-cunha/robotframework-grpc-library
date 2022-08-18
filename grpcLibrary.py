import json
import logging
import os
import re
import sys
from pathlib import Path

import grpc
from google.protobuf.json_format import Parse, ParseDict


def generate_grpc_code(service_name):
    """
    Generate the gRPC code and the respective libraries to call
    services endpoints.

    Input
    -----
     Protos location: Protos should be located in ``{service_name}/protos`` folder

    Output
    -----
     Generated code location is ``Libraries/Grpc/{service_name}Library`` folder

    Importing library
    -----------------
     ``Library  Libraries/Grpc/{service_name}Library/{proto_file_name}.py``

     E.g. Proto with name helloWorld.proto of Hello service

     ``Libraries/Grpc/HelloLibrary/helloWorld.py``

    Keywords
    ------------------
     For each service / endpoint of proto will be generated the keyword
     ``Grpc Call {service} {endpoint}``

     E.g.
     service Demo {
        rpc send(SendRequest) returns (SendResponse)
     }

     ``Grpc Call Demo Send  ${HOST}  ${DATA}  ${METADA}``

    Keyword Usage
    -------------
     For

     service Demo {
        rpc send(SendRequest) returns (SendResponse)
     }

     ``Grpc Call Demo Send  ${HOST}  ${DATA}  ${METADA}``

     ``host`` the url of service eg: localhost:8080

     ``data`` the body of request. can be dictionary ou json string

     ``metadata`` the metadata of request. dictionary

    Response object
    ---------------
     ``Grpc Call {service} {endpoint}`` keyword returns a ``GrpcReponse`` object

     res.response:  The object of response like ``SendRequest``

     res.status_code:  The string of status code. Eg. OK, INVALID_ARGUMENT

     res.metadata:  trailing_metadata of response as dictionary

     res.is_success:  True if the request returns an OK status

     res.is_error:  True if the request returns an non-OK status

     res.error:  RpcError object

     res.call:  GRPC Call object. Only for success calls, `null` for non-OK response

    Parameters
    ----------
     service_name : string
        Name of Service. Used to find protos in ``{service_name}/protos`` folder and
        store generated code in ``Libraries/Grpc/{service_name}Library``
    """
    output_folder = f"Libraries/Grpc/{service_name}Library"

    logging.info("Generating GRPC code at " + output_folder)

    path = Path(output_folder)
    path.mkdir(parents=True, exist_ok=True)

    str_proto_path = f"{service_name}/protos"

    logging.info("Loading protos at " + str_proto_path)

    proto_path = Path(str_proto_path)
    for entry in proto_path.iterdir():
        if entry.is_file() & entry.name.endswith(".proto"):
            logging.info(f"Generating GRPC code of proto {entry.name}")
            os.system(
                f"python -m grpc_tools.protoc -I{service_name}/protos \
                                        --proto_path={_site_packages_path()} \
                                        --python_out={output_folder} \
                                        --grpc_python_out={output_folder} \
                                        {entry.name}"
            )

            _create_keyword_file(entry, output_folder)

    logging.info("Codes generated successfully")


service_pattern = r"^service (.*) {"
endpoint_pattern = r"^rpc\s*([a-zA-Z]+)\s*\(([a-zA-Z]+)\)\s*returns\s*\([stream ]*([a-zA-Z]+)\).*"


def _create_keyword_file(proto_path, output_folder):
    services = _read_proto(proto_path)

    file_name = proto_path.name[0:-6]
    _write_keyword_file(services, output_folder, file_name)


def _read_proto(proto_path):
    """
    Read a proto file and extract services and enpoints

    Parameters
    ----------
    proto_path : Location of proto

    Returns
    -------
    list
       a list of services and theirs endpoints
    """
    services = []

    with open(proto_path) as proto:
        for line in proto:
            fix_line = line.strip()
            if fix_line:

                if _is_service(fix_line):
                    service_name = re.search(service_pattern, fix_line).group(
                        1
                    )
                    cur_service = _GrpcServiceDef(service_name)
                    services.append(cur_service)

                if _is_endpoint(fix_line):
                    result = re.search(endpoint_pattern, fix_line)

                    endpoint = _GrpcEndpointDef(
                        name=result.group(1),
                        request=result.group(2),
                        response=result.group(3),
                    )

                    cur_service.add_endpoint(endpoint)

    return services


def _write_keyword_file(services, output_folder, file_name):
    """
    Based on list of services write a keyword file with all endpoints and services

    Parameters
    ----------
    services : list
       list of services definitions
    output_folder : str
       path of folder where the files will be stored
    file_name : str
       name of file to be used as name of *.py keyword file
    """

    with open("grpcKeywordTemplate") as file:
        endpoint_template_data = file.read()

    with open(f"{output_folder}/{file_name}.py", "w") as keyword_file:
        keyword_file.write(
            "import grpc\n"
            f"import {file_name}_pb2\n"
            f"import {file_name}_pb2_grpc\n"
            "from grpcLibrary import GrpcResponse, parse_data, parse_metadata, create_channel\n"
        )

        for service in services:
            for endpoint in service.endpoints:
                endpoint_data = (
                    endpoint_template_data.replace("{file_name}", file_name)
                    .replace("{service_name}", service.name)
                    .replace("{endpoint}", endpoint.name)
                    .replace("{request}", endpoint.request)
                )
                keyword_file.write("\n\n" + endpoint_data)


def _is_service(line):
    """returns if line is a Service line"""
    return re.match(service_pattern, line)


def _is_endpoint(line):
    """returns if line is an Endpoint line"""
    return re.match(endpoint_pattern, line)


def _site_packages_path():
    python_path = sys.exec_prefix
    python_version = sys.version_info
    return f"{python_path}/lib/python{python_version.major}.{python_version.minor}/site-packages"


class _GrpcServiceDef:
    def __init__(self, name):
        self._name = name
        self._endpoints = []

    @property
    def name(self):
        return self._name

    @property
    def endpoints(self):
        return self._endpoints

    def add_endpoint(self, endpoint):
        self._endpoints.append(endpoint)


class _GrpcEndpointDef:
    def __init__(self, name, request, response):
        self._name = name
        self._request = request
        self._response = response

    @property
    def name(self):
        return self._name

    @property
    def request(self):
        return self._request

    @property
    def response(self):
        return self._response


class GrpcResponse:
    def __init__(self, response=None, call=None, error=None):
        self._call = call
        self._response = response
        self._error = error
        self._status_code = call.code() if call else error.code()

    @property
    def call(self):
        """
        GRPC native Call object

        Only for success calls, `null` for non-OK response
        """
        return self._call

    @property
    def response(self):
        """
        The object of response as defined in proto

        Only for success calls, `null` for non-OK response
        """
        return self._response

    @property
    def status_code(self):
        """The string representation of status code. Eg. `OK`, `INVALID_ARGUMENT`"""
        return self._status_code.name

    @property
    def error(self):
        """
        GRPC native RpcError object

        Only for non-OK calls, `null` for OK response
        """
        return self._error

    @property
    def metadata(self):
        """trailing_metadata of response as dictionary"""
        if self.is_success():
            trailing_metadata = self._call.trailing_metadata()
        else:
            trailing_metadata = self._error.trailing_metadata()

        return self._metadata_to_dict(trailing_metadata)

    def _metadata_to_dict(self, trailing_metadata):
        """transform trailing_metadata tuples to dictionary"""
        metadata = {}
        for key, value in trailing_metadata:
            metadata[key] = value
        return metadata

    def is_success(self):
        """True if is an OK call. False otherwise"""
        return not self._error

    def is_error(self):
        """True if is a non-OK call. False otherwise"""
        return not self.is_success()


def parse_data(request, data):
    """
    Convert data as JSON String or Dictionary in grpc request object

    Parameters
    ----------
    request : instance grpc request object as defined in proto
    data : str or dict
       The data of request as JSON String or dictionary
    """
    if data:
        if isinstance(data, dict):
            return ParseDict(data, request)
        elif isinstance(data, str):
            return Parse(json.dumps(data), request)
        else:
            raise AttributeError(
                "Invalid Type! Data should be JSON Str or Dict type"
            )
    else:
        return request


def parse_metadata(metadata):
    """
    Convert metadata aDictionary in list of tuples

    Parameters
    ----------
    metadata : dict
       The dictionary of metadata to be send in gRPC Call
    """
    req_metadata = []
    if metadata:

        if not isinstance(metadata, dict):
            raise AttributeError("Invalid Type! Metadata should be Dict type")

        for key, value in metadata.items():
            req_metadata.append((key, value))

    return req_metadata


def create_channel(host, secure):
    return (
        grpc.secure_channel(
            target=host, credentials=grpc.ssl_channel_credentials()
        )
        if secure
        else grpc.insecure_channel(target=host)
    )


if __name__ == "__main__":
    generate_grpc_code(sys.argv[1])
