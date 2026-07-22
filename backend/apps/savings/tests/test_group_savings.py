from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.destinations.models import Country, Destination
from apps.savings.models import SavingEntry
from apps.trips.models import Trip, TripMember
from apps.users.models import User


@pytest.fixture
def destination(db):
    country = Country.objects.create(
        name_uz="Gruziya", name_en="Georgia", code="GE", visa_type="free", visa_cost_usd=0
    )
    return Destination.objects.create(country=country, city_uz="Tbilisi", city_en="Tbilisi")


def _user(phone, **overrides):
    return User.objects.create_user(phone=phone, full_name="User " + phone[-4:], password="testpass123", **overrides)


def _trip(owner, destination):
    return Trip.objects.create(
        user=owner,
        destination=destination,
        start_date=date.today() + timedelta(days=30),
        duration_days=5,
        budget_min=Decimal("400"),
        budget_max=Decimal("600"),
        target_amount=Decimal("500"),
        status=Trip.Status.SAVING,
    )


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestAddMember:
    def test_owner_can_add_member_by_phone(self, destination):
        owner = _user("+998900000101")
        friend = _user("+998900000102")
        trip = _trip(owner, destination)

        res = _client_for(owner).post(f"/api/v1/trips/{trip.id}/members/", {"phone": friend.phone}, format="json")

        assert res.status_code == 201
        assert TripMember.objects.filter(trip=trip, user=friend).exists()

    def test_cannot_add_unknown_phone(self, destination):
        owner = _user("+998900000103")
        trip = _trip(owner, destination)

        res = _client_for(owner).post(f"/api/v1/trips/{trip.id}/members/", {"phone": "+998900000199"}, format="json")

        assert res.status_code == 404

    def test_cannot_add_self(self, destination):
        owner = _user("+998900000104")
        trip = _trip(owner, destination)

        res = _client_for(owner).post(f"/api/v1/trips/{trip.id}/members/", {"phone": owner.phone}, format="json")

        assert res.status_code == 400

    def test_cannot_add_same_member_twice(self, destination):
        owner = _user("+998900000105")
        friend = _user("+998900000106")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=friend)

        res = _client_for(owner).post(f"/api/v1/trips/{trip.id}/members/", {"phone": friend.phone}, format="json")

        assert res.status_code == 400

    def test_non_owner_cannot_add_members(self, destination):
        owner = _user("+998900000107")
        outsider = _user("+998900000108")
        target = _user("+998900000109")
        trip = _trip(owner, destination)

        res = _client_for(outsider).post(f"/api/v1/trips/{trip.id}/members/", {"phone": target.phone}, format="json")

        assert res.status_code == 404


@pytest.mark.django_db
class TestMemberAccess:
    def test_member_can_view_trip_detail(self, destination):
        owner = _user("+998900000110")
        member = _user("+998900000111")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)

        res = _client_for(member).get(f"/api/v1/trips/{trip.id}/")

        assert res.status_code == 200

    def test_non_member_cannot_view_trip_detail(self, destination):
        owner = _user("+998900000112")
        outsider = _user("+998900000113")
        trip = _trip(owner, destination)

        res = _client_for(outsider).get(f"/api/v1/trips/{trip.id}/")

        assert res.status_code == 404

    def test_member_cannot_edit_trip(self, destination):
        owner = _user("+998900000114")
        member = _user("+998900000115")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)

        res = _client_for(member).patch(f"/api/v1/trips/{trip.id}/", {"target_amount": "999"}, format="json")

        assert res.status_code == 404

    def test_member_cannot_delete_trip(self, destination):
        owner = _user("+998900000116")
        member = _user("+998900000117")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)

        res = _client_for(member).delete(f"/api/v1/trips/{trip.id}/")

        assert res.status_code == 404
        assert Trip.objects.filter(id=trip.id).exists()


