import datetime
from typing import Set, Tuple

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


def get_occupancy_dates(check_in_date: datetime.date, nights: int) -> Set[str]:
    return set(
        (check_in_date + datetime.timedelta(days=night)).strftime("%Y-%m-%d")
        for night in range(0, nights)
    )


def is_booking_possible(db: Session, booking: schemas.BookingBase) -> Tuple[bool, str]:
    new_booking_occupancy_dates = get_occupancy_dates(
        booking.check_in_date, booking.number_of_nights
    )
    # check 1 : The Same guest cannot book the same unit multiple times, on the same dates
    same_guest_booking = (
        db.query(models.Booking)
        .filter_by(guest_name=booking.guest_name, unit_id=booking.unit_id)
        .first()
    )
    # Do check only if booking found
    if same_guest_booking is not None:
        same_guest_booking_occupancy_dates = get_occupancy_dates(
            same_guest_booking.check_in_date, same_guest_booking.number_of_nights
        )

        # If there are no overlapping dates, will return "falsy" empty set
        is_same_guest_booking_same_unit_same_dates = (
            new_booking_occupancy_dates & same_guest_booking_occupancy_dates
        )

        if is_same_guest_booking_same_unit_same_dates:
            return (
                False,
                "The given guest name cannot book the same unit multiple times",
            )

    # check 2 : the same guest cannot be in multiple units at the same time
    same_guest_same_unit_booking = (
        db.query(models.Booking).filter_by(guest_name=booking.guest_name).first()
    )
    # Do check only if booking found
    if same_guest_same_unit_booking is not None:
        same_guest_same_unit_booking_occupancy_dates = get_occupancy_dates(
            same_guest_same_unit_booking.check_in_date,
            same_guest_same_unit_booking.number_of_nights,
        )

        is_same_guest_already_booked_same_dates = (
            new_booking_occupancy_dates & same_guest_same_unit_booking_occupancy_dates
        )
        if is_same_guest_already_booked_same_dates:
            return False, "The same guest cannot be in multiple units at the same time"

    # check 3 : Unit is available for the check-in date
    most_recent_unit_booking = (
        db.query(models.Booking).filter_by(unit_id=booking.unit_id).first()
    )

    # Do check only if query found
    if most_recent_unit_booking is not None:
        most_recent_unit_booking_occupancy_dates = get_occupancy_dates(
            most_recent_unit_booking.check_in_date,
            most_recent_unit_booking.number_of_nights,
        )

        is_unit_unavailable_on_overlapping_dates = (
            new_booking_occupancy_dates & most_recent_unit_booking_occupancy_dates
        )
        if is_unit_unavailable_on_overlapping_dates:
            return False, "For the given check-in date, the unit is already occupied"

    return True, "OK"
