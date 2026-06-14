package com.tests.booking;

import com.framework.base.BaseApiTest;
import com.framework.client.ResponseValidator;
import com.framework.constants.Endpoints;
import com.framework.models.request.PartialBookingRequest;
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
public class PartialUpdateBookingTest extends BaseApiTest {

    private int bookingId;
    private String originalLastname;
    private int originalTotalprice;

    @BeforeClass(alwaysRun = true)
    public void createBooking() {
        var createdBooking = TestDataManager.buildBookingRequest();
        originalLastname = createdBooking.getLastname();
        originalTotalprice = createdBooking.getTotalprice();

        CreateBookingResponse response = ResponseValidator
                .from(apiClient.post(Endpoints.BOOKING, createdBooking))
                .assertStatusCode(200)
                .extract(CreateBookingResponse.class);

        bookingId = response.getBookingid();
    }

    @Test(description = "Partially update a booking's firstname and verify other fields are preserved")
    @Story("Partial Update Booking")
    @Severity(SeverityLevel.NORMAL)
    public void shouldPartiallyUpdateBookingSuccessfully() {
        PartialBookingRequest partialUpdate = TestDataManager.buildPartialUpdate("James", originalLastname);

        BookingResponse response = ResponseValidator
                .from(authenticatedApiClient.patch(Endpoints.BOOKING_BY_ID, Map.of("id", bookingId), partialUpdate))
                .assertStatusCode(200)
                .validateSchema("schemas/booking-response-schema.json")
                .extract(BookingResponse.class);

        assertThat(response.getFirstname()).isEqualTo("James");
        assertThat(response.getLastname()).isEqualTo(originalLastname);
        assertThat(response.getTotalprice()).isEqualTo(originalTotalprice);
    }
}
