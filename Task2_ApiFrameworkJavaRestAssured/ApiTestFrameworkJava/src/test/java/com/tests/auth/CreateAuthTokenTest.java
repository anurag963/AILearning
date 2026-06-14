package com.tests.auth;

import com.framework.base.BaseApiTest;
import com.framework.client.ResponseValidator;
import com.framework.constants.Endpoints;
import com.framework.models.request.AuthRequest;
import com.framework.models.response.AuthResponse;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import org.testng.annotations.Test;

import static org.assertj.core.api.Assertions.assertThat;

@Epic("Auth API")
@Feature("Token Management")
public class CreateAuthTokenTest extends BaseApiTest {

    @Test(description = "Create an auth token with valid credentials and verify a non-empty token is returned")
    @Story("Create Token")
    @Severity(SeverityLevel.CRITICAL)
    public void shouldCreateAuthTokenSuccessfully() {
        AuthRequest request = AuthRequest.builder()
                .username("admin")
                .password("password123")
                .build();

        AuthResponse response = ResponseValidator
                .from(apiClient.post(Endpoints.AUTH, request))
                .assertStatusCode(200)
                .validateSchema("schemas/auth-response-schema.json")
                .extract(AuthResponse.class);

        assertThat(response.getToken()).isNotBlank();
    }
}