@pytest.mark.django_db
class TestGroupSavingEntries:
    def test_owner_and_member_can_each_save_on_the_same_day(self, destination):
        owner = _user("+998900000118")
        member = _user("+998900000119")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        today = date.today().isoformat()

        r1 = _client_for(owner).post(
            f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": today}, format="json"
        )
        r2 = _client_for(member).post(
            f"/api/v1/trips/{trip.id}/savings/", {"amount": "15", "date": today}, format="json"
        )

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert SavingEntry.objects.filter(trip=trip, date=date.today()).count() == 2

    def test_resubmitting_same_day_updates_only_own_entry(self, destination):
        owner = _user("+998900000120")
        member = _user("+998900000121")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        today = date.today().isoformat()

        _client_for(owner).post(f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": today}, format="json")
        _client_for(member).post(f"/api/v1/trips/{trip.id}/savings/", {"amount": "15", "date": today}, format="json")
        _client_for(member).post(f"/api/v1/trips/{trip.id}/savings/", {"amount": "20", "date": today}, format="json")

        assert SavingEntry.objects.filter(trip=trip, date=date.today()).count() == 2
        owner_entry = SavingEntry.objects.get(trip=trip, user=owner)
        member_entry = SavingEntry.objects.get(trip=trip, user=member)
        assert owner_entry.amount == Decimal("10")
        assert member_entry.amount == Decimal("20")

    def test_non_member_cannot_add_saving_entry(self, destination):
        owner = _user("+998900000122")
        outsider = _user("+998900000123")
        trip = _trip(owner, destination)

        res = _client_for(outsider).post(
            f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": date.today().isoformat()}, format="json"
        )

        assert res.status_code == 404

    def test_stats_aggregate_across_members(self, destination):
        owner = _user("+998900000124")
        member = _user("+998900000125")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        today = date.today().isoformat()
        _client_for(owner).post(f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": today}, format="json")
        _client_for(member).post(f"/api/v1/trips/{trip.id}/savings/", {"amount": "15", "date": today}, format="json")

        res = _client_for(owner).get(f"/api/v1/trips/{trip.id}/savings/stats/")

        assert res.status_code == 200
        today_entry = next(w for w in res.data["data"]["weekly"] if w["date"] == date.today().isoformat())
        assert Decimal(str(today_entry["amount"])) == Decimal("25")

    def test_member_can_only_delete_own_entry(self, destination):
        owner = _user("+998900000126")
        member = _user("+998900000127")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        owner_entry = SavingEntry.objects.create(trip=trip, user=owner, amount=Decimal("10"), date=date.today())

        res = _client_for(member).delete(f"/api/v1/savings/{owner_entry.id}/")

        assert res.status_code == 404
        assert SavingEntry.objects.filter(id=owner_entry.id).exists()

    def test_owner_can_delete_members_entry(self, destination):
        owner = _user("+998900000128")
        member = _user("+998900000129")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        member_entry = SavingEntry.objects.create(trip=trip, user=member, amount=Decimal("10"), date=date.today())

        res = _client_for(owner).delete(f"/api/v1/savings/{member_entry.id}/")

        assert res.status_code == 204


@pytest.mark.django_db
class TestCancelledTripBlocksNewSavings:
    def test_cannot_add_entry_to_cancelled_trip(self, destination):
        owner = _user("+998900000140")
        trip = _trip(owner, destination)
        trip.status = Trip.Status.CANCELLED
        trip.save(update_fields=["status"])

        res = _client_for(owner).post(
            f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": date.today().isoformat()}, format="json"
        )

        assert res.status_code == 400
        assert not SavingEntry.objects.filter(trip=trip).exists()

    def test_cannot_add_entry_to_completed_trip(self, destination):
        owner = _user("+998900000141")
        trip = _trip(owner, destination)
        trip.status = Trip.Status.COMPLETED
        trip.save(update_fields=["status"])

        res = _client_for(owner).post(
            f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": date.today().isoformat()}, format="json"
        )

        assert res.status_code == 400

    def test_restoring_a_cancelled_trip_allows_saving_again(self, destination):
        owner = _user("+998900000142")
        trip = _trip(owner, destination)
        trip.status = Trip.Status.CANCELLED
        trip.save(update_fields=["status"])
        client = _client_for(owner)

        restore_res = client.patch(f"/api/v1/trips/{trip.id}/", {"status": "planning"}, format="json")
        assert restore_res.status_code == 200

        add_res = client.post(
            f"/api/v1/trips/{trip.id}/savings/", {"amount": "10", "date": date.today().isoformat()}, format="json"
        )
        assert add_res.status_code == 201


@pytest.mark.django_db
class TestTripMembersListAndRemove:
    def test_members_endpoint_lists_owner_and_members_with_totals(self, destination):
        owner = _user("+998900000130")
        member = _user("+998900000131")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        SavingEntry.objects.create(trip=trip, user=owner, amount=Decimal("30"), date=date.today())
        SavingEntry.objects.create(trip=trip, user=member, amount=Decimal("20"), date=date.today() - timedelta(days=1))

        res = _client_for(member).get(f"/api/v1/trips/{trip.id}/members/")

        assert res.status_code == 200
        by_id = {row["id"]: row for row in res.data["data"]}
        assert Decimal(str(by_id[owner.id]["total_saved"])) == Decimal("30")
        assert Decimal(str(by_id[member.id]["total_saved"])) == Decimal("20")
        assert by_id[owner.id]["is_owner"] is True
        assert by_id[member.id]["is_owner"] is False

    def test_owner_can_remove_member(self, destination):
        owner = _user("+998900000132")
        member = _user("+998900000133")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)

        res = _client_for(owner).delete(f"/api/v1/trips/{trip.id}/members/{member.id}/")

        assert res.status_code == 200
        assert not TripMember.objects.filter(trip=trip, user=member).exists()

    def test_removed_member_loses_access(self, destination):
        owner = _user("+998900000134")
        member = _user("+998900000135")
        trip = _trip(owner, destination)
        TripMember.objects.create(trip=trip, user=member)
        TripMember.objects.filter(trip=trip, user=member).delete()

        res = _client_for(member).get(f"/api/v1/trips/{trip.id}/")

        assert res.status_code == 404


@pytest.mark.django_db
class TestSharedTripsEndpoint:
    def test_returns_only_trips_where_user_is_a_member_not_owner(self, destination):
        owner = _user("+998900000136")
        member = _user("+998900000137")
        owned_trip = _trip(owner, destination)
        shared_trip = _trip(owner, destination)
        TripMember.objects.create(trip=shared_trip, user=member)

        res = _client_for(member).get("/api/v1/trips/shared/")

        assert res.status_code == 200
        ids = [t["id"] for t in res.data["data"]]
        assert shared_trip.id in ids
        assert owned_trip.id not in ids
