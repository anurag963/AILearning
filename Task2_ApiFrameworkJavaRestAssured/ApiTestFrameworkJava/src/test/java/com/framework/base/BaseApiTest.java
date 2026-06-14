package com.framework.base;

import com.framework.client.ApiClient;
import com.framework.client.RequestResponseLoggingFilter;
import com.framework.config.ConfigManager;
import com.framework.listeners.RetryListener;
import com.framework.utils.JsonUtils;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.config.ObjectMapperConfig;
import io.restassured.config.RestAssuredConfig;
import io.restassured.http.ContentType;
import io.restassured.mapper.ObjectMapperType;
import io.restassured.specification.RequestSpecification;
import lombok.extern.log4j.Log4j2;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.Listeners;

/**
 * Suite-level wiring: builds the shared {@link RequestSpecification} supplier,
 * registers Allure + logging filters, configures the global Jackson object
 * mapper, and exposes a thread-safe {@link ApiClient} to all test classes.
 */
@Log4j2
@Listeners({RetryListener.class})
public class BaseApiTest {

    /** Unauthenticated client - used for GET/POST endpoints that require no token. */
    protected static ApiClient apiClient;

    /** Client carrying the resolved auth headers - used for PUT/PATCH/DELETE booking endpoints. */
    protected static ApiClient authenticatedApiClient;

    @BeforeSuite(alwaysRun = true)
    public void initSuite() {
        RestAssured.baseURI = ConfigManager.config().baseUrl();
        RestAssured.useRelaxedHTTPSValidation();
        RestAssured.filters(new AllureRestAssured(), new RequestResponseLoggingFilter());
        RestAssured.config = RestAssuredConfig.config().objectMapperConfig(
                ObjectMapperConfig.objectMapperConfig()
                        .jackson2ObjectMapperFactory((cls, charset) -> JsonUtils.objectMapper())
                        .defaultObjectMapperType(ObjectMapperType.JACKSON_2));

        apiClient = new ApiClient(() -> new RequestSpecBuilder()
                .setContentType(ContentType.JSON)
                .build());

        authenticatedApiClient = new ApiClient(() -> new RequestSpecBuilder()
                .setContentType(ContentType.JSON)
                .addHeaders(ConfigManager.authStrategy().getHeaders())
                .build());

        log.info("Suite initialised. Environment: {}, Base URI: {}",
                ConfigManager.config().env(), RestAssured.baseURI);
    }

    @AfterSuite(alwaysRun = true)
    public void teardownSuite() {
        log.info("Suite teardown complete.");
    }
}
