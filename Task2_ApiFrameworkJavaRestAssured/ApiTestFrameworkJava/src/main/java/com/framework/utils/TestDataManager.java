package com.framework.utils;

import com.framework.models.request.BookingDates;
import com.framework.models.request.BookingRequest;
import com.framework.models.request.PartialBookingRequest;
import com.github.javafaker.Faker;

import java.time.LocalDate;
import java.time.ZoneId;

/**
 * Faker-backed builder for randomised, non-colliding Restful Booker test data.
 */
public final class TestDataManager {

    private static final Faker FAKER = new Faker();

    private TestDataManager() {
    }

    public static BookingRequest buildBookingRequest() {
        LocalDate checkin = LocalDate.now(ZoneId.systemDefault()).plusDays(FAKER.number().numberBetween(1, 30));
        LocalDate checkout = checkin.plusDays(FAKER.number().numberBetween(1, 14));

        return BookingRequest.builder()
                .firstname(FAKER.name().firstName())
                .lastname(FAKER.name().lastName())
                .totalprice(FAKER.number().numberBetween(50, 1000))
                .depositpaid(FAKER.bool().bool())
                .bookingdates(BookingDates.builder()
                        .checkin(checkin)
                        .checkout(checkout)
                        .build())
                .additionalneeds(FAKER.options().option("Breakfast", "Lunch", "Dinner", "Late checkout"))
                .build();
    }

    public static PartialBookingRequest buildPartialUpdate(String firstname, String lastname) {
        return PartialBookingRequest.builder()
                .firstname(firstname)
                .lastname(lastname)
                .build();
    }
}
