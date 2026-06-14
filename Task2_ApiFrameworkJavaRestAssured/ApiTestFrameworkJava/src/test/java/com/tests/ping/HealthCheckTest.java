package com.tests.ping;

import com.framework.base.BaseApiTest;
import com.framework.client.ResponseValidator;
import com.framework.constants.Endpoints;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import org.testng.annotations.Test;

@Epic("Ping API")
@Feature("Health Check")
public class HealthCheckTest extends BaseApiTest {

    @Test(description = "Verify the API health check endpoint responds with 201 Created")
    @Story("Health Check")
    @Severity(SeverityLevel.BLOCKER)
    public void shouldReturnHealthy() {
        ResponseValidator
                .from(apiClient.get(Endpoints.PING))
                .assertStatusCode(201);
    }
}
