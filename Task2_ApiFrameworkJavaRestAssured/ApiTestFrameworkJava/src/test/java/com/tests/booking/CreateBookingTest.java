package com.tests.booking;

import com.framework.base.BaseApiTest;
import com.framework.client.ResponseValidator;
import com.framework.constants.Endpoints;
import com.framework.models.request.BookingRequest;
import com.framework.models.response.CreateBookingResponse;
import com.framework.utils.TestDataManager;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import org.testng.annotations.Test;

import static org.assertj.core.api.Assertions.assertThat;

@Epic("Booking API")
@Feature("Booking Management")
public class CreateBookingTest extends BaseApiTest {

    @Test(description = "Create booking and verify 200 with valid booking ID")
    @Story("Create Booking")
    @Severity(SeverityLevel.CRITICAL)
    public void shouldCreateBookingSuccessfully() {
        BookingRequest request = TestDataManager.buildBookingRequest();

        CreateBookingResponse response = ResponseValidator
                .from(apiClient.post(Endpoints.BOOKING, request))
                .assertStatusCode(200)
                .validateSchema("schemas/create-booking-response-schema.json")
                .extract(CreateBookingResponse.class);

        assertThat(response.getBookingid()).isPositive();
        assertThat(response.getBooking().getFirstname()).isEqualTo(request.getFirstname());
        assertThat(response.getBooking().getLastname()).isEqualTo(request.getLastname());
        assertThat(response.getBooking().getTotalprice()).isEqualTo(request.getTotalprice());
        assertThat(response.getBooking().getBookingdates().getCheckin())
                .isEqualTo(request.getBookingdates().getCheckin());
    }
}
