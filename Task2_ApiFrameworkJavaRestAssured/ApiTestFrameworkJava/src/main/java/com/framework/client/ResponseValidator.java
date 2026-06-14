package com.framework.client;

import io.restassured.response.Response;

import static io.restassured.module.jsv.JsonSchemaValidator.matchesJsonSchemaInClasspath;

/**
 * Chainable assertions over a RestAssured {@link Response}:
 * {@code assertStatusCode -> validateSchema -> extract}.
 */
public class ResponseValidator {

    private final Response response;

    private ResponseValidator(Response response) {
        this.response = response;
    }

    public static ResponseValidator from(Response response) {
        return new ResponseValidator(response);
    }

    public ResponseValidator assertStatusCode(int expectedStatusCode) {
        response.then().statusCode(expectedStatusCode);
        return this;
    }

    public ResponseValidator validateSchema(String classpathSchemaLocation) {
        response.then().body(matchesJsonSchemaInClasspath(classpathSchemaLocation));
        return this;
    }

    public <T> T extract(Class<T> type) {
        return response.as(type);
    }

    public Response raw() {
        return response;
    }
}
