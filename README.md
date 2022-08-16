# robotframework-grpc-library

``GrpcLibrary`` is a [Robot Framework](https://robotframework.org/) library
aimed to provide gRPC api testing functionalities by wrapping the well known [Python gRPC Library](https://grpc.io/docs/languages/python/).

## How to use

In this early stage it's necessary download the script and his template

1 - Download the files above and place to root of project

- grpcLibrary.py
- grpcKeywodTemplate

2 - Install dependencies listed in requirements.txt

- grpcio-tools
- grpcio
- protobuf
- types-protobuf

3 - Create a folder for your service with `/protos` folder inside with respective proto files

4 - Run the script

```
python grpcLibrary.py {service_name}
```

As result `Libraries/Grpc/{service_name}Library/` folder will be created with respective files

To use just add import

```robotframework
*** Settings ***
Library  /Libraries/Grpc/{service_name}Library/{proto_file_name}.py
```

## Keywords

The generated library provides the keyword

`Grpc Call {Service Name} {Endpoint Name}` 

So there is a `Grpc Call` keyword for each endpoint on proto file. Wich returns a `GrpcResponse` object

```robotframework
*** Settings ***
Library  /Libraries/Grpc/GrpcDemoLibrary/demoGrpc.py

*** Variables ***
${DEMO_URL}  localhost:8080

*** Keywords ***

Call Send Endpoint
    ${METADATA}=  Create Dictionary                correlation-id=1234
    ${BODY}=      Set Variable                     { "name" : 'Luke' }
    ${RESPONSE}=  Grpc Call DemoGrpcService Send   ${DEMO_URL}          ${BODY}  ${METADATA}
    [return]  ${RESPONSE}
```

### Arguments

| Argument | Type      | Required | Description                               |
| -------- | -------   | -------- | ----------------------------------------- |
| host     | str       | yes      | url of gRPC service                       |
| data     | str, dict | no       | request body in JSON String or Dictionary |
| metadata | dict      | no       | Dicitonary with metadata                  | 

### GrpcResponse Object

Como retorno você receberá um objeto **GrpcReponse** que incluí os atributos abaixo

| Property      | Description                                                    | Avaiable         |
| ------------- | -------------------------------------------------------------- | ---------------- |
| response      | Object of response, as defined on proto file                   | OK Responses     |
| status_code   | String representation of gRPC status. Eg. OK, INVALID_ARGUMENT | Always           |
| metadata      | Trailing Metadata of response                                  | Always           |
| error         | RpcError trew by gRPC                                          | non-OK Responses |
| call          | Object call of gRPC                                            | OK Responses     |
| is_success()  | True if response was OK                                        | Always           |
| is_error()    | True if response was non-OK                                    | Always           |

## Test examples

You can find a few test examples in `grpc_resource.robot` file.

Inside a GrpcDemo folder you can find the proto used in these examples