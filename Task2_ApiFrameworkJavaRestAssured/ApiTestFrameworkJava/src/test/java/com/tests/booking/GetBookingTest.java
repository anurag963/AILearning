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
public class GetBookingTest extends BaseApiTest {

    private int bookingId;
    private BookingRequest createdBooking;

    @BeforeClass(alwaysRun = true)
    public void createBooking() {
        createdBooking = TestDataManager.buildBookingRequest();

        CreateBookingResponse response = ResponseValidator
                .from(apiClient.post(Endpoints.BOOKING, createdBooking))
                .assertStatusCode(200)
                .extract(CreateBookingResponse.class);

        bookingId = response.getBookingid();
    }

    @Test(description = "Get booking by id and verify response matches created booking")
    @Story("Get Booking")
    @Severity(SeverityLevel.CRITICAL)
    public void shouldGetBookingByIdSuccessfully() {
        BookingResponse response = ResponseValidator
                .from(apiClient.get(Endpoints.BOOKING_BY_ID, Map.of("id", bookingId)))
                .assertStatusCode(200)
                .validateSchema("schemas/booking-response-schema.json")
                .extract(BookingResponse.class);

        assertThat(response.getFirstname()).isEqualTo(createdBooking.getFirstname());
        assertThat(response.getLastname()).isEqualTo(createdBooking.getLastname());
        assertThat(response.getTotalprice()).isEqualTo(createdBooking.getTotalprice());
        assertThat(response.getBookingdates().getCheckin()).isEqualTo(createdBooking.getBookingdates().getCheckin());
    }

    @Test(description = "Get all booking ids and verify the created booking id is present")
    @Story("Get Booking Ids")
    @Severity(SeverityLevel.NORMAL)
    public void shouldGetAllBookingIds() {
        ResponseValidator
                .from(apiClient.get(Endpoints.BOOKING))
                .assertStatusCode(200)
                .validateSchema("schemas/booking-ids-response-schema.json")
                .raw()
                .then()
                .body("findAll { it.bookingid == " + bookingId + " }", org.hamcrest.Matchers.hasSize(1));
    }
}
