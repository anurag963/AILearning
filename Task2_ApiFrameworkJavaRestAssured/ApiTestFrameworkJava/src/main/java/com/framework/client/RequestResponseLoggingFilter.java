package com.framework.client;

import io.restassured.filter.Filter;
import io.restassured.filter.FilterContext;
import io.restassured.response.Response;
import io.restassured.specification.FilterableRequestSpecification;
import io.restassured.specification.FilterableResponseSpecification;
import lombok.extern.log4j.Log4j2;

/**
 * Logs every outbound request and inbound response via Log4j2 at DEBUG level.
 * Registered globally on {@code RestAssured.filters(...)} in {@code BaseApiTest}.
 */
@Log4j2
public class RequestResponseLoggingFilter implements Filter {

    @Override
    public Response filter(FilterableRequestSpecification requestSpec,
                            FilterableResponseSpecification responseSpec,
                            FilterContext ctx) {
        log.debug("--> " + requestSpec.getMethod() + " " + requestSpec.getURI());
        log.debug("Request headers: " + requestSpec.getHeaders());
        if (requestSpec.getBody() != null) {
            log.debug("Request body: " + requestSpec.getBody());
        }

        Response response = ctx.next(requestSpec, responseSpec);

        log.debug("<-- " + response.getStatusCode() + " " + requestSpec.getURI() + " (" + response.getTime() + " ms)");
        log.debug("Response body: " + response.getBody().asPrettyString());

        return response;
    }
}
