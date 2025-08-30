from sqlalchemy import create_engine,MetaData,Table,Column
import sqlalchemy
import yaml
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

def create_metadata(): #建表示例 练习
    engine = create_engine('mysql://root:Aa200206@127.0.0.1:3306/world?charset=utf8', echo=True)

    #conn = engine.connect()
    metadata = MetaData()

    admin = Table('admin',metadata,
                  Column('id', sqlalchemy.Integer, primary_key=True),
                  Column('name', sqlalchemy.String(100), nullable=False, unique=True),
                  Column('password', sqlalchemy.String(100), nullable=False),
                  )


    metadata.create_all(engine)

def insert_metadata():   #插入值示例 练习
    # 1. 创建数据库引擎（连接）
    engine = create_engine('mysql://root:Aa200206@127.0.0.1:3306/world?charset=utf8', echo=True)

    # 2. 获取表结构（假设表已存在）
    metadata = MetaData()
    # 使用 autoload=True 自动加载表结构
    table_name = Table('admin', metadata, autoload_with=engine)

    # 3. 插入数据  一条数据
    # with engine.connect() as conn:
    #     # 构造 INSERT 语句
    #     insert_stmt = table_name.insert().values(name='admin2', password='123456')
    #     # 执行插入
    #     result = conn.execute(insert_stmt)
    #     print(result.inserted_primary_key)
    #     conn.commit()


    #插入数据  多条数据
    with engine.connect() as conn:
        insert_stmt = table_name.insert()
        conn.execute(insert_stmt,[
            {'name':'admin3', 'password':'123456'},
            {'name': 'admin4', 'password': '123456'}
        ])
        conn.commit()

def select():  #查询  练习

    # 1. 创建数据库引擎（连接）
    engine = create_engine('mysql://root:Aa200206@127.0.0.1:3306/world?charset=utf8', echo=True)

    # 2. 获取表结构（假设表已存在）
    metadata = MetaData()
    # 使用 autoload=True 自动加载表结构
    table_name = Table('city', metadata, autoload_with=engine)

    from sqlalchemy import and_ ,or_

    with engine.connect() as conn:
        #select_stmt = table_name.select()

        #select_stmt = table_name.select().where(table_name.c.Name == 'Herat')  #条件查询
        select_stmt = table_name.select().where(
            or_(table_name.c.Name == 'Herat'
                ,and_(
                    table_name.c.Population>5000000,table_name.c.CountryCode =='CHN'
                )
            ) ) #条件查询

        result = conn.execute(select_stmt)

        for row in result:
            print(row)

#####################################################################


def orm():


    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    db_conf = config['database']

    engine = create_engine(
        f"{db_conf['type']}://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database_name']}?charset=utf8", echo=True
    )

    Base = declarative_base()

    class users(Base):
        __tablename__ = 'users_info'
        id = Column(sqlalchemy.Integer, primary_key=True)
        name = Column(sqlalchemy.String(100), nullable=False)
        password = Column(sqlalchemy.String(100), nullable=False)
        email = Column(sqlalchemy.String(100), nullable=False)
        address = Column(sqlalchemy.String(100), nullable=False)


    Session = sessionmaker(bind=engine)
    session = Session()
    sum_data =[
        users(name='Herat', password='1234566', address='beijing'),
        users(name='faf', password='1234566', address='shanghai'),
        users(name='afqqg', password='1234566', address='zhanjiang')
    ]
    #datas = users(name = 'Herat',password = '1234566',address = 'beijing')
    #session.add(datas)
    session.add_all(sum_data)
    session.commit()


if __name__ == '__main__':
    orm()