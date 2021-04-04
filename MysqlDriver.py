from DatabaseDriver import DatabaseDriver
import pymysql.cursors

class MysqlDriver(DatabaseDriver):

    def __init__(self, db_config, config):
        self.host = db_config['host']
        self.user = db_config['user']
        self.password = db_config['password']
        self.db = db_config['database']
        self.activity_table = db_config['activity_table']

        conn = self.get_conn(False)
        with conn.cursor() as cursor:
            cursor.execute('SHOW DATABASES')
            result = cursor.fetchall()

            if self.db not in [x[0] for x in result]:
                print(f"Database {self.db} does not exist. Creating it now")
                cursor.execute('CREATE DATABASE {}'.format(self.db))

        conn.commit()
        conn.close()

        table_cols = {}
        for field, field_config in config['fields'].items():
            if field_config is not None:
                col_type = field_config['db_col_type'] if 'db_col_type' in field_config else db_config['default_col_type']
                field_units = '_' + field_config['units'].replace(' ', '_') if 'units' in field_config else ''
            else:
                col_type = db_config['default_col_type']
                field_units = ''

            table_cols[field + field_units] = col_type

        all_cols = ', '.join([f'{key} {value}' for key, value in table_cols.items()])

        conn = self.get_conn(True)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.activity_table} ({all_cols})")
            cursor.execute(f"DESC {self.activity_table}")
            result = cursor.fetchall()
            for field, col_type in table_cols.items():
                if field not in [x[0] for x in result]:
                    print(f"Missing column {field} {col_type}, adding it now")
                    cursor.execute(f"ALTER TABLE {self.activity_table} ADD {field} {col_type}")
                    
        conn.commit()
        conn.close()

    def get_conn(self, withDb = True):
        if withDb:
            return pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.db)
        else:
            return pymysql.connect(host=self.host, user=self.user, password=self.password)

    def insert_data(self, data):
        conn = self.get_conn(True)

        with conn.cursor() as cursor:
            cursor.execute(f"DESC {self.activity_table}")
            result = cursor.fetchall()
            columns = [x[0] for x in result]
            col_str = ', '.join(columns)
            query_params = []
            insert_stmt = f'INSERT IGNORE INTO {self.activity_table} ({col_str}) VALUES '
            comma = ''
            for row in data:
                insert_stmt += f'{comma}({", ".join(["%s" for x in range(len(columns))])})'
                for col in columns:
                    if col in row:
                        query_params.append(row[col])
                    else:
                        query_params.append(None)
                comma = ', '
            cursor.execute(insert_stmt, query_params)

        conn.commit()
        conn.close()
