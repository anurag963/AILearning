package com.framework.constants;

/**
 * Restful Booker API path constants. Paths only - never full URLs;
 * {@code RestAssured.baseURI} supplies the host.
 */
public final class Endpoints {

    private Endpoints() {
    }

    public static final String AUTH = "/auth";
    public static final String PING = "/ping";
    public static final String BOOKING = "/booking";
    public static final String BOOKING_BY_ID = "/booking/{id}";
}
