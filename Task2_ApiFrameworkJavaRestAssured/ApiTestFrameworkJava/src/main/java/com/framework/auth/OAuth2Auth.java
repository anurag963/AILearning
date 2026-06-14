package com.framework.auth;

import com.framework.config.AppConfig;
import io.restassured.http.ContentType;
import lombok.extern.log4j.Log4j2;

import java.util.HashMap;
import java.util.Map;

import static io.restassured.RestAssured.given;

/**
 * Generic OAuth2 client-credentials strategy. Resolves an access token from
 * {@code oauth2.token.url} and exposes it as {@code Authorization: Bearer <token>}.
 * <p>
 * Inference: Restful Booker does not expose an OAuth2 token endpoint - this
 * strategy is provided for framework extensibility to other target APIs and is
 * activated only when {@code auth.type=OAUTH2}.
 */
@Log4j2
public class OAuth2Auth implements AuthStrategy {

    private final AppConfig config;
    private volatile String cachedAccessToken;

    public OAuth2Auth(AppConfig config) {
        this.config = config;
    }

    @Override
    public Map<String, String> getHeaders() {
        return Map.of("Authorization", "Bearer " + resolveAccessToken());
    }

    private String resolveAccessToken() {
        if (cachedAccessToken == null) {
            synchronized (this) {
                if (cachedAccessToken == null) {
                    log.info("Resolving OAuth2 access token from {}", config.oauth2TokenUrl());

                    Map<String, String> form = new HashMap<>();
                    form.put("grant_type", "client_credentials");
                    form.put("client_id", config.oauth2ClientId());
                    form.put("client_secret", config.oauth2ClientSecret());
                    if (config.oauth2Scope() != null && !config.oauth2Scope().isBlank()) {
                        form.put("scope", config.oauth2Scope());
                    }

                    cachedAccessToken = given()
                            .contentType(ContentType.URLENC)
                            .formParams(form)
                            .when()
                            .post(config.oauth2TokenUrl())
                            .then()
                            .statusCode(200)
                            .extract()
                            .path("access_token");
                }
            }
        }
        return cachedAccessToken;
    }
}
