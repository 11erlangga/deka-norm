from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String(50), primary_key=True)
    year = Column(SmallInteger, nullable=False)
    category = Column(String(100), nullable=False)
    sub_category = Column(String(100))
    detail_product = Column(String(100))
    test_type = Column(String(50))
    methodology = Column(String(50))
    sub_method = Column(String(50))
    notes = Column(Text)


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    respondent_id = Column(String(50), nullable=False)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False)
    segment = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    actual_age = Column(SmallInteger, nullable=True)
    ses = Column(String(20), nullable=True)
    occupation = Column(String(225), nullable=True)
    variable_name = Column(String(150), nullable=False)
    scale_max = Column(SmallInteger, nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    score_normalized = Column(Numeric(7, 4))
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "respondent_id",
            "project_id",
            "segment",
            "variable_name",
            name="uq_response",
        ),
    )


def init_db(engine):
    Base.metadata.create_all(engine)
    print("Tables created.")
