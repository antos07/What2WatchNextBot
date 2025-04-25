import datetime

import freezegun

from app.core.models import User
from app.testing.constants import RANDOM_DATETIME


class TestUser:
    def test_created_at_defaults_to_current_timestamp(self):
        with freezegun.freeze_time(RANDOM_DATETIME):
            user = User(id=1, first_name="test")

        assert user.created_at == RANDOM_DATETIME

    def test_last_activity_at_defaults_to_current_timestamp(
        self, freezer: freezegun.api.FrozenDateTimeFactory
    ):
        freezer.move_to(RANDOM_DATETIME)

        user = User(id=1, first_name="test")
        assert user.last_activity_at == RANDOM_DATETIME

    def test_update_last_activity(self, freezer: freezegun.api.FrozenDateTimeFactory):
        user = User(id=1, first_name="test", last_activity_at=RANDOM_DATETIME)
        new_activity_at = RANDOM_DATETIME + datetime.timedelta(days=1)
        freezer.move_to(new_activity_at)

        user.update_last_activity()

        assert user.last_activity_at == new_activity_at
