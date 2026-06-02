import dataclasses
import json
import re
from configparser import ConfigParser
from dataclasses import dataclass, field, fields, is_dataclass, MISSING, Field, dataclass, field
from typing import Any, Optional, dataclass_transform, get_type_hints

import pytest

from npg.conf import IniData

#
# Misc
#

def url(*items):
    return "/".join(items)

#
# Current
#
# ❌ Have to remember to use field(repr=False)
# ❌ By default, fields are printable
#

@dataclass
class ConfigWithSecret:
    secret_repr_false: str = field(repr=False)
    secret_no_rep: str
    key1: str

def test_current():
    config = ConfigWithSecret("secret_repr_false", "secret_no_repr", "key1")
    assert "secret_no_repr" in str(config)
    assert "secret_no_repr" in repr(config)
    assert "secret_repr_false" in str(dataclasses.asdict(config)), "Limitation"
    assert "secret_repr_false" in str(config.__dict__), "Limitation"
    # assert "secret_repr_false" in json.dumps(config)

#
# Secret class
#
# ✅ Explicit
# ❌ Have to remember to use Secret
# ❌ By default, fields are printable
#

class Secret:
    def __init__(self, value: str):
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Secret('********')"

    __str__ = __repr__

class SecretIniData(IniData):
    def parse_ini_value(self, parser: ConfigParser, section: str, _field, hint) -> Any:
        if hint is Secret:
            return Secret(parser.get(section, _field.name))

        return super().parse_ini_value(parser, section, _field, hint)

    def parse_environment_value(self, val: str, hint) -> Any:
        if hint is Secret:
            return Secret(val)

        return super().parse_environment_value(val, hint)

@dataclass
class DbConfigSecret:
    dbhost: str
    dbport: str
    dbuser: str
    dbname: str
    dbpass: Secret

    @property
    def url(self):
        return url(
            "mysql+pymysql",
            self.dbuser,
            self.dbpass.get_secret_value(),
            self.dbhost,
            int(self.dbport),
            self.dbname
        )

def test_secret(tmp_path):
    config = DbConfigSecret("host", "1", "user", "name", Secret("password"))
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass.get_secret_value() == "password"
    assert "password" not in str(dataclasses.asdict(config))
    assert "password" not in str(config.__dict__)
    # assert "password" not in json.dumps(config)

    ini_file = tmp_path / "config.ini"
    section = "db"
    ini_file.write_text(f"[{section}]\ndbhost=host\ndbport=1\ndbuser=user\ndbname=name\ndbpass=password\n")
    parser = SecretIniData(DbConfigSecret)
    config = parser.from_file(ini_file, section)
    assert "host" in str(config)
    assert "host" in repr(config)
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass.get_secret_value() == "password"

#
# dataclass_with_repr_false_secrets
#
# ✅ Secures existing usage without config
# ❌ Heuristic
#

SECRET_NAMES = {"password", "passwd", "dbpass", "token", "secret", "api_key"}

@dataclass_transform()
def dataclass_with_repr_false_secrets(cls=None, **kwargs):
    def wrap(c):
        annotations = getattr(c, "__annotations__", {})
        for name in annotations:
            if name.lower() in SECRET_NAMES and not hasattr(c, name):
                setattr(c, name, field(repr=False))
        return dataclass(c, **kwargs)

    return wrap(cls) if cls else wrap

@dataclass_with_repr_false_secrets
class DbConfigReprFalseSecrets:
    dbhost: str
    dbport: str
    dbuser: str
    dbname: str
    dbpass: str

    @property
    def url(self):
        return url(
            "mysql+pymysql",
            self.dbuser,
            self.dbpass,
            self.dbhost,
            int(self.dbport),
            self.dbname
        )

def test_repr_false_secrets(tmp_path):
    config = DbConfigReprFalseSecrets("host", "1", "user", "name", "password")
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass == "password"
    assert "password" in str(dataclasses.asdict(config)), "Limitation"
    assert "password" in str(config.__dict__), "Limitation"
    # assert "password" not in json.dumps(config)

    ini_file = tmp_path / "config.ini"
    section = "db"
    ini_file.write_text(f"[{section}]\ndbhost=host\ndbport=1\ndbuser=user\ndbname=name\ndbpass=password\n")
    parser = IniData(DbConfigReprFalseSecrets)
    config = parser.from_file(ini_file, section)
    assert "host" in str(config)
    assert "host" in repr(config)
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass == "password"

#
# dataclass_with_repr_false_default
#
# ✅ Secures existing usage without config
# ❌ Need to maintain field mapping
# ❌ Need to explicitly mark fields as printable
# ❌ Need to remember to use custom dataclass
#

