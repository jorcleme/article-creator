# import psycopg2
# from psycopg2.extras import DictCursor

# connection = psycopg2.connect("dbname=dqsg user=jorcleme password=qzpm*QZPM24")
# cursor = connection.cursor(cursor_factory=DictCursor)
# cursor.execute(
#     'SELECT a."vector", a."title" FROM "Article" a INNER JOIN "_ArticleToProductFamily" atpf ON a.id = atpf."A" INNER JOIN "ProductFamily" pf ON pf.id = atpf."B" WHERE pf.id = \'b755b539-4dc2-41c0-8ca4-2e18ecfce895\''
# )

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://jorcleme:qzpm*QZPM24@localhost:5432/test_hig"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

Base = declarative_base()
