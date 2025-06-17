import datetime
from typing import Set, Tuple, Union

from sqlalchemy import Column
from sqlalchemy.orm import Session

from . import models, schemas


class UnableToBook(Exception):
    pass


def create_booking(db: Session, booking: schemas.BookingBase) -> models.Booking:
    (is_possible, reason) = is_booking_possible(db=db, booking=booking)
    if not is_possible:
        raise UnableToBook(reason)
    db_booking = models.Booking(
        guest_name=booking.guest_name,
        unit_id=booking.unit_id,
        check_in_date=booking.check_in_date,
        number_of_nights=booking.number_of_nights,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def extend_booking(db: Session, booking: schemas.BookingBase) -> models.Booking:
    current_booking = (
        db.query(models.Booking)
        .filter_by(
            guest_name=booking.guest_name,
            unit_id=booking.unit_id,
            check_in_date=booking.check_in_date,
        )
        .first()
    )
    if current_booking is None:
        raise UnableToBook("Unable to find current booking")

    if current_booking.number_of_nights >= booking.number_of_nights:
        raise UnableToBook(
            "Number of nights to extend is fewer than current number of nights"
        )
    # get revised check_in_date and difference number of nights to leverage
    # is_booking_possible validator
    desired_number_of_nights = booking.number_of_nights
    booking.check_in_date = current_booking.check_in_date + datetime.timedelta(
        current_booking.number_of_nights
    )
    booking.number_of_nights = (
        desired_number_of_nights - current_booking.number_of_nights
    )
    # leverage is_booking_possible validator
    (is_possible, reason) = is_booking_possible(db=db, booking=booking)
    if not is_possible:
        raise UnableToBook(reason)

    # update number of nights to desired amount
    current_booking.number_of_nights = desired_number_of_nights

    db.commit()
    db.refresh(current_booking)
    return current_booking


def get_occupancy_dates(
    check_in_date: Union[datetime.date, Column[datetime.date]],
    nights: Union[int, Column[int]],
) -> Set[str]:
    return set(
        (check_in_date + datetime.timedelta(days=night)).strftime("%Y-%m-%d")
        for night in range(0, nights)
    )


def check_conflicting_occupancy_dates(
    query_booking: models.Booking, new_booking: schemas.BookingBase
) -> bool:
    """
    This takes in two bookings as objects of comparison, generates full date sets
    from their checkin_dates and number of nights, and sees if there is an overlap.
    If there is an overlap, the intersection of the sets will return a date, which
    is evaluated into True, indicating a conflict. An empty set (no conflict) will
    return False
    """
    query_booking_occupancy_dates = get_occupancy_dates(
        query_booking.check_in_date, query_booking.number_of_nights
    )
    new_booking_occupancy_dates = get_occupancy_dates(
        new_booking.check_in_date, new_booking.number_of_nights
    )

    # If there are no overlapping/conflicting dates, intersection will return false
    return bool(new_booking_occupancy_dates & query_booking_occupancy_dates)


def is_booking_possible(db: Session, booking: schemas.BookingBase) -> Tuple[bool, str]:
    """
    Checks for conflicts with users, units, and dates. If no conflicts are found
    returns True and "OK", otherwise returns False with a specific error message
    """

    # check 1 : The Same guest cannot book the same unit multiple times, on the same dates
    same_guest_same_unit_booking = (
        db.query(models.Booking)
        .filter_by(guest_name=booking.guest_name, unit_id=booking.unit_id)
        .first()
    )
    # If a booking is found, check for conflicts, return error if True
    if same_guest_same_unit_booking is not None and check_conflicting_occupancy_dates(
        same_guest_same_unit_booking, booking
    ):
        return (
            False,
            "The given guest name cannot book the same unit multiple times",
        )

    # check 2 : the same guest cannot be in multiple units at the same time
    same_guest_multiple_unit_booking = (
        db.query(models.Booking).filter_by(guest_name=booking.guest_name).first()
    )
    # If a booking is found, check for conflicts, return error if True
    if (
        same_guest_multiple_unit_booking is not None
        and check_conflicting_occupancy_dates(same_guest_multiple_unit_booking, booking)
    ):
        return False, "The same guest cannot be in multiple units at the same time"

    # check 3 : Unit is available for the check-in date
    most_recent_unit_booking = (
        db.query(models.Booking).filter_by(unit_id=booking.unit_id).first()
    )
    # If a booking is found, check for conflicts, return error if True
    if most_recent_unit_booking is not None and check_conflicting_occupancy_dates(
        most_recent_unit_booking, booking
    ):
        return False, "For the given check-in date, the unit is already occupied"

    return True, "OK"
