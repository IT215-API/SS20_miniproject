from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Student, Classroom
from schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    APIResponse
)


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


def response_data(
    status_code,
    message,
    data,
    path
):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": None,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "path": path
    }

@router.get("")
def get_students(
    name: Optional[str] = Query(None),
    student_code: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    class_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Student)
        .options(
            joinedload(Student.classroom)
        )
    )

    if name:
        query = query.filter(
            Student.full_name.ilike(
                f"%{name}%"
            )
        )

    if student_code:
        query = query.filter(
            Student.student_code.ilike(
                f"%{student_code}%"
            )
        )

    if email:
        query = query.filter(
            Student.email.ilike(
                f"%{email}%"
            )
        )

    if class_id:
        query = query.filter(
            Student.class_id == class_id
        )

    students = query.all()

    return response_data(
        200,
        "Lấy danh sách sinh viên thành công",
        students,
        "/students"
    )

@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = (
        db.query(Student)
        .options(
            joinedload(Student.classroom)
        )
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy sinh viên"
        )

    return response_data(
        200,
        "Lấy thông tin sinh viên thành công",
        student,
        f"/students/{student_id}"
    )

@router.post(
    "",
    status_code=201
)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db)
):
    
    if student_data.gender not in [
        "male",
        "female",
        "other"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Gender phải là male, female hoặc other"
        )

    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == student_data.class_id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Lớp học không tồn tại"
        )

    if classroom.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Lớp học không hoạt động"
        )

    student_count = (
        db.query(Student)
        .filter(
            Student.class_id == classroom.id
        )
        .count()
    )

    if student_count >= classroom.max_students:
        raise HTTPException(
            status_code=400,
            detail="Lớp học đã đủ số lượng sinh viên"
        )

    existing_code = (
        db.query(Student)
        .filter(
            Student.student_code
            == student_data.student_code
        )
        .first()
    )

    if existing_code:
        raise HTTPException(
            status_code=409,
            detail="Mã sinh viên đã tồn tại"
        )

    existing_email = (
        db.query(Student)
        .filter(
            Student.email == student_data.email
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email đã tồn tại"
        )

    student = Student(
        student_code=student_data.student_code,
        full_name=student_data.full_name,
        email=student_data.email,
        age=student_data.age,
        gender=student_data.gender,
        class_id=student_data.class_id
    )

    db.add(student)

    db.commit()

    db.refresh(student)

    student = (
        db.query(Student)
        .options(
            joinedload(Student.classroom)
        )
        .filter(Student.id == student.id)
        .first()
    )

    return response_data(
        201,
        "Thêm sinh viên thành công",
        student,
        "/students"
    )

@router.put("/{student_id}")
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db)
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy sinh viên"
        )

    # Gender
    if (
        student_data.gender is not None
        and student_data.gender not in [
            "male",
            "female",
            "other"
        ]
    ):
        raise HTTPException(
            status_code=400,
            detail="Gender không hợp lệ"
        )

    # Student code
    if student_data.student_code:

        duplicate = (
            db.query(Student)
            .filter(
                Student.student_code
                == student_data.student_code,
                Student.id != student_id
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Mã sinh viên đã tồn tại"
            )

    if student_data.email:

        duplicate = (
            db.query(Student)
            .filter(
                Student.email
                == student_data.email,
                Student.id != student_id
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Email đã tồn tại"
            )

    if (
        student_data.class_id is not None
        and student_data.class_id != student.class_id
    ):
        new_class = (
            db.query(Classroom)
            .filter(
                Classroom.id
                == student_data.class_id
            )
            .first()
        )

        if not new_class:
            raise HTTPException(
                status_code=404,
                detail="Lớp mới không tồn tại"
            )

        if new_class.status != "active":
            raise HTTPException(
                status_code=400,
                detail="Lớp mới không hoạt động"
            )

        count = (
            db.query(Student)
            .filter(
                Student.class_id == new_class.id
            )
            .count()
        )

        if count >= new_class.max_students:
            raise HTTPException(
                status_code=400,
                detail="Lớp mới đã đủ số lượng"
            )

    data = student_data.model_dump(
        exclude_unset=True
    )

    for key, value in data.items():
        setattr(student, key, value)

    db.commit()

    db.refresh(student)

    student = (
        db.query(Student)
        .options(
            joinedload(Student.classroom)
        )
        .filter(Student.id == student_id)
        .first()
    )

    return response_data(
        200,
        "Cập nhật sinh viên thành công",
        student,
        f"/students/{student_id}"
    )