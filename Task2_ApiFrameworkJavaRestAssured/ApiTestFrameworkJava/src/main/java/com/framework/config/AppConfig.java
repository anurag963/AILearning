package com.framework.config;

import org.aeonbits.owner.Config;

/**
 * Type-safe configuration contract resolved via Owner.
 * Environment is selected through the {@code env} system property (default: dev),
 * loaded from {@code classpath:config/<env>.properties}.
 */
@Config.Sources({
        "classpath:config/${env}.properties"
})
public interface AppConfig extends Config {

    @Key("env")
    @DefaultValue("dev")
    String env();

    @Key("base.url")
    String baseUrl();

    @Key("thread.count")
    @DefaultValue("4")
    int threadCount();

    @Key("retry.count")
    @DefaultValue("2")
    int retryCount();

    @Key("auth.type")
    @DefaultValue("TOKEN")
    String authType();

    @Key("auth.username")
    String authUsername();

    @Key("auth.password")
    String authPassword();

    @Key("oauth2.token.url")
    String oauth2TokenUrl();

    @Key("oauth2.client.id")
    String oauth2ClientId();

    @Key("oauth2.client.secret")
    String oauth2ClientSecret();

    @Key("oauth2.scope")
    String oauth2Scope();

    @Key("apikey.header.name")
    @DefaultValue("x-api-key")
    String apiKeyHeaderName();

    @Key("apikey.value")
    String apiKeyValue();
}
