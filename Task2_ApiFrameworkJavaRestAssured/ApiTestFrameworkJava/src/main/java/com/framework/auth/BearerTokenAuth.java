package com.framework.auth;

import com.framework.config.AppConfig;
import com.framework.constants.Endpoints;
import io.restassured.http.ContentType;
import lombok.extern.log4j.Log4j2;

import java.util.Map;

import static io.restassured.RestAssured.given;

/**
 * Resolves a Restful Booker auth token via {@code POST /auth} and exposes it
 * as the {@code Cookie: token=<value>} header required by the PUT/PATCH/DELETE
 * booking endpoints.
 * <p>
 * Inference: Restful Booker does not implement the {@code Authorization: Bearer}
 * scheme; its token is supplied via a session cookie, so this strategy resolves
 * the token once and caches it for the lifetime of the strategy instance.
 */
@Log4j2
public class BearerTokenAuth implements AuthStrategy {

    private final AppConfig config;
    private volatile String cachedToken;

    public BearerTokenAuth(AppConfig config) {
        this.config = config;
    }

    @Override
    public Map<String, String> getHeaders() {
        return Map.of("Cookie", "token=" + resolveToken());
    }

    private String resolveToken() {
        if (cachedToken == null) {
            synchronized (this) {
                if (cachedToken == null) {
                    log.info("Resolving Restful Booker auth token for user '{}'", config.authUsername());
                    cachedToken = given()
                            .baseUri(config.baseUrl())
                            .contentType(ContentType.JSON)
                            .body(Map.of(
                                    "username", config.authUsername(),
                                    "password", config.authPassword()))
                            .when()
                            .post(Endpoints.AUTH)
                            .then()
                            .statusCode(200)
                            .extract()
                            .path("token");
                }
            }
        }
        return cachedToken;
    }
}
