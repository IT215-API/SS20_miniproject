from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request
)

from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Student, Classroom
from schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse
)


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


def make_response(
    status_code: int,
    message: str,
    data,
    error,
    path: str
):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "path": path
    }


@router.get("/")
def get_students(
    request: Request,
    name: Optional[str] = Query(None),
    student_code: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    class_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Student)
        .options(joinedload(Student.classroom))
    )

    if name:
        query = query.filter(
            Student.full_name.ilike(f"%{name}%")
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

    data = [
        StudentResponse.model_validate(
            student
        ).model_dump()
        for student in students
    ]

    return make_response(
        200,
        "Lấy danh sách sinh viên thành công",
        data,
        None,
        request.url.path
    )


@router.get("/{student_id}")
def get_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    student = (
        db.query(Student)
        .options(joinedload(Student.classroom))
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy sinh viên"
        )

    data = StudentResponse.model_validate(
        student
    ).model_dump()

    return make_response(
        200,
        "Lấy thông tin sinh viên thành công",
        data,
        None,
        request.url.path
    )


@router.post("", status_code=201)
def create_student(
    student_data: StudentCreate,
    request: Request,
    db: Session = Depends(get_db)
):
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
        .options(joinedload(Student.classroom))
        .filter(Student.id == student.id)
        .first()
    )

    data = StudentResponse.model_validate(
        student
    ).model_dump()

    return make_response(
        201,
        "Thêm sinh viên thành công",
        data,
        None,
        request.url.path
    )


@router.put("/{student_id}")
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    request: Request,
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

    if student_data.student_code:
        duplicate_code = (
            db.query(Student)
            .filter(
                Student.student_code
                == student_data.student_code,
                Student.id != student_id
            )
            .first()
        )

        if duplicate_code:
            raise HTTPException(
                status_code=409,
                detail="Mã sinh viên đã tồn tại"
            )

    if student_data.email:
        duplicate_email = (
            db.query(Student)
            .filter(
                Student.email == student_data.email,
                Student.id != student_id
            )
            .first()
        )

        if duplicate_email:
            raise HTTPException(
                status_code=409,
                detail="Email đã tồn tại"
            )

    if (
        student_data.class_id is not None
        and student_data.class_id != student.class_id
    ):
        new_classroom = (
            db.query(Classroom)
            .filter(
                Classroom.id == student_data.class_id
            )
            .first()
        )

        if not new_classroom:
            raise HTTPException(
                status_code=404,
                detail="Lớp học mới không tồn tại"
            )

        if new_classroom.status != "active":
            raise HTTPException(
                status_code=400,
                detail="Lớp học mới không hoạt động"
            )

        new_class_count = (
            db.query(Student)
            .filter(
                Student.class_id
                == new_classroom.id
            )
            .count()
        )

        if new_class_count >= new_classroom.max_students:
            raise HTTPException(
                status_code=400,
                detail="Lớp học mới đã đủ số lượng sinh viên"
            )

    update_data = student_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)

    student = (
        db.query(Student)
        .options(joinedload(Student.classroom))
        .filter(Student.id == student_id)
        .first()
    )

    data = StudentResponse.model_validate(
        student
    ).model_dump()

    return make_response(
        200,
        "Cập nhật sinh viên thành công",
        data,
        None,
        request.url.path
    )