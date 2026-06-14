package com.framework.auth;

import com.framework.config.AppConfig;

import java.util.Map;

/**
 * Static API-key strategy. Exposes the configured {@code apikey.header.name}
 * header with value {@code apikey.value}.
 * <p>
 * Inference: Restful Booker does not require an API key - this strategy is
 * provided for framework extensibility to other target APIs and is activated
 * only when {@code auth.type=API_KEY}.
 */
public class ApiKeyAuth implements AuthStrategy {

    private final AppConfig config;

    public ApiKeyAuth(AppConfig config) {
        this.config = config;
    }

    @Override
    public Map<String, String> getHeaders() {
        return Map.of(config.apiKeyHeaderName(), config.apiKeyValue());
    }
}
