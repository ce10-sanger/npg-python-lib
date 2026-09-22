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
import json
from pathlib import Path

import structlog
from pytest import CaptureFixture
from pytest import mark as m

from npg.log import configure_structlog


@m.describe("configure_structlog")
class TestConfigureStructlog:
    @m.context("When configuring with default options")
    @m.it("Logs to stderr")
    def test_normal_defaults(self, capsys: CaptureFixture):
        # Act
        configure_structlog()
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        stderr = capsys.readouterr().err
        assert "Test Message" in stderr
        assert not "CRITICAL" in stderr

    @m.context("When configuring with config file specifying logging to file")
    @m.it("Logs to file")
    def test_normal_config_file(self, capsys: CaptureFixture, tmp_path: Path):
        # Arrange
        config_file = tmp_path / "logging.json"
        log_path = tmp_path / "test.log"
        config_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "disable_existing_loggers": False,
                    "loggers": {
                        "root": {
                            "level": "INFO",
                            "handlers": [
                                "file",
                            ],
                        }
                    },
                    "handlers": {
                        "file": {
                            "class": "logging.FileHandler",
                            "level": "INFO",
                            "formatter": "simple",
                            "filename": str(log_path),
                            "mode": "a",
                        }
                    },
                    "formatters": {"simple": {"format": "%(message)s"}},
                }
            )
        )

        # Act
        configure_structlog(config_file)
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        stderr = capsys.readouterr().err
        assert "Test Message" not in stderr
        assert "Test Message" in log_path.read_text()
        assert "CRITICAL" not in stderr
        assert "CRITICAL" not in log_path.read_text()

    @m.context("When configuring with missing config file")
    @m.it("Falls back to default log to stderr behaviour")
    @m.it("and logs a CRITICAL error to stderr")
    def test_error(self, capsys: CaptureFixture):
        # Act
        configure_structlog("missing-logging.json")
        log = structlog.stdlib.get_logger()
        log.error("Test Message")

        # Assert
        stderr = capsys.readouterr().err
        assert "Test Message" in stderr
        assert "CRITICAL" in stderr
