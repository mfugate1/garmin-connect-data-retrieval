from database_drivers.DatabaseDriver import DatabaseDriver
import pymysql.cursors

class MysqlDriver(DatabaseDriver):

    def __init__(self, db_config, config):
        self.host = db_config['host']
        self.user = db_config['user']
        self.password = db_config['password']
        self.db = db_config['database']
        self.default_col_type = db_config['default_col_type']

        conn = self.get_conn(False)
        with conn.cursor() as cursor:
            cursor.execute('SHOW DATABASES')
            result = cursor.fetchall()

            if self.db not in [x[0] for x in result]:
                print(f"Database {self.db} does not exist. Creating it now")
                cursor.execute('CREATE DATABASE {}'.format(self.db))

        conn.commit()
        conn.close()

        conn = self.get_conn(True)

        self.create_table(conn, config['activity_config']['table'], self.generate_cols(config['activity_config']['fields']))
        self.create_table(conn, config['daily_stats_config']['table'], self.generate_cols(config['daily_stats_config']['fields']))
        
        conn.commit()
        conn.close()

    def create_table(self, conn, table, cols):
        cols_str = ', '.join([f'{key} {value}' for key, value in cols.items()])
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols_str})")
            cursor.execute(f"DESC {table}")
            result = cursor.fetchall()
            for field, col_type in cols.items():
                if field not in [x[0] for x in result]:
                    print(f"Missing column {field} {col_type}, adding it now")
                    cursor.execute(f"ALTER TABLE {table} ADD {field} {col_type}")

    def generate_cols(self, fields):
        table_cols = {}
        for field, field_config in fields.items():
            if field_config is not None:
                col_type = field_config['db_col_type'] if 'db_col_type' in field_config else self.default_col_type
                field_units = '_' + field_config['units'].replace(' ', '_') if 'units' in field_config else ''
            else:
                col_type = self.default_col_type
                field_units = ''

            table_cols[field + field_units] = col_type
        return table_cols

    def get_conn(self, withDb = True):
        if withDb:
            return pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.db)
        else:
            return pymysql.connect(host=self.host, user=self.user, password=self.password)

    def insert_data(self, data, table):
        conn = self.get_conn(True)

        with conn.cursor() as cursor:
            cursor.execute(f"DESC {table}")
            result = cursor.fetchall()
            columns = [x[0] for x in result]
            col_str = ', '.join(columns)
            query_params = []
            insert_stmt = f'REPLACE INTO {table} ({col_str}) VALUES '
            comma = ''
            print(columns)
            for row in data:
                print(row)
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
