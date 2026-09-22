from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..limiter import limiter
from ..models import Employee
from ..schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["employees"])


def _get_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


def _commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="employee_code or email already exists",
        )


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/second")
def create_employee(request: Request, payload: EmployeeCreate, db: Session = Depends(get_db)):
    employee = Employee(**payload.model_dump())
    db.add(employee)
    _commit_or_conflict(db)
    db.refresh(employee)
    return employee


@router.get("", response_model=list[EmployeeRead])
@limiter.limit("10/second")
def list_employees(request: Request, db: Session = Depends(get_db)):
    return db.scalars(select(Employee).order_by(Employee.id)).all()


@router.get("/{employee_id}", response_model=EmployeeRead)
@limiter.limit("10/second")
def get_employee(request: Request, employee_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeRead)
@limiter.limit("10/second")
def update_employee(
    request: Request,
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    employee = _get_or_404(db, employee_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    _commit_or_conflict(db)
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/second")
def delete_employee(request: Request, employee_id: int, db: Session = Depends(get_db)):
    employee = _get_or_404(db, employee_id)
    db.delete(employee)
    db.commit()
