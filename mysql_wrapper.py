import MySQLdb
import helpers.crypt
import copy

class Empty: pass

def diff(other):
    return {
        k: v for k, v in vars(other).items()
        if k not in vars(Empty).keys() and not callable(other.__dict__[k])
    }

def getattribute(cls, name):
    if name.startswith("_"):
        return object.__getattribute__(cls, name)
    return BaseOperator(name)

class BaseMetaclass(type):
    """BaseMetaclass"""
    def __new__(cls, clsname, superclasses, attributedict):
        cls.__getattribute__ = lambda a, b: getattribute(a, b)
        return type.__new__(cls, clsname, superclasses, attributedict)

class Base(metaclass=BaseMetaclass):
    """Base class for all databases"""
    def __init__(self, *args, **kwargs):
        dic = diff(type(self))
        for k, v in dic.items(): setattr(self, k, v)
        for arg in args:
            for key, value in arg.items():
                if key in dic:
                    setattr(self, key, value)

class BaseOperator:
    """For operator operations"""
    def __init__(self, name):
        self.__name = name

    def __eq__(self, value):
        return (self.__name, value)

class Session:
    """Creates and handles the database session"""
    def __init__(self, user, passwd, db_name):
        self.db = MySQLdb.connect(user=user, passwd=passwd, db=db_name)
        for subclass in Base.__subclasses__():
            self.create_table(subclass)

    def create_table(self, obj):
        return create_table(self.db, obj)

    def query(self, obj):
        return query(self.db, obj)

    def add(self, obj):
        obj.id = add(self.db, helpers.crypt.encrypt_obj(copy.deepcopy(obj)))
        return obj

    def update(self, obj):
        return update(self.db, helpers.crypt.encrypt_obj(copy.deepcopy(obj)))

    def delete(self, obj):
        return delete(self.db, obj)

class Query:
    """A class that is returned when asking to do a query"""
    def __init__(self, db, obj):
        self.db = db
        self.obj = obj
        self.query = "SELECT * FROM " + obj.__tablename__
        self.all_values = []
        self.where_is_used = False

    def first(self):
        self.query += ";"
        print(self.query)
        cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        result = cursor.fetchone()
        if not result:
            return None
        return helpers.crypt.decrypt_obj(self.obj(result))

    def all(self):
        self.query += ";"
        print(self.query)
        cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        results = list(cursor.fetchall())
        if not results:
            return None
        to_return = []
        for result in results:
            to_return.append(helpers.crypt.decrypt_obj(self.obj(result)))
        return to_return

    def delete(self):
        self.query += ";"
        print(self.query)
        cursor = self.db.cursor()
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        results = list(cursor.fetchall())
        if not results:
            return None
        to_return = []
        for result in results:
            to_return.append(helpers.crypt.decrypt_obj(self.obj(*result)))
        for o in to_return:
            delete(self.db, o)

    def where(self, *args):
        for key, value in args:
            if self.where_is_used:
                self.query += " AND "
            else:
                self.where_is_used = True
                self.query += " WHERE "
            self.query += key + " = %s"
            self.all_values.append(value)
        return self

def query(db, obj):
    return Query(db, obj)

def delete(db, obj):
    dic = vars(obj)
    if not 'id' in dic:
        return
    query = "DELETE FROM " + obj.__tablename__ + " WHERE id = " + str(dic["id"]) + ";"
    print(query)
    cursor = db.cursor()
    cursor.execute(query)
    db.commit()
    obj.id = int()

def update(db, obj):
    query = "UPDATE " + obj.__tablename__ + " SET "
    all_values = []
    obj_id = -1
    for key, value in vars(obj).items():
        if key == "id":
            obj_id = value
            continue
        if key.startswith("_") or key == "ignore" or key == "to_hash":
            continue
        query += key + " = %s, "
        all_values.append(value)
    if obj_id < 0:
        return
    query = query[:-2]
    query += " WHERE id = " + str(obj_id) + ";"
    print(query)
    cursor = db.cursor()
    cursor.execute(query, all_values)
    db.commit()

def add(db, obj):
    query = "INSERT INTO " + obj.__tablename__ + " ("
    all_values = []
    for key, value in vars(obj).items():
        if key.startswith("_") or key == "id" or key == "ignore" or key == "to_hash":
            continue
        query += key + ","
        all_values.append(value)
    if query.endswith("("):
        return
    query = query[:-1]
    query += ") VALUES ("
    for _ in range(len(all_values)):
        query += "%s,"
    query = query[:-1]
    query += ");"
    print(query)
    cursor = db.cursor()
    cursor.execute(query, all_values)
    db.commit()
    return cursor.lastrowid

def create_table(db, obj):
    query = "CREATE TABLE IF NOT EXISTS " + obj.__tablename__ + " ("
    has_id = False
    for key, value in vars(obj).items():
        if key.startswith("_"):
            continue
        if isinstance(value, int):
            query += key + " MEDIUMINT"
            if key == "id":
                has_id = True
                query += " NOT NULL AUTO_INCREMENT"
            query += ", "
        elif isinstance(value, bytes):
            query += key + " BLOB, "
        elif isinstance(value, bool):
            query += key + " BOOLEAN, "
    if has_id:
        query += "PRIMARY KEY (id), "
    if query.endswith("("):
        query = query[:-2]
    else:
        query = query[:-2]
        query += ")"
    print(query)
    query += ";"
    cursor = db.cursor()
    cursor.execute(query)
