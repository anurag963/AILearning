package com.framework.config;

import com.framework.auth.ApiKeyAuth;
import com.framework.auth.AuthStrategy;
import com.framework.auth.BearerTokenAuth;
import com.framework.auth.OAuth2Auth;
import lombok.extern.log4j.Log4j2;
import org.aeonbits.owner.ConfigFactory;

/**
 * Lazily-initialised singleton providing thread-safe access to {@link AppConfig}
 * and the resolved {@link AuthStrategy} for the current environment.
 * <p>
 * Environment is resolved from the {@code env} system property (default: {@code dev}),
 * passed via {@code -Denv=qa|staging|prod}.
 */
@Log4j2
public final class ConfigManager {

    private static volatile AppConfig config;
    private static volatile AuthStrategy authStrategy;

    private ConfigManager() {
    }

    public static AppConfig config() {
        if (config == null) {
            synchronized (ConfigManager.class) {
                if (config == null) {
                    System.setProperty("env", System.getProperty("env", "dev"));
                    config = ConfigFactory.create(AppConfig.class, System.getProperties());
                    log.info("Loaded configuration for env '{}', baseUrl '{}'", config.env(), config.baseUrl());
                }
            }
        }
        return config;
    }

    public static AuthStrategy authStrategy() {
        if (authStrategy == null) {
            synchronized (ConfigManager.class) {
                if (authStrategy == null) {
                    authStrategy = switch (config().authType().toUpperCase()) {
                        case "TOKEN" -> new BearerTokenAuth(config());
                        case "OAUTH2" -> new OAuth2Auth(config());
                        case "API_KEY" -> new ApiKeyAuth(config());
                        default -> throw new IllegalStateException(
                                "Unsupported auth.type: " + config().authType());
                    };
                    log.info("Resolved auth strategy '{}' for env '{}'", authStrategy.getClass().getSimpleName(), config().env());
                }
            }
        }
        return authStrategy;
    }
}
