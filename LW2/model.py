from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declarative_base,
    sessionmaker
)
from sqlalchemy import URL, create_engine
from sqlalchemy import Select
from sqlalchemy import func
import os


Base = declarative_base()



class Student(Base):

    __tablename__ = 'student'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    group: Mapped[int]

    def __repr__(self) -> str:
        return f'Student(id={self.id}; first_name={self.first_name}; last_name={self.last_name}; group={self.group})'
    

class DBWorker:

    def __init__(self) -> None:
        self._DB_URL = URL.create(
            drivername='postgresql+psycopg',
            username=os.getenv('DB_OWNER_NAME'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST_NAME'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME')
        )
        self._engine = create_engine(url=self._DB_URL)
        self._Session = sessionmaker(bind=self._engine)


    def create_database(self):            
        Base.metadata.create_all(self._engine)        

    def delete_database(self):            
        Base.metadata.drop_all(self._engine)
    
    def get_students(self):
        with self._Session() as session:
            stmt = Select(Student)
            students = session.scalars(stmt)
            return students.all()

    def create_student(self, first_name: str, last_name: str, group: int):
        print('Called!')
        with self._Session() as session:
            new_student = Student(first_name=first_name, last_name=last_name, group=group)
            session.add(new_student)
            session.commit()

    def get_students_amount(self) -> int:
        with self._Session() as session:
            return session.query(Student).count()