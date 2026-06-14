package com.tests.booking;

import com.framework.base.BaseApiTest;
import com.framework.client.ResponseValidator;
import com.framework.constants.Endpoints;
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

@Epic("Booking API")
@Feature("Booking Management")
public class DeleteBookingTest extends BaseApiTest {

    private int bookingId;

    @BeforeClass(alwaysRun = true)
    public void createBooking() {
        CreateBookingResponse response = ResponseValidator
                .from(apiClient.post(Endpoints.BOOKING, TestDataManager.buildBookingRequest()))
                .assertStatusCode(200)
                .extract(CreateBookingResponse.class);

        bookingId = response.getBookingid();
    }

    @Test(description = "Delete a booking and verify the booking id is gone")
    @Story("Delete Booking")
    @Severity(SeverityLevel.CRITICAL)
    public void shouldDeleteBookingSuccessfully() {
        ResponseValidator
                .from(authenticatedApiClient.delete(Endpoints.BOOKING_BY_ID, Map.of("id", bookingId)))
                .assertStatusCode(201);

        ResponseValidator
                .from(apiClient.get(Endpoints.BOOKING_BY_ID, Map.of("id", bookingId)))
                .assertStatusCode(404);
    }
}
