from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    class_code = Column(String(20), unique=True, nullable=False)
    class_name = Column(String(100), nullable=False)
    max_students = Column(Integer, nullable=False, default=30)
    status = Column(String(20), nullable=False, default="active")

    students = relationship(
        "Student",
        back_populates="classroom"
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    full_name = Column(String(100), nullable=False)
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    age = Column(Integer, nullable=False)
    gender = Column(
        Enum("male", "female", "other"),
        nullable=False
    )

    class_id = Column(
        Integer,
        ForeignKey("classrooms.id"),
        nullable=False
    )

    classroom = relationship(
        "Classroom",
        back_populates="students"
    )