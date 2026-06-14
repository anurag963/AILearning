package com.tests.booking;

import com.framework.base.BaseApiTest;
import com.framework.client.ResponseValidator;
import com.framework.constants.Endpoints;
import com.framework.models.request.BookingRequest;
import com.framework.models.response.BookingResponse;
import com.framework.models.response.CreateBookingResponse;
import com.framework.utils.TestDataManager;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@Epic("Booking API")
@Feature("Booking Management")
public class UpdateBookingTest extends BaseApiTest {

    private int bookingId;

    @BeforeClass(alwaysRun = true)
    public void createBooking() {
        CreateBookingResponse response = ResponseValidator
                .from(apiClient.post(Endpoints.BOOKING, TestDataManager.buildBookingRequest()))
                .assertStatusCode(200)
                .extract(CreateBookingResponse.class);

        bookingId = response.getBookingid();
    }

    @Test(description = "Update an existing booking and verify the response reflects the new values")
    @Story("Update Booking")
    @Severity(SeverityLevel.CRITICAL)
    public void shouldUpdateBookingSuccessfully() {
        BookingRequest updateRequest = TestDataManager.buildBookingRequest();

        BookingResponse response = ResponseValidator
                .from(authenticatedApiClient.put(Endpoints.BOOKING_BY_ID, Map.of("id", bookingId), updateRequest))
                .assertStatusCode(200)
                .validateSchema("schemas/booking-response-schema.json")
                .extract(BookingResponse.class);

        assertThat(response.getFirstname()).isEqualTo(updateRequest.getFirstname());
        assertThat(response.getLastname()).isEqualTo(updateRequest.getLastname());
        assertThat(response.getTotalprice()).isEqualTo(updateRequest.getTotalprice());
        assertThat(response.isDepositpaid()).isEqualTo(updateRequest.isDepositpaid());
        assertThat(response.getAdditionalneeds()).isEqualTo(updateRequest.getAdditionalneeds());
    }
}
