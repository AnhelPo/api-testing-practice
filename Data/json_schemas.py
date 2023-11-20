"""JSON-схемы проекта API_tests_example"""

COMPANIES_MAIN = {
    "type": "object",
    "properties": {
        "data": {
            "type": "array",
            "items":
                {
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer"
                        },
                        "company_name": {
                            "type": "string"
                        },
                        "company_address": {
                            "type": "string"
                        },
                        "company_status": {
                            "type": "string",
                            "enum": ["ACTIVE", "CLOSED", "BANKRUPT"]
                        },
                        "description": {
                            "type": "string"
                        },
                        "description_lang": {
                            "type": "array",
                            "items":
                                {
                                    "type": "object",
                                    "properties": {
                                        "translation_lang": {
                                            "type": "string"
                                        },
                                        "translation": {
                                            "type": "string"
                                        }
                                    },
                                    "required": [
                                        "translation_lang",
                                        "translation"
                                    ]
                                }

                        }
                    },
                    "required": [
                        "company_id",
                        "company_name",
                        "company_address",
                        "company_status"
                    ]
                }

        },
        "meta": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer"
                },
                "offset": {
                    "type": "integer"
                },
                "total": {
                    "type": "integer"
                }
            },
            "required": [
                "total"
            ]
        }
    },
    "required": [
        "data",
        "meta"
    ]
}

COMPANY_BY_ID = {
    "type": "object",
    "properties": {
        "company_id": {
            "type": "integer"
        },
        "company_name": {
            "type": "string"
        },
        "company_address": {
            "type": "string"
        },
        "company_status": {
            "type": "string",
            "enum": ["ACTIVE", "BANKRUPT", "CLOSED"]
        },
        "description_lang": {
            "type": "array",
            "items":
                {
                    "type": "object",
                    "properties": {
                        "translation_lang": {
                            "type": "string",
                            "enum": ["EN", "RU", "PL", "UA"]
                        },
                        "translation": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "translation_lang",
                        "translation"
                    ]
                }
        }
    },
    "oneOf": [
        {
            "required": ["description"]
        },
        {
            "required": ["description_lang"]
        }
    ],
    "required": [
        "company_id",
        "company_name",
        "company_address",
        "company_status"
    ]
}

USERS_MAIN = {
    "type": "object",
    "properties": {
        "meta": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer"
                },
                "offset": {
                    "type": "integer"
                },
                "total": {
                    "type": "integer"
                }
            },
            "required": [
                "total"
            ]
        },
        "data": {
            "type": "array",
            "items":
                {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": ["string", "null"]
                        },
                        "last_name": {
                            "type": "string"
                        },
                        "company_id": {
                            "type": ["integer", "null"]
                        },
                        "user_id": {
                            "type": "integer"
                        }
                    },
                    "required": [
                        "last_name",
                        "user_id"
                    ]
                }

        }
    },
    "required": [
        "meta",
        "data"
    ]
}

USER_BY_ID = {
    "type": "object",
    "properties": {
        "first_name": {
            "type": ["string", "null"],
        },
        "last_name": {
            "type": "string",
        },
        "company_id": {
            "type": ["integer", "null"],
        },
        "user_id": {
            "type": "integer",
        }
    },
    "required": [
        "first_name",
        "last_name",
        "company_id",
        "user_id"
    ]
}

USER_CREATED = {
    "type": "object",
    "properties": {
        "first_name": {
            "type": ["string", "null"]
        },
        "last_name": {
            "type": "string"
        },
        "company_id": {
            "type": ["integer", "null"]
        },
        "user_id": {
            "type": "integer"
        }
    },
    "required": [
        "first_name",
        "last_name",
        "company_id",
        "user_id"
    ]
}

BAD_REQUEST_400 = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string"
                }
            },
            "required": [
                "reason"
            ]
        }
    },
    "required": [
        "detail"
    ]
}

UNPROCESSABLE_ENTITY_422 = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "loc": {
                            "type": "array",
                            "items": {
                                "type": ["string", "integer"]
                            }
                        },
                        "msg": {
                            "type": "string"
                        },
                        "type": {
                            "type": "string"
                        },
                    },
                    "required": [
                        "loc",
                        "msg",
                        "type"
                    ]
                }
            ]
        }
    },
    "required": [
        "detail"
    ]
}

NOT_FOUND_404 = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string"
                }
            },
            "required": [
                "reason"
            ]
        }
    },
    "required": [
        "detail"
    ]
}
