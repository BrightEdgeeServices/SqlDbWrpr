import pytest
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column

from sqldbwrpr.sqldbwrpr import SchemaSourceError
from sqldbwrpr.sqldbwrpr import SQLDbWrpr


class TestSqlDbWrprSchemaResolution:
    def test_resolve_db_structure_prefers_explicit_structure(self):
        explicit_structure = {
            "ExplicitTable": {
                "ExplicitField": {
                    "Type": ["int"],
                    "Params": SQLDbWrpr._build_default_field_params(),
                    "Possible Values": "",
                    "Comment": "",
                }
            }
        }
        metadata = MetaData()
        Table("metadata_table", metadata, Column("id", Integer, primary_key=True))

        result = SQLDbWrpr.resolve_db_structure(
            p_db_structure=explicit_structure,
            p_sqlalchemy_metadata=metadata,
        )

        assert result is explicit_structure

    def test_resolve_db_structure_raises_without_schema_source(self):
        with pytest.raises(SchemaSourceError, match="Supply p_db_structure"):
            SQLDbWrpr.resolve_db_structure()

    def test_resolve_db_structure_uses_declarative_base_metadata(self):
        class Base(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"

            id = mapped_column(Integer, primary_key=True)
            name = mapped_column(String(30), nullable=False)

        result = SQLDbWrpr.resolve_db_structure(p_sqlalchemy_base=Base)

        assert result["user"]["id"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert result["user"]["name"]["Type"] == ["varchar", 30]
        assert result["user"]["name"]["Params"]["NN"] == "Y"

    def test_resolve_db_structure_uses_sqlalchemy_metadata(self):
        metadata = MetaData()
        country = Table(
            "country",
            metadata,
            Column("code", String(3), primary_key=True, comment="Country code"),
            Column("description", String(30)),
        )
        member = Table(
            "member",
            metadata,
            Column("id", Integer, primary_key=True),
            Column(
                "country_code",
                String(3),
                ForeignKey(country.c.code, ondelete="CASCADE", onupdate="RESTRICT"),
                nullable=False,
            ),
            Column("name", String(30), nullable=False),
            Column("joined_at", DateTime),
            Column("fee", Numeric(5, 2)),
        )
        Index("idx_member_name", member.c.name, unique=True)

        result = SQLDbWrpr.resolve_db_structure(p_sqlalchemy_metadata=metadata)

        assert list(result) == ["country", "member"]
        assert result["country"]["code"]["Comment"] == "Country code"
        assert result["country"]["code"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert result["member"]["country_code"]["Params"]["FKey"] == [1, 1, "country", "code", "C", "R"]
        assert result["member"]["name"]["Params"]["Index"] == [1, 1, "A", "U"]
        assert result["member"]["joined_at"]["Type"] == ["datetime"]
        assert result["member"]["fee"]["Type"] == ["decimal", 5, 2]
