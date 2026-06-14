package com.framework.client;

import io.restassured.response.Response;
import io.restassured.specification.RequestSpecification;
import lombok.extern.log4j.Log4j2;

import java.util.Map;
import java.util.function.Supplier;

import static io.restassured.RestAssured.given;

/**
 * Thin wrapper around RestAssured's {@code given()} entry point. Each thread
 * receives its own {@link RequestSpecification} instance via {@link ThreadLocal}
 * so the client is safe for {@code parallel="methods"} TestNG execution.
 */
@Log4j2
public class ApiClient {

    private final ThreadLocal<RequestSpecification> specHolder;

    public ApiClient(Supplier<RequestSpecification> specSupplier) {
        this.specHolder = ThreadLocal.withInitial(specSupplier);
    }

    public Response get(String endpoint) {
        log.debug("GET {}", endpoint);
        return given(specHolder.get()).when().get(endpoint);
    }

    public Response get(String endpoint, Map<String, ?> pathParams) {
        log.debug("GET {} | pathParams: {}", endpoint, pathParams);
        return given(specHolder.get()).pathParams(pathParams).when().get(endpoint);
    }

    public Response post(String endpoint, Object body) {
        log.debug("POST {}", endpoint);
        return given(specHolder.get()).body(body).when().post(endpoint);
    }

    public Response put(String endpoint, Map<String, ?> pathParams, Object body) {
        log.debug("PUT {} | pathParams: {}", endpoint, pathParams);
        return given(specHolder.get()).pathParams(pathParams).body(body).when().put(endpoint);
    }

    public Response patch(String endpoint, Map<String, ?> pathParams, Object body) {
        log.debug("PATCH {} | pathParams: {}", endpoint, pathParams);
        return given(specHolder.get()).pathParams(pathParams).body(body).when().patch(endpoint);
    }

    public Response delete(String endpoint, Map<String, ?> pathParams) {
        log.debug("DELETE {} | pathParams: {}", endpoint, pathParams);
        return given(specHolder.get()).pathParams(pathParams).when().delete(endpoint);
    }
}