@dataclass_transform(field_specifiers=(field,))
def dataclass_with_repr_false_default(cls=None, **dataclass_kwargs):
    def wrap(c):
        annotations = getattr(c, "__annotations__", {})

        for name in annotations:
            value = c.__dict__.get(name, MISSING)

            # No field() specified
            if value is MISSING:
                setattr(c, name, field(repr=False))

            # Existing dataclass field
            elif isinstance(value, Field):
                if value.repr is not True:
                    setattr(
                        c,
                        name,
                        field(
                            default=value.default,
                            init=value.init,
                            repr=False,
                            hash=value.hash,
                            compare=value.compare,
                            metadata=value.metadata,
                            kw_only=value.kw_only,
                        ),
                        # ❌ Need to maintain this
                    )

        # Could set frozen=True,slots=True
        return dataclass(**dataclass_kwargs)(c)

    return wrap if cls is None else wrap(cls)

@dataclass_with_repr_false_default
class DbConfigReprFalseDefault:
    dbhost: str = field(repr=True)
    dbport: str
    dbuser: str = field(repr=False)
    dbname: str
    dbpass: str
    no_type = "no_type" # Not included in dataclass fields

    @property
    def url(self):
        return url(
            "mysql+pymysql",
            self.dbuser,
            self.dbpass,
            self.dbhost,
            int(self.dbport),
            self.dbname,
            self.no_type
        )

def test_repr_false_default(tmp_path):
    with pytest.raises(TypeError, match=re.escape("DbConfigReprFalseDefault.__init__() takes 6 positional arguments but 7 were given")
                       ):
        config = DbConfigReprFalseDefault("host", "1", "user", "name", "password", "no_type")
    config = DbConfigReprFalseDefault("host", "1", "user", "name", "password")
    assert "host" in str(config)
    assert "host" in repr(config)
    assert "port" not in str(config)
    assert "port" not in repr(config)
    assert "user" not in str(config)
    assert "user" not in repr(config)
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass == "password"
    assert "no_type" not in str(config)
    assert "no_type" not in repr(config)
    assert "password" in str(dataclasses.asdict(config)), "Limitation"
    assert "password" in str(config.__dict__), "Limitation"
    # assert "password" not in json.dumps(config)

    ini_file = tmp_path / "config.ini"
    section = "db"
    ini_file.write_text(f"[{section}]\ndbhost=host\ndbport=1\ndbuser=user\ndbname=name\ndbpass=password\nno_type=no_type\n")
    parser = IniData(DbConfigReprFalseDefault)
    config = parser.from_file(ini_file, section)
    assert "host" in str(config)
    assert "host" in repr(config)
    assert "port" not in str(config)
    assert "port" not in repr(config)
    assert "user" not in str(config)
    assert "user" not in repr(config)
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass == "password"
    assert "no_type" not in str(config)
    assert "no_type" not in repr(config)

#
# Third party
# pydantic SecretStr
#
# ❌ Have to remember to use SecretStr
#

from pydantic import BaseModel, SecretStr

class DbConfigPydantic(BaseModel):
    dbhost: str
    dbport: str
    dbuser: str
    dbname: str
    dbpass: SecretStr

    @property
    def url(self):
        return url(
            "mysql+pymysql",
            self.dbuser,
            self.dbpass.get_secret_value(),
            self.dbhost,
            int(self.dbport),
            self.dbname
        )

def test_pydantic(tmp_path):
    config = DbConfigPydantic(dbhost="host", dbport="1", dbuser="user", dbname="name", dbpass=SecretStr("password"))
    assert "host" in str(config)
    assert "host" in repr(config)
    assert "password" not in str(config)
    assert "password" not in repr(config)
    assert config.dbpass.get_secret_value() == "password"
    assert "no_type" not in str(config)
    assert "no_type" not in repr(config)
    assert "password" not in config.__dict__
    # assert "password" not in json.dumps(config)
    assert "password" not in str(config.model_dump())

#
# frozen=True
#

@dataclass
class ConfigNotFrozen:
    secret: str

def test_not_frozen():
    config = ConfigNotFrozen(secret="secret")
    config.another_secret = "secret"

@dataclass(frozen=True)
class ConfigFrozen:
    secret: str

def test_frozen():
    config = ConfigFrozen(secret="secret")
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.another_secret = "secret"
    config.__dict__["another_secret"] = "secret"
    assert config.another_secret == "secret"

#
# frozen=True,slots=True
#
# ✅ Protects against new secrets being added
# Whilst a good default, seems very much a corner case!
#

@dataclass(frozen=True, slots=True)
class ConfigSlots:
    secret: str

def test_slots():
    config = ConfigSlots(secret="secret")
    with pytest.raises(TypeError):
        config.another_secret = "secret"
    with pytest.raises(AttributeError):
        config.__dict__["another_secret"] = "secret"
    assert not hasattr(config, "another_secret")