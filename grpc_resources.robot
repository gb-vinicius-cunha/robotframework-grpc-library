*** Settings ***
Library  Collections

*** Keywords ***

Request Should Be Successful
    [Documentation]  Fails if is a non-OK response. In this case error object 
    ...              will be not null and response will be null
    [Arguments]  ${RESPONSE}
    Should Be True    ${RESPONSE.is_success()}

Request Should Be Error
    [Documentation]  Fails if is a non-OK response. In this case response object 
    ...              will be not null and error will be null
    [Arguments]  ${RESPONSE}
    Should Be True    ${RESPONSE.is_error()}

Status Should Be
    [Documentation]  Fails if response status code is different than the expected.
    [Arguments]  ${RESPONSE}  ${STATUS}
    Should Be Equal    ${RESPONSE.status_code}  ${STATUS}

Error Message Should Be
    [Documentation]  Fails if details of error response is different than the expected.
    [Arguments]  ${MESSAGE}  ${RESPONSE}
    Should Be Equal    ${MESSAGE}    ${RESPONSE.error.details()}

Metadata Should Contain
    [Documentation]  Fails if metadata of response not contains METADATA_KEY.
    ...              If pass an optional METADATA_VALUE, fails if value is different than the expected. 
    [Arguments]  ${RESPONSE}  ${METADATA_KEY}  ${METADATA_VALUE}=

    IF  $METADATA_VALUE == ''
        Dictionary Should Contain Key   ${RESPONSE.metadata}    ${METADATA_KEY}
    ELSE
        Dictionary Should Contain Item  ${RESPONSE.metadata}    ${METADATA_KEY}    ${METADATA_VALUE}
    END
    