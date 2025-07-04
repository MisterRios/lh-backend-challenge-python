import datetime

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
with freeze_time("2023-05-21"):
    GUEST_A_UNIT_1: dict = {
        "unit_id": "1",
        "guest_name": "GuestA",
        "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
        "number_of_nights": 5,
    }
    GUEST_A_UNIT_2: dict = {
        "unit_id": "2",
        "guest_name": "GuestA",
        "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
        "number_of_nights": 5,
    }
    GUEST_B_UNIT_1: dict = {
        "unit_id": "1",
        "guest_name": "GuestB",
        "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
        "number_of_nights": 5,
    }
    GUEST_A_UNIT_1_TEN_NIGHTS: dict = {
        "unit_id": "1",
        "guest_name": "GuestA",
        "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
        "number_of_nights": 10,
    }
    GUEST_A_UNIT_2_TEN_NIGHTS: dict = {
        "unit_id": "2",
        "guest_name": "GuestA",
        "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
        "number_of_nights": 10,
    }
    GUEST_B_UNIT_1_TEN_NIGHTS: dict = {
        "unit_id": "1",
        "guest_name": "GuestB",
        "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
        "number_of_nights": 10,
    }


@pytest.fixture()
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.mark.freeze_time("2023-05-21")
def test_create_fresh_booking(test_db):
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    response.raise_for_status()
    assert response.status_code == 200, response.text


@pytest.mark.freeze_time("2023-05-21")
def test_same_guest_same_unit_booking(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text
    response.raise_for_status()

    # Guests want to book same unit again
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "The given guest name cannot book the same unit multiple times"
    )


@pytest.mark.freeze_time("2023-05-21")
def test_same_guest_different_unit_booking(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Guest wants to book another unit
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_2)
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "The same guest cannot be in multiple units at the same time"
    )


@pytest.mark.freeze_time("2023-05-21")
def test_same_guest_same_unit_booking_different_date(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text
    response.raise_for_status()

    # Guests want to book same unit again, ten days later
    response = client.post(
        "/api/v1/booking",
        json={
            "unit_id": "1",  # same unit
            "guest_name": "GuestA",  # different guest
            # check_in date of GUEST A + 10, the unit is free on this date
            "check_in_date": (datetime.date.today() + datetime.timedelta(10)).strftime(
                "%Y-%m-%d"
            ),
            "number_of_nights": 5,
        },
    )
    assert response.status_code == 200, response.text
    response.raise_for_status()


@pytest.mark.freeze_time("2023-05-21")
def test_different_guest_same_unit_booking(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # GuestB trying to book a unit that is already occupied
    response = client.post("/api/v1/booking", json=GUEST_B_UNIT_1)
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "For the given check-in date, the unit is already occupied"
    )


@pytest.mark.freeze_time("2023-05-21")
def test_different_guest_same_unit_booking_different_date_occupied(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # GuestB trying to book a unit that is already occupied
    response = client.post(
        "/api/v1/booking",
        json={
            "unit_id": "1",  # same unit
            "guest_name": "GuestB",  # different guest
            # check_in date of GUEST A + 1, the unit is already booked on this date
            # trying to check in tomorrow
            "check_in_date": (datetime.date.today() + datetime.timedelta(1)).strftime(
                "%Y-%m-%d"
            ),
            "number_of_nights": 5,
        },
    )
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "For the given check-in date, the unit is already occupied"
    )


@pytest.mark.freeze_time("2023-05-21")
def test_different_guest_same_unit_booking_different_date_unoccupied(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # GuestB trying to book a unit that is no longer occupied ten days later
    response = client.post(
        "/api/v1/booking",
        json={
            "unit_id": "1",  # same unit
            "guest_name": "GuestB",  # different guest
            # check_in date of GUEST A + 1, the unit is already booked on this date
            "check_in_date": (datetime.date.today() + datetime.timedelta(10)).strftime(
                "%Y-%m-%d"
            ),
            "number_of_nights": 5,
        },
    )
    assert response.status_code == 200, response.text
    response.raise_for_status()


@pytest.mark.freeze_time("2023-05-21")
def test_extend_booking_successful(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text


@pytest.mark.freeze_time("2023-05-21")
def test_extend_booking__no_booking__different_checkin_date(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Guests want to extend same unit
    response = client.post("/api/v1/booking/extend", json=GUEST_A_UNIT_1_TEN_NIGHTS)
    assert response.status_code == 200, response.text
    response.raise_for_status()

    response_json = response.json()
    assert response_json["unit_id"] == GUEST_A_UNIT_1_TEN_NIGHTS["unit_id"]
    assert response_json["guest_name"] == GUEST_A_UNIT_1_TEN_NIGHTS["guest_name"]
    assert response_json["check_in_date"] == GUEST_A_UNIT_1_TEN_NIGHTS["check_in_date"]
    assert (
        response_json["number_of_nights"]
        == GUEST_A_UNIT_1_TEN_NIGHTS["number_of_nights"]
    )


@pytest.mark.freeze_time("2023-05-21")
def test_extend_booking__no_booking__different_guest(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Different guest wants to extend same unit
    response = client.post("/api/v1/booking/extend", json=GUEST_B_UNIT_1_TEN_NIGHTS)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Unable to find current booking"


@pytest.mark.freeze_time("2023-05-21")
def test_extend_booking__no_booking__different_unit(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Different guest wants to extend same unit
    response = client.post("/api/v1/booking/extend", json=GUEST_A_UNIT_2_TEN_NIGHTS)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Unable to find current booking"


@pytest.mark.freeze_time("2023-05-21")
def test_extend_booking_too_few_nights(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Extend booking with too few nights
    response = client.post(
        "/api/v1/booking/extend",
        json={
            "unit_id": "1",  # same unit
            "guest_name": "GuestA",  # same guest
            "check_in_date": datetime.date.today().strftime(
                "%Y-%m-%d"
            ),  # same check_in_date
            # too few nights to extend
            "number_of_nights": 4,
        },
    )
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "Number of nights to extend is fewer than current number of nights"
    )


@pytest.mark.freeze_time("2023-05-21")
def test_extend_booking_same_number_of_nights(test_db):
    # Create first booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Different guest wants to extend same unit
    response = client.post("/api/v1/booking/extend", json=GUEST_A_UNIT_1)
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "Number of nights to extend is fewer than current number of nights"
    )
