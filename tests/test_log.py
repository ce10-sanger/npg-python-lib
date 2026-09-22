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
from pathlib import Path

import structlog
from pytest import LogCaptureFixture, CaptureFixture
from pytest import mark as m

from npg.log import configure_structlog


@m.describe("configure_structlog")
class TestConfigureStructlog:
    def test_normal_defaults(self, caplog: LogCaptureFixture, capsys: CaptureFixture):
        # Act
        configure_structlog()
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        assert "Test Message" in capsys.readouterr().err
        assert "Test Message" in caplog.text

        assert not "CRITICAL" in capsys.readouterr().err
        assert not "CRITICAL" in caplog.text

    def test_normal_config_file(
        self, caplog: LogCaptureFixture, capsys: CaptureFixture, tmp_path: Path
    ):
        # Arrange
        config_file = tmp_path / "logging.json"
        log_path = tmp_path / "test.log"
        config_file.write_text(
            """
{
    "version": 1,
    "disable_existing_loggers": false,
    "loggers": {
        "root": {
            "level": "INFO",
            "handlers": [
                "file",
            ]
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": """" + str(%s) + """",
            "mode": "a"
        }
    },
    "formatters": {
        "simple": {
            "format": "%(message)s"
        }
    }
}        
"""
        )

        # Act
        configure_structlog(config_file)
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        assert "Test Message" not in capsys.readouterr().err
        assert "Test Message" in caplog.text
        assert "Test Message" in log_path.read_text()

        assert "CRITICAL" not in caplog.text
        assert "CRITICAL" not in log_path.read_text()

    def test_error(self, caplog: LogCaptureFixture, capsys: CaptureFixture):
        # Act
        configure_structlog("missing-logging.json")
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        assert "Test Message" in capsys.readouterr().err
        assert "Test Message" in caplog.text

        assert "CRITICAL" in capsys.readouterr().err
        assert "CRITICAL" in caplog.text
