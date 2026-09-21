# -*- coding: utf-8 -*-
#
# Copyright © 2026 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import structlog
from pytest import LogCaptureFixture, CaptureFixture
from pytest import mark as m

from npg.log import configure_structlog


@m.describe("TODO")
class TestTODO:
    def test_todo(self, caplog: LogCaptureFixture, capsys: CaptureFixture):
        # Act
        configure_structlog("missing.conf")
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        assert "CRITICAL" in capsys.readouterr().err
        assert "Test Message" in capsys.readouterr().err
        assert "Test Message" in caplog.text
