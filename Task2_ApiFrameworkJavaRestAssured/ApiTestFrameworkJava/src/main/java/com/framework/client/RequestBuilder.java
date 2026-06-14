package com.framework.client;

import io.restassured.builder.RequestSpecBuilder;
import io.restassured.specification.RequestSpecification;

import java.util.Map;

/**
 * Fluent builder for one-off request customisations (extra headers, query/path
 * params, body) layered on top of the shared {@link RequestSpecification}.
 */
public class RequestBuilder {

    private final RequestSpecBuilder specBuilder;

    public RequestBuilder(RequestSpecification base) {
        this.specBuilder = new RequestSpecBuilder().addRequestSpecification(base);
    }

    public RequestBuilder withHeader(String name, String value) {
        specBuilder.addHeader(name, value);
        return this;
    }

    public RequestBuilder withHeaders(Map<String, String> headers) {
        headers.forEach(specBuilder::addHeader);
        return this;
    }

    public RequestBuilder withQueryParam(String name, Object value) {
        specBuilder.addQueryParam(name, String.valueOf(value));
        return this;
    }

    public RequestBuilder withQueryParams(Map<String, ?> params) {
        params.forEach((name, value) -> specBuilder.addQueryParam(name, String.valueOf(value)));
        return this;
    }

    public RequestBuilder withPathParam(String name, Object value) {
        specBuilder.addPathParam(name, String.valueOf(value));
        return this;
    }

    public RequestBuilder withBody(Object body) {
        specBuilder.setBody(body);
        return this;
    }

    public RequestSpecification build() {
        return specBuilder.build();
    }
}
