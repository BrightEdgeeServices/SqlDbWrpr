"""Database wrapper utilities for MySQL and PostgreSQL.

SqlDbWrpr creates databases and tables from either the legacy dictionary
structure or SQLAlchemy metadata, then imports and exports CSV data through a
small DB-API based wrapper.
"""

import datetime
import logging
import os
import sys

import csvwrpr
import displayfx
import fixdate
import mysql.connector
import psycopg
from beetools import msg as bm
from mysql.connector import errorcode

# from pathlib import Path


# _PROJ_DESC = __doc__.split("\n")[0]
# _PROJ_PATH = Path(__file__)
# _PROJ_NAME = _PROJ_PATH.stem


class SchemaSourceError(ValueError):
    """Raised when no supported database schema source is supplied."""


class SQLDbWrpr:
    """Base wrapper for schema creation and CSV import/export operations."""

    def __init__(
        self,
        p_host_name="localhost",
        p_user_name="",
        p_password="",
        p_recreate_db=False,
        p_db_name="",
        p_db_structure=None,
        p_sqlalchemy_base=None,
        p_sqlalchemy_metadata=None,
        p_batch_size=10000,
        p_bar_len=50,
        p_msg_width=50,
        p_verbose=False,
        p_db_port="3306",
        p_ssl_ca=None,
        p_ssl_key=None,
        p_ssl_cert=None,
    ):
        """Initialize common wrapper state and resolve the database schema.

        A legacy `p_db_structure` dictionary takes precedence. If it is not
        supplied, SQLAlchemy metadata is read from `p_sqlalchemy_metadata` or
        from `p_sqlalchemy_base.metadata`. A `SchemaSourceError` is raised when
        none of those schema sources are available.

        Parameters
        - p_host_name: Host to connect to.
        - p_user_name: User name for the connection.
        - p_password: Password for the connection.
        - p_recreate_db: Recreate the database when the backend supports it.
        - p_db_name: Database name.
        - p_db_structure: Legacy SqlDbWrpr table/field dictionary.
        - p_sqlalchemy_base: Declarative base that exposes SQLAlchemy metadata.
        - p_sqlalchemy_metadata: SQLAlchemy MetaData instance.
        - p_batch_size: Number of rows committed per import batch.
        - p_bar_len: Length of progress bars.
        - p_msg_width: Width of progress messages.
        """
        self.logger_name = __name__
        self.logger = logging.getLogger(self.logger_name)
        self.logger.info("Start")
        self.success = False
        self.bar_len = p_bar_len
        self.batch_size = p_batch_size
        self.char_fields = {}
        self.conn = None
        self.cur = None
        self.db_name = p_db_name
        self.db_structure = self.resolve_db_structure(
            p_db_structure=p_db_structure,
            p_sqlalchemy_base=p_sqlalchemy_base,
            p_sqlalchemy_metadata=p_sqlalchemy_metadata,
        )
        self.db_error = mysql.connector.Error
        self.delimiter = ","
        self.fkey_ref_act = {
            "C": "CASCADE",
            "R": "RESTRICT",
            "D": "SET DEFAULT",
            "N": "SET NULL",
        }
        self.host_name = p_host_name
        self.identifier_quote = ""
        self.idx_type = {"U": "UNIQUE", "F": "FULLTEXT", "S": "SPATIAL"}
        self.inline_indexes = True
        self.msg_width = p_msg_width
        self.non_char_fields = {}
        self._password = p_password
        self.re_create_db = p_recreate_db
        self.silent = p_verbose
        self.sort_order = {"A": "ASC", "D": "DESC"}
        self.table_load_order = []
        self.user_name = p_user_name
        self.get_db_field_types()
        self.db_port = p_db_port

    def close(self):
        """Close the active database connection."""
        if self.conn:
            self.conn.close()

    def build_column_sql(self, p_field_name, p_field_type, p_field_params, p_field_comment):
        """Build SQL for one column in a CREATE TABLE statement."""
        sql_str = f"{self.quote_identifier(p_field_name)} {self.render_field_type(p_field_type, p_field_params)}"
        if p_field_params["AI"] == "Y":
            sql_str += " AUTO_INCREMENT"
        if p_field_params["UN"] == "Y" and p_field_params["AI"] != "Y":
            sql_str += " UNSIGNED"
        if p_field_params["NN"] == "Y":
            sql_str += " NOT NULL"
        if p_field_params["ZF"] == "Y":
            sql_str += " ZEROFILL"
        if p_field_params["DEF"]:
            sql_str += self.render_default_sql(p_field_type, p_field_params["DEF"])
        if p_field_comment:
            sql_str += f' COMMENT "{p_field_comment}"'
        return sql_str

    def build_index_sql(self, p_table_name, p_idx_name, p_idx_fields, p_unique=False):
        """Build an index clause for the active SQL dialect."""
        idx_type = "UNIQUE INDEX" if p_unique else "INDEX"
        index_fields = []
        for field_det in p_idx_fields:
            index_fields.append(f"{self.quote_identifier(field_det[0])} {self.sort_order[field_det[2]]}")
        return f"{idx_type} {self.quote_identifier(p_idx_name)} ({','.join(index_fields)}) VISIBLE, "

    def build_insert_sql(self, p_table_name, p_header, p_replace=False):
        """Build SQL for inserting rows into a table."""
        insert_command = "REPLACE" if p_replace else "INSERT"
        return "{} INTO {} ({}) VALUES ({})".format(
            insert_command,
            self.quote_identifier(p_table_name),
            ",".join([self.quote_identifier(str(x)) for x in p_header]),
            ",".join([self.param_placeholder() for x in range(len(p_header))]),
        )

    def param_placeholder(self):
        """Return the DB-API placeholder used by this backend."""
        return "%s"

    def quote_identifier(self, p_identifier):
        """Quote an SQL identifier for this backend."""
        if not self.identifier_quote:
            return str(p_identifier)
        escaped_identifier = str(p_identifier).replace(self.identifier_quote, self.identifier_quote * 2)
        return f"{self.identifier_quote}{escaped_identifier}{self.identifier_quote}"

    def quote_identifier_list(self, p_identifiers):
        """Quote and join SQL identifiers."""
        return ",".join([self.quote_identifier(p_identifier) for p_identifier in p_identifiers])

    def render_default_sql(self, p_field_type, p_default_value):
        """Render a column default expression."""
        if p_field_type[0] == "varchar" or p_field_type[0] == "char":
            return f' DEFAULT "{p_default_value}"'
        return f" DEFAULT {p_default_value}"

    def render_field_type(self, p_field_type, p_field_params):
        """Render a field type for this backend."""
        field_type = p_field_type[0]
        if field_type == "varchar" or field_type == "char":
            return f"{field_type} ({str(p_field_type[1])})"
        if field_type == "decimal":
            return f"{field_type}({str(p_field_type[1])}, {str(p_field_type[2])})"
        return field_type

    def create_db(self):
        """Create the database according to self.db_structure."""
        self.cur.execute("SHOW DATABASES")
        db_res = [x[0].decode() if isinstance(x[0], (bytearray, bytes)) else str(x[0]) for x in self.cur.fetchall()]
        # if self.db_name.lower() in db_res:
        if self.db_name in db_res:
            try:
                self.cur.execute(f"DROP DATABASE {self.db_name}")
                self.conn.commit()
            except self.db_error as err:
                self._print_err_msg(err, "Could not drop the database")
                self.close()
                sys.exit()
        try:
            self.cur.execute(f'CREATE DATABASE {self.db_name} DEFAULT CHARACTER SET "utf8"')
            self.conn.commit()
            self.cur.execute(f"USE {self.db_name}")
            self.conn.commit()
        except self.db_error as err:
            self._print_err_msg(err, "Could not create the database")
            self.close()
            sys.exit()
        return True

    def create_tables(self):
        """Create database tables, indexes, and constraints from the resolved schema."""

        def build_db(p_db_sql_str_set):
            """Execute the generated table or index SQL statements."""
            for sql_set in p_db_sql_str_set:
                try:
                    self.cur.execute(sql_set[1])
                    if self.silent:
                        print(f"Created table = {sql_set[0]}")
                except self.db_error as err:
                    print(f"Failed creating table = {sql_set[0]}: {err}\nForced termination of program")
                    print(f"{sql_set[1]}")
                    sys.exit()
            pass

        # end build_db

        def generate_db_sql(
            p_table_set_up_str,
            p_primary_key_str,
            p_idx_set_up_list,
            p_constraint_set_up_list,
        ):
            """Combine column, primary-key, index, and constraint SQL."""
            table_set_up_str = p_table_set_up_str
            table_set_up_str += p_primary_key_str
            for idx_str in p_idx_set_up_list:
                table_set_up_str += idx_str
            for constraint_str in p_constraint_set_up_list:
                table_set_up_str += constraint_str[2]
            table_set_up_str = f"{table_set_up_str[:-2]})"
            return table_set_up_str

        # end generate_db_sql

        def build_constraints(p_table_name):
            # noinspection PySingleQuotedDocstring
            """Build foreign-key constraint SQL for one table."""
            constraint_list = []
            fkey_nr_list = []
            for field_name in self.db_structure[p_table_name]:
                fkey = get_foreign_key(p_table_name, field_name)
                if fkey["Present"]:
                    fkey_nr_list.append(fkey["ForeignKeyNr"])
                    # fkey_PROJ_NAME = 'fk_{}_{}'.format( fkey[ 'FKeyTable' ], fkey[ 'RefTable' ])
                    fkey_str = (
                        "CONSTRAINT fk_{}_{} FOREIGN KEY ({}) REFERENCES {} ({}) ON DELETE {} ON UPDATE {}, ".format(
                            fkey["FKeyTable"],
                            fkey["RefTable"],
                            self.quote_identifier_list(fkey["FKeyFlds"]),
                            self.quote_identifier(fkey["RefTable"]),
                            self.quote_identifier_list(fkey["RefFields"]),
                            self.fkey_ref_act[fkey["OnDelete"]],
                            self.fkey_ref_act[fkey["OnUpdate"]],
                        )
                    )
                    constraint_list.append([fkey["FKeyTable"], fkey["RefTable"], fkey_str])
                    pass
            return constraint_list

        # def build_constraints

        def build_all_indexes(p_table_name):
            """Build inline or post-create index SQL for one table."""

            # def build_primary_key_idx(p_table_name):
            #     '''Build primary-key index SQL.'''
            #     idx_name_list = []
            #     idx_str_list = []
            #     pkey = get_primary_key(p_table_name)
            #     idx_name = '{}_UNIQUE'.format('_'.join(pkey['Flds']))
            #     idx_name_list.append(idx_name)
            #     idx_str = 'UNIQUE INDEX pk_{} ({}) VISIBLE, '.format(
            #         idx_name, ','.join(pkey['Flds'])
            #     )
            #     idx_str_list.append(idx_str)
            #     return idx_str_list, idx_name_list
            #
            # # end build_primary_key_idx

            def build_unique_key_idx(p_table_name, p_dx_name_list, p_idx_str_list):
                """Build grouped index definitions from legacy field metadata."""
                idx_list = {}
                idx_name_list = p_dx_name_list
                idx_str_list = p_idx_str_list
                for field_name in self.db_structure[p_table_name]:
                    field_param_st_ref = self.db_structure[p_table_name][field_name]["Params"]
                    if field_param_st_ref["Index"]:
                        if field_param_st_ref["Index"][0] not in idx_list:
                            idx_list[field_param_st_ref["Index"][0]] = [[field_name] + field_param_st_ref["Index"][1:]]
                        else:
                            idx_list[field_param_st_ref["Index"][0]].append(
                                [field_name] + field_param_st_ref["Index"][1:]
                            )
                for idx_instance in idx_list:
                    idx_instance_order = sorted(idx_list[idx_instance], key=lambda x: x[1])
                    idx_name = ""
                    for field_det in idx_instance_order:
                        idx_name += f"{field_det[0]}_"
                    if field_det[3] == "U":
                        idx_name = f"unq_{idx_name[:-1]}"
                    else:
                        idx_name = f"idx_{idx_name[:-1]}"
                    if idx_name not in idx_name_list:
                        idx_name_list.append(idx_name)
                        idx_str = self.build_index_sql(
                            p_table_name,
                            idx_name,
                            idx_instance_order,
                            field_det[3] == "U",
                        )
                        if self.inline_indexes:
                            idx_str_list.append(idx_str)
                        else:
                            post_create_sql_set.append([idx_name, idx_str])
                return idx_str_list, idx_name_list

            # end build_unique_key_idx

            idx_name_list = []
            idx_list = []
            idx_list, idx_name_list = build_unique_key_idx(p_table_name, idx_name_list, idx_list)
            return idx_list

        # def build_all_indexes

        def build_primary_key_sql_str(p_table_name):
            """Build the primary-key clause for one table."""
            primary_key_det = get_primary_key(p_table_name)
            sql_str = "PRIMARY KEY ({}), ".format(self.quote_identifier_list(primary_key_det["Flds"]))
            return sql_str

        # def build_primary_key_sql_str

        def build_table_sql_str(p_table_name):
            """Build the CREATE TABLE prefix and column definitions."""
            sql_str = f"CREATE TABLE {self.quote_identifier(p_table_name)} ("
            for field_name in self.db_structure[p_table_name]:
                field_type_st_ref = self.db_structure[p_table_name][field_name]["Type"]
                field_param_st_ref = self.db_structure[p_table_name][field_name]["Params"]
                field_comment_st_ref = self.db_structure[p_table_name][field_name]["Comment"]
                sql_str += self.build_column_sql(
                    field_name,
                    field_type_st_ref,
                    field_param_st_ref,
                    field_comment_st_ref,
                )
                sql_str += ", "
            return sql_str

        # end build_table_sql_str

        def get_foreign_key(p_table_name, p_field_name):
            """Return normalized foreign-key metadata for a field."""
            fkey = {
                "Present": False,
                "FKeyFlds": [],
                "RefFields": [],
                "FKeyTable": "",
                "RefTable": "",
                "ForeignKeyNr": False,
                "OnDelete": "N",
                "OnUpdate": "N",
            }
            fkey_source = self.db_structure[p_table_name][p_field_name]["Params"]["FKey"]
            if fkey_source:
                table_det = self.db_structure[p_table_name]
                fkey["ForeignKeyNr"] = fkey_source[0]
                fkey["FKeyTable"] = p_table_name
                fkey["RefTable"] = fkey_source[2]
                ref_field_pair_list = []
                for field in table_det:
                    if table_det[field]["Params"]["FKey"]:
                        if table_det[field]["Params"]["FKey"][0] == fkey["ForeignKeyNr"]:
                            ref_field_pair_list.append(
                                [
                                    field,
                                    table_det[field]["Params"]["FKey"][3],
                                    table_det[field]["Params"]["FKey"][1],
                                ]
                            )
                ref_field_pair_list = sorted(ref_field_pair_list, key=lambda x: x[2])
                fkey["FKeyFlds"], fkey["RefFields"], t_order = zip(*ref_field_pair_list)
                fkey["OnDelete"] = fkey_source[4]
                fkey["OnUpdate"] = fkey_source[5]
                fkey["Present"] = True
            return fkey

        # end get_foreign_key

        def get_primary_key(p_table_name):
            """Return normalized primary-key metadata for a table."""
            pkey = {"Present": False, "Flds": (), "SortPairList": [], "SortPairStr": []}
            for field_name in self.db_structure[p_table_name]:
                pkey_field_det = self.db_structure[p_table_name][field_name]
                if pkey_field_det["Params"]["PrimaryKey"][0] == "Y":
                    pkey["Flds"] += (field_name,)
                    pkey["SortPairList"].append(
                        (
                            field_name,
                            self.sort_order[pkey_field_det["Params"]["PrimaryKey"][1]],
                        )
                    )
                    pkey["SortPairStr"].append(
                        "{} {}".format(
                            field_name,
                            self.sort_order[pkey_field_det["Params"]["PrimaryKey"][1]],
                        )
                    )
                    pkey["Present"] = True
            return pkey

        # end get_primary_key

        def order_table_build_list(p_db_sql_str_set, p_constraint_set_up_list):
            """Order table creation so referenced tables are created first."""
            db_sql_str_set = p_db_sql_str_set
            ordered = False
            while not ordered:
                ordered = True
                for constraint in p_constraint_set_up_list:
                    fkey_pos_found = False
                    i = 0
                    fkey_pos = -1
                    while not fkey_pos_found:
                        if db_sql_str_set[i][0] == constraint[1]:
                            fkey_pos_found = True
                            fkey_pos = i
                        else:
                            i += 1
                    table_pos_found = False
                    i = 0
                    tbl_pos = -1
                    while not table_pos_found:
                        if db_sql_str_set[i][0] == constraint[0]:
                            table_pos_found = True
                            tbl_pos = i
                        else:
                            i += 1
                    if tbl_pos < fkey_pos:
                        db_sql_str_set.insert(fkey_pos + 1, db_sql_str_set[tbl_pos])
                        del db_sql_str_set[tbl_pos]
                        ordered = False
            self.table_load_order = [x[0] for x in db_sql_str_set]
            return db_sql_str_set

        # end order_table_build_list

        def structure_validation():
            """Validate schema relationships before SQL generation."""

            def check_pkey_fkey_overlap(p_remove_fkey_pkey__overlap=True):
                """Detect and optionally remove primary-key/foreign-key overlap."""

                def partial_overlap(p_fkey, p_pkey):
                    """Return whether a foreign key partially overlaps a primary key."""
                    is_overlap = False
                    for field_name in p_fkey["FKeyFlds"]:
                        if field_name in p_pkey["Flds"]:
                            is_overlap = True
                    return is_overlap

                # end partial_overlap

                def remove_fkey(p_fkey):
                    """Remove a foreign-key definition from all participating fields."""
                    for field_name in self.db_structure[p_fkey["FKeyTable"]]:
                        if self.db_structure[p_fkey["FKeyTable"]][field_name]["Params"]["FKey"]:
                            if (
                                self.db_structure[p_fkey["FKeyTable"]][field_name]["Params"]["FKey"][0]
                                == p_fkey["ForeignKeyNr"]
                            ):
                                self.db_structure[p_fkey["FKeyTable"]][field_name]["Params"]["FKey"] = []
                    pass

                # end remove_fkey

                for table_name in self.db_structure:
                    pkey = get_primary_key(table_name)
                    source_table = self.db_structure[table_name]
                    for field_name in source_table:
                        fkey = get_foreign_key(table_name, field_name)
                        if fkey["Present"]:
                            if pkey["Flds"] != fkey["FKeyFlds"] and partial_overlap(fkey, pkey):
                                log_str = "The foreign key {}.{} and the primary key in {}.{} overlaps.".format(
                                    fkey["FKeyTable"],
                                    fkey["FKeyFlds"],
                                    table_name,
                                    pkey["Flds"],
                                )
                                self.logger.warning(log_str)
                                if p_remove_fkey_pkey__overlap:
                                    remove_fkey(fkey)
                                    log_str = 'Current settings forced removed the foreign key "{}.{}"'.format(
                                        fkey["FKeyTable"], fkey["FKeyFlds"]
                                    )
                                    self.logger.warning(log_str)
                                else:
                                    log_str = "This may cause a problem adding record to either {} or {}".format(
                                        fkey["FKeyTable"], table_name
                                    )
                                    self.logger.warning(log_str)
                        pass
                    pass

            # end check_pkey_ukey_overlap
            check_pkey_fkey_overlap()
            pass

        # end structure_validation()

        success = True
        post_create_sql_set = []
        structure_validation()
        table_set_up_list = ""
        idx_set_up_list = []
        constraint_set_up_list = []
        db_sql_str_set = []
        for table_name in self.db_structure:
            table_set_up_list = build_table_sql_str(table_name)
            primary_key_str = build_primary_key_sql_str(table_name)
            idx_set_up_list = build_all_indexes(table_name)
            tblconstraint_list = build_constraints(table_name)
            db_sql_str_set.append(
                [
                    table_name,
                    generate_db_sql(
                        table_set_up_list,
                        primary_key_str,
                        idx_set_up_list,
                        tblconstraint_list,
                    ),
                ]
            )
            if tblconstraint_list:
                constraint_set_up_list += tblconstraint_list
            pass
        db_sql_str_set = order_table_build_list(db_sql_str_set, constraint_set_up_list)
        build_db(db_sql_str_set)
        build_db(post_create_sql_set)
        return success

    def create_users(self, p_admin_user, p_new_users):
        """Create database users.

        Concrete database backends must implement this because user management
        SQL differs between databases.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement create_users()")

    def delete_users(self, p_admin_user, p_del_users):
        """Delete database users.

        Concrete database backends must implement this because user management
        SQL differs between databases.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement delete_users()")

    def grant_rights(self, p_admin_user, p_user_rights):
        """Grant database rights.

        Concrete database backends must implement this because privilege syntax
        differs between databases.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement grant_rights()")

    def _err_broken_rec(self, p_sql_str, p_csv_db_slice):
        """Write broken record to logger"""
        # self.logger.critical( p_err )
        for row in p_csv_db_slice:
            try:
                self.cur.execute(p_sql_str, row)
            except Exception:
                self.logger.warning(f"{p_sql_str}\n{row}\nForced program termination")
                sys.exit()
            else:
                self.conn.commit()
            pass
        pass

    def export_to_csv(
        self,
        p_csv_path,
        p_table_name,
        p_delimeter="|",
        p_strip_chars="",
        p__vol_size=0,
        p_sql_query="",
    ):
        """Export a table to a csv file

        Parameters
        - p_csv_path         - Path name of the file to be exported
        - p_table_name = ''  - Table name to export
        - p_delimeter = '|'  - Field delimiter to use
        - p_strip_chars = '' - characters to strip from text
        - p__vol_size = 0    - Create a multiple volume export. p__vol_size is
                             the number of records per file.  0 will create
                             only one volume.
        """

        def multi_volume_export(p_csv_path, p__vol_size):
            """Create multiple volumes in path with p__vol_size records

            Parameters
            - p_csv_path         - Path name of the file to be exported
            - p__vol_size = 0    - Create a multiple volume export. p__vol_size is
                                 the number of records per file.  0 will create
                                 only one volume.
            """
            file_name_list = []
            header = p_delimeter.join(self.db_structure[p_table_name])
            prim_key_sql_str = "SELECT "
            select_header = self.quote_identifier_list(self.db_structure[p_table_name])
            all_sql_str = "SELECT " + select_header + " FROM " + self.quote_identifier(p_table_name) + " WHERE "
            for i, field in enumerate(self.db_structure[p_table_name]):
                if self.db_structure[p_table_name][field]["Params"]["PrimaryKey"][0] == "Y":
                    prim_key_sql_str += self.quote_identifier(field) + ", "
                    all_sql_str += self.quote_identifier(field) + " = " + self.param_placeholder() + " and "
            prim_key_sql_str = prim_key_sql_str[:-2] + " FROM " + self.quote_identifier(p_table_name)
            all_sql_str = all_sql_str[:-5]
            print(f"Collecting {p_table_name} table records")
            self.cur.execute(prim_key_sql_str)
            prim_key_res = self.cur.fetchall()
            vol_cntr = 1
            # curr_vol_size = p__vol_size
            list_len = len(prim_key_res)
            msg = bm.display(
                f"Export records table = {p_table_name} ({list_len})",
                p_len=self.msg_width,
            )
            rec_cntr = 0
            pfx = displayfx.DisplayFx(list_len, p_msg=msg, p_bar_len=self.bar_len)
            csv_file = None
            for i, pkeys_rec in enumerate(prim_key_res):
                if rec_cntr == 0:
                    if rec_cntr == 0 and vol_cntr > 1:
                        csv_file.close()
                        # if list_len - ((vol_cntr - 1) * p__vol_size) < p__vol_size:
                        # curr_vol_size = list_len - ((vol_cntr - 1) * p__vol_size)
                    if vol_cntr == 1:
                        csv_vol_path = p_csv_path
                    else:
                        csv_vol_path = p_csv_path[:-4] + f"{vol_cntr:0>2}" + p_csv_path[-4:]
                    file_name_list.append(os.path.split(csv_vol_path))
                    csv_file = open(csv_vol_path, "w+")
                    csv_file.write(header + "\n")
                self.cur.execute(all_sql_str, pkeys_rec)
                row_res = self.cur.fetchall()[0]
                csv_row = ""
                for j, field in enumerate(row_res):
                    if field is None:
                        field = "NULL"
                    if j in self.char_fields[p_table_name]:
                        csv_row += '"' + str(field) + '"' + p_delimeter
                    else:
                        csv_row += str(field) + p_delimeter
                for char in p_strip_chars:
                    csv_row.replace(char, "")
                csv_file.write(csv_row[:-1] + "\n")
                if rec_cntr == p__vol_size:
                    rec_cntr = 0
                    vol_cntr += 1
                else:
                    rec_cntr += 1
                pfx.update(i)
            csv_file.close()
            return file_name_list

        # end multi_volume_export

        def single_volume_export(p_csv_path, p_sql_query):
            """Create single volume in path with p__vol_size records

            Parameters
            - p_csv_path          - Path name of the file to be exported
            """
            header = ""
            file_name_list = []
            file_name_list.append(os.path.split(p_csv_path))
            if not p_sql_query:
                header = p_delimeter.join(self.db_structure[p_table_name])
                sql_str = (
                    "SELECT "
                    + self.quote_identifier_list(self.db_structure[p_table_name])
                    + " FROM "
                    + self.quote_identifier(p_table_name)
                )
            else:
                header = p_delimeter.join(p_sql_query[0])
                sql_str = p_sql_query[1]
            csv_file = open(p_csv_path, "w+")
            csv_file.write(header + "\n")
            print(f"Collecting {p_table_name} table records")
            self.cur.execute(sql_str)
            table_res = self.cur.fetchall()
            # cntr = 0
            list_len = len(table_res)
            msg = bm.display(
                f"Export records table = {p_table_name} ({list_len})",
                p_len=self.msg_width,
            )
            dfx = displayfx.DisplayFx(list_len, p_msg=msg, p_bar_len=self.bar_len)
            for i, row in enumerate(table_res):
                csv_row = ""
                for j, field in enumerate(row):
                    # if not field:
                    if field is None:
                        field = "NULL"
                    if j in self.char_fields[p_table_name]:
                        csv_row += '"' + str(field) + '"' + p_delimeter
                    else:
                        csv_row += str(field) + p_delimeter
                for char in p_strip_chars:
                    csv_row.replace(char, "")
                csv_file.write(csv_row[:-1] + "\n")
                dfx.update(i)
            csv_file.close()
            return file_name_list

        # end single_volume_export

        file_name_list = None
        try:
            self.cur.execute("SELECT COUNT(*) FROM " + self.quote_identifier(p_table_name))
        except self.db_error as err:
            print(f"Err mesg: {err.msg}")
            print(err.msg)
        else:
            count_rec_res = self.cur.fetchall()[0][0]
            if p__vol_size > 0 and count_rec_res > p__vol_size and not p_sql_query:
                file_name_list = multi_volume_export(p_csv_path, p__vol_size)
            else:
                file_name_list = single_volume_export(p_csv_path, p_sql_query)
            # success = True
        return file_name_list

    def get_db_field_types(self):
        """Populate field type lookup lists used during import/export."""
        for p_table_name in self.db_structure:
            self.char_fields[p_table_name] = []
            self.non_char_fields[p_table_name] = []
            for field in self.db_structure[p_table_name]:
                if (
                    self.db_structure[p_table_name][field]["Type"][0] == "char"
                    or self.db_structure[p_table_name][field]["Type"][0] == "varchar"
                ):
                    self.char_fields[p_table_name].append(field)
                else:
                    self.non_char_fields[p_table_name].append(field)

    def import_csv(
        self,
        p_table_name,
        p_csv_file_name="",
        p_key="",
        p_header="",
        p_del_head=False,
        p_csv_db="",
        p_csv_corr_str_file_name="",
        p_vol_type="Multi",
        p_verbose=False,
        p_replace=False,
    ):
        """Import CSV rows into a database table.

        Parameters
        - p_table_name
          Table name to import the CSV data into
        - p_csv_file_name = ''
          CSV file name. Empty when rows are supplied in p_csv_db
        - p_key = ''
          Key used to insert in table
        - p_header = ''
          - Header of CSV files
        - p_del_head = ''
          - Delete the header
        - p_csv_db = ''
          - Contains the CSV rows directly and makes p_csv_file_name obsolete.
        - p_csv_corr_str_file_name = ''
          - File containing string replacements to apply before parsing
        - p_vol_type = 'Multi'
          - Multi - Read multiple volume
          - Single - Read single file
        - p_verbose = False
          - Determine whether progress output is written to screen
        - debug = False
          - Switch debug output on
        - p_replace = False
          - False - INSERT into database
          - True - REPLACE into database
        """

        def import_volume(p_csv_db, p_header, p_verbose):
            """Prepare and write one in-memory CSV volume to the active table."""

            def convert_str_to_none(p_non_char_fields_idx, p_csv_db):
                """Convert blank non-character values to None before insert."""
                rows_to_del = []
                csv_db = p_csv_db
                list_len = len(csv_db)
                msg = bm.display(
                    f"Convert empty strings to None ({list_len})",
                    p_len=self.msg_width,
                )
                dfx = displayfx.DisplayFx(
                    list_len,
                    p_msg=msg,
                    p_verbose=p_verbose,
                    p_bar_len=self.bar_len,
                )
                for row_idx, row in enumerate(csv_db):
                    found_none = False
                    t_tow = list(csv_db[row_idx])
                    for field in p_non_char_fields_idx:
                        if t_tow[field] == "":
                            t_tow[field] = None
                            found_none = True
                    if found_none:
                        csv_db.append(tuple(t_tow))
                        rows_to_del.append(row_idx)
                    dfx.update(row_idx)
                list_len = len(rows_to_del)
                msg = bm.display(f"Cleanup ({list_len})", p_len=self.msg_width)
                dfx = displayfx.DisplayFx(
                    list_len,
                    p_msg=msg,
                    p_verbose=p_verbose,
                    p_bar_len=self.bar_len,
                )
                for i, row_idx in enumerate(sorted(rows_to_del, reverse=True)):
                    del csv_db[row_idx]
                    dfx.update(i)
                print()
                return csv_db

            # end convert_str_to_none

            def find_non_char_field_idx(p_csv_db):
                """Find non-character field indexes that may contain empty strings."""
                non_char_fields_idx = []
                for header_field_name in self.non_char_fields[p_table_name]:
                    for row_idx, data_field_name in enumerate(p_csv_db[0]):
                        if header_field_name == data_field_name:
                            non_char_fields_idx.append(row_idx)
                            break
                return non_char_fields_idx

            # end find_non_char_field_idx

            def fix_dates(p_csv_db, p_table_name, p_header):
                """Normalize date and datetime values before insert."""
                c_field_idx = 0
                c_field_type = 1
                csv_db = p_csv_db
                idx = []
                # date_time_idx = []
                for i, field in enumerate(p_header):
                    if field in self.db_structure[p_table_name]:
                        if self.db_structure[p_table_name][field]["Type"][0] == "date":
                            idx.append([i, "date"])
                        elif self.db_structure[p_table_name][field]["Type"][0] == "datetime":
                            idx.append([i, "datetime"])
                if idx:
                    for i, row in enumerate(csv_db[1:]):
                        for field_det in idx:
                            if row[field_det[c_field_idx]] is not None:
                                if field_det[c_field_type] == "date" and not isinstance(
                                    row[field_det[c_field_idx]], datetime.date
                                ):
                                    fixed_date = fixdate.FixDate(
                                        # self.logger_name,
                                        row[field_det[c_field_idx]],
                                        p_out_format="%Y/%m/%d",
                                    ).date_str
                                    if isinstance(csv_db[i + 1], tuple):
                                        csv_db[i + 1] = (
                                            csv_db[i + 1][: field_det[c_field_idx]]
                                            + (fixed_date,)
                                            + csv_db[i + 1][field_det[c_field_idx] + 1 :]
                                        )
                                    if isinstance(csv_db[i + 1], list):
                                        csv_db[i + 1] = (
                                            csv_db[i + 1][: field_det[c_field_idx]]
                                            + [fixed_date]
                                            + csv_db[i + 1][field_det[c_field_idx] + 1 :]
                                        )
                                    pass
                                    # elif field_det[ c_field_type ] == 'datetime' and isinstance( row[ field_det[ c_field_idx ]], datetime.datetime ):
                                    #     date, time = row[ field_det[ c_field_idx ]].split( ' ' )
                                    #     date, time = row[ field_det[ c_field_idx ]].split( ' ' )
                                    # fixed_date = fixdate.FixDate( self.logger_name, date, p_out_format = '%Y/%m/%d').date_str
                                    #     if isinstance( csv_db[ i + 1 ], tuple ):
                                    #         csv_db[ i + 1 ] = csv_db[ i + 1 ][:field_det[ c_field_idx ]] + ( '{} {}'.format( fixed_date, time ), ) \
                                    #                                            + csv_db[ i + 1 ][ field_det[ c_field_idx ] + 1:]
                                    #     if isinstance( csv_db[ i + 1 ], list ):
                                    #         csv_db[ i + 1 ] = csv_db[ i + 1 ][:field_det[ c_field_idx ]] + [ '{} {}'.format( fixed_date, time ) ] \
                                    #                                            + csv_db[ i + 1 ][ field_det[ c_field_idx ] + 1:]
                                    pass
                    pass
                return csv_db

            # end fix_dates

            def write_to_table(p_csv_db):
                """Write prepared rows to the destination table."""
                i = 1
                j = 0  # In case batch size is more than all records
                list_len = len(p_csv_db)
                msg = bm.display(
                    f"Populate table = {p_table_name} ({list_len})",
                    p_len=self.msg_width,
                )
                dfx = displayfx.DisplayFx(
                    list_len,
                    p_msg=msg,
                    p_verbose=p_verbose,
                    p_bar_len=self.bar_len,
                )
                sql_str = self.build_insert_sql(p_table_name, header, p_replace=p_replace)
                for j in range(self.batch_size, list_len, self.batch_size):
                    try:
                        self.cur.executemany(sql_str, p_csv_db[i : j + 1])
                    except self.db_error as err:
                        self.logger.error(err)
                        self.conn.rollback()
                        self._err_broken_rec(sql_str, p_csv_db[i : j + 1])
                    finally:
                        self.conn.commit()
                        i = j + 1
                        dfx.update(j)
                # New needs to be tested. Writing the records 1 by 1?
                # self.logger.debug('{}'.format(p_csv_db[j + 1 : len(p_csv_db)]))
                self.cur.executemany(sql_str, p_csv_db[j + 1 : len(p_csv_db)])
                self.conn.commit()
                if j < list_len:
                    dfx.update(list_len)
                pass

            # end write_to_table

            csv_db = p_csv_db
            if p_header:
                header = p_header
            else:
                header = csv_db[0]
            csv_db = fix_dates(csv_db, p_table_name, header)
            if self.non_char_fields[p_table_name]:
                csv_db = convert_str_to_none(find_non_char_field_idx(p_csv_db), p_csv_db)
            write_to_table(csv_db)
            pass

        # end import_volume

        def import_single_volume(p_csv_db, p_header, p_verbose):
            """Import one supplied in-memory CSV volume."""
            success = False
            # if not p_csv_db:
            #     if os.path.isfile(p_csv_file_name):
            #         csv_file_data = csvwrpr.CsvWrpr(
            #             self.logger_name,
            #             p_csv_file_name=p_csv_file_name,
            #             p_key1=p_key,
            #             p_header=p_header,
            #             p_del_head=p_del_head,
            #             p_struc_type=(),
            #             p_csv_corr_str_file_name=p_csv_corr_str_file_name,
            #             p_replace_header=replace_header,
            #             p_verbose=p_verbose,
            #             p_bar_len=self.bar_len,
            #             p_msg_width=self.msg_width,
            #         )
            #         csv_db = csv_file_data.csv_db
            if p_csv_db:
                import_volume(p_csv_db, p_header, p_verbose)
                success = True
            return success

        # end import_single_volume

        def import_multi_volume(p_verbose, p_header):
            """Import numbered CSV files until the next volume is missing."""
            vol_cntr = 1
            success = False
            vol_csv_file_name = p_csv_file_name
            while os.path.isfile(vol_csv_file_name):
                # x = csvwrpr.csv
                csv_file_data = csvwrpr.CsvWrpr(
                    vol_csv_file_name,
                    p_key1=p_key,
                    p_header=p_header,
                    p_del_head=p_del_head,
                    p_struc_type=(),
                    p_csv_corr_str_file_name=p_csv_corr_str_file_name,
                    p_replace_header=replace_header,
                    p_verbose=p_verbose,
                    p_msg_width=self.msg_width,
                    p_bar_len=self.bar_len,
                    p_match_nr_of_fields=True,
                )
                csv_db = csv_file_data.csv_db
                if csv_db:
                    import_volume(csv_db, p_header, p_verbose)
                    success = True
                vol_cntr += 1
                vol_csv_file_name = p_csv_file_name[:-4] + f"{vol_cntr:0>2}" + p_csv_file_name[-4:]
            if not success:
                log_str = f"No data to import from {vol_csv_file_name}"
                self.logger.warning(log_str)
            return success

        # end import_multi_volume

        if p_header:
            replace_header = True
        else:
            replace_header = False
        if p_vol_type == "Single" or p_csv_db:
            success = import_single_volume(p_csv_db, p_header, p_verbose)
        elif p_vol_type == "Multi":
            success = import_multi_volume(p_verbose, p_header)
        else:
            success = False
        return success

    def import_and_split_csv(
        self,
        p_split_struct,
        p_data,
        p_header="",
        p_insert_header=False,
        p_verbose=False,
        p_debug=False,
    ):
        """Split CSV rows into one or more destination table imports.

        Parameters
        - p_split_struct - { 'Seq01': { 'TableName': Desttable_name1, 'Key': TableKey, 'Replace': False, 'Flds': [[ OrgField1, DestField1, [ Command, Parm1, Parm2, Parm3 ]],
                                                                                                                      [ OrgField2, DestField2, [ Command, Parm1, Parm2, Parm3 ]],
                                                                                                                      [ ...                                             ]]},
                            'Seq02': { 'TableName': Desttable_name2, 'Key': TableKey, 'Replace': False, 'Flds': [[ OrgField1, DestField1, [ Command, Parm1, Parm2, Parm3 ]],
                                                                                                                      [ OrgField2, DestField3, [ Command, Parm1, Parm2, Parm3 ]],
                                                                                                                      [ ...                                             ]]},
                          ...                                                                                                                        }
          - SeqNN:               Any iterate sequence to indicate the various tables the csv file should be split into ( seq01, seq02, seq03, ...)
          - table_name (str):     Mandatory key word (in the python dict structure) to indicate the table name in the database
          - Desttable_name (str): The name of the table in the database to populate
          - Key (str):           Mandatory key word (in the python dict structure) to indicate the primary key field of the table
          - TableKey (str):      Destination table primary key
          - Replace (boolean):   Either use REPLACE or INSERT SQL statement to add records to the table.  INSERT will cause
                                 a failure when the record to be added is a duplicate.
          - Fields (str):        Mandatory key word (in the python dict structure) to list the fields in the table
          - OrgFieldN (str):     Field name from the CSV file to copy to the database table
          - DestFieldN (str):    Destination field where OrgFieldN will be copied into
          - Command (int):       0 = Copy OrgFieldN to DestFieldN as is
                                     Parm1 = Truncate OrgFieldN at Parm1 if it is a string and insert into DestFieldN.  0 for no truncation.  Non 'str' will not be truncated
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
                                     Parm3 = Insert a default value if the original field matched the list.
                                           = [ list, Def ]
                                 1 = Insert fixed value into DestFieldN
                                     Parm1 = The fixed value to insert into DestFieldN
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
                                 2 = Split OrgFieldN by ',' and insert the n'th occurrence defined in Parm1 into DestFieldN
                                     Parm1 = The n'th occurrence from split of OrgFieldN to insert into DestFieldN
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
                                 3 = Combine the "year" value in OrgFieldN with "01/01" and insert into DestFieldN
                                     Parm1 = Date
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
                                 4 = Value of OrgFieldN will be looked up in a dict and inserted into DestFieldN
                                     Parm1 = Lookup table in form of dict
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
                                 5 = Copy sub string from OrgFieldN into DestFieldN
                                     Parm1 = List with start and end value to copy from OrgFieldN
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
                                 6 = Insert auto number into DestFieldN
                                     Parm1 = Start with the value and add 1 with each iteration
                                     Parm2 = True if you do not want to add the row if the result is empty, else False
        - p_data
        - p_header = ''
        """
        if isinstance(p_data, list):
            csv_file_data = p_data.copy()
        elif isinstance(p_data, str):
            csv_file_data = csvwrpr.CsvWrpr(
                self.logger_name,
                p_data,
                "",
                p_struc_type=(),
                p_header=p_header,
                p_verbose=p_verbose,
                p_bar_len=self.bar_len,
                p_msg_width=self.msg_width,
            ).csv_db
        else:
            csv_file_data = ()
            print("Incorrect data structure")
        if p_insert_header and p_header:
            header = [tuple(p_header)]
            csv_file_data = header + csv_file_data
        for seq in p_split_struct:
            table = p_split_struct[seq]["TableName"]
            new_header = ()
            field_list = []
            field_config = []
            for field in p_split_struct[seq]["Flds"]:
                field_config = []
                t_str = (field[1],)
                new_header = new_header + t_str
                if field[0] != "None":
                    field_config.append(csv_file_data[0].index(field[0]))
                else:
                    field_config.append(-1)
                field_config = field_config + field[2]
                field_list.append(field_config)
            newcsv_db = [new_header]
            table_len = len(csv_file_data[1:])
            if isinstance(p_data, list):
                msg = bm.display(
                    f"Split data to {table} ({table_len})",
                    p_len=self.msg_width,
                )
            else:
                msg = bm.display(
                    f"Split {os.path.split(p_data)[1]} to {table} ({table_len})",
                    p_len=self.msg_width,
                )
            c_field_nr = 0
            c_cmd_opy = 0
            c_cmd_insert = 1
            c_cmd_split = 2
            c_cmd_date = 3
            c_cmd_look_up = 4
            c_cmd_copy_sub = 5
            c_cmd_auto_inc = 6
            c_no_trunc = 0
            c_cmd = 1
            c_parm1 = 2
            c_parm2 = 3
            c_parm3 = 4
            c_parm3_rep_str = 0
            c_parm3_def_str = 1
            dfx = displayfx.DisplayFx(
                len(csv_file_data[1:]),
                p_msg=msg,
                p_verbose=False,
                p_bar_len=self.bar_len,
            )
            for i, row in enumerate(csv_file_data[1:]):
                new_row = ()
                add_row = True
                for field_det in field_list:
                    t_str = ""
                    if field_det[c_cmd] == c_cmd_opy:  # Copy / duplicate
                        if field_det[c_parm1] == c_no_trunc or isinstance(row[field_det[c_field_nr]], str):
                            t_str = row[field_det[c_field_nr]]
                        else:
                            t_str = row[field_det[c_field_nr]][0 : field_det[c_parm1]]
                        if len(field_det) > 4:
                            if t_str in field_det[c_parm3][c_parm3_rep_str]:
                                t_str = field_det[c_parm3][c_parm3_def_str]
                    elif field_det[c_cmd] == c_cmd_insert:  # Insert fixed value
                        t_str = field_det[c_parm1]
                    elif field_det[c_cmd] == c_cmd_split:  # Insert fixed value from split field
                        if row[field_det[c_field_nr]].count(",") >= field_det[c_parm1]:
                            t_str = row[field_det[c_field_nr]].split(",")[field_det[c_parm1]]
                        else:
                            t_str = ""
                    elif field_det[c_cmd] == c_cmd_date:  # Insert special value
                        if field_det[c_parm1] == "Date":
                            t_str = row[field_det[c_field_nr]] + "/01/01"
                        else:
                            print("my_sql_db: 143 - Unknown value -", field_list[1])
                    elif field_det[c_cmd] == c_cmd_look_up:  # Replace with look up value
                        if row[field_det[c_field_nr]] in field_det[c_parm1]:
                            t_str = field_det[c_parm1][row[field_det[0]]]
                    elif field_det[c_cmd] == c_cmd_copy_sub:  # Replace with substring from original field
                        t_str = row[field_det[c_field_nr]][field_det[c_parm1][0] : field_det[c_parm1][1]]
                    elif field_det[c_cmd] == c_cmd_auto_inc:  # Insert auto number
                        t_str = field_det[c_parm1]
                        field_det[c_parm1] += 1
                    if isinstance(t_str, str):
                        t_str = t_str.strip()
                    new_row = new_row + (t_str,)
                    if field_det[c_parm2] and not t_str:
                        add_row = add_row and False
                        break
                if add_row:
                    newcsv_db.append(new_row)
                dfx.update(i)
            self.import_csv(
                p_table_name=table,
                p_csv_db=newcsv_db,
                p_header=new_header,
                p_verbose=p_verbose,
                p_replace=p_split_struct[seq]["Replace"],
            )

    @classmethod
    def from_sqlalchemy_metadata(cls, p_sqlalchemy_metadata):
        """Convert SQLAlchemy metadata into the legacy SqlDbWrpr schema structure."""
        if not getattr(p_sqlalchemy_metadata, "tables", None):
            raise SchemaSourceError("SQLAlchemy metadata does not define any tables")
        db_structure = {}
        for table in p_sqlalchemy_metadata.sorted_tables:
            db_structure[table.name] = cls._table_to_legacy_structure(table)
        return db_structure

    @staticmethod
    def resolve_db_structure(p_db_structure=None, p_sqlalchemy_base=None, p_sqlalchemy_metadata=None):
        """Resolve schema from explicit config, SQLAlchemy metadata, or declarative base."""
        if p_db_structure:
            return p_db_structure
        if p_sqlalchemy_metadata is None and p_sqlalchemy_base is not None:
            p_sqlalchemy_metadata = getattr(p_sqlalchemy_base, "metadata", None)
        if p_sqlalchemy_metadata is not None:
            return SQLDbWrpr.from_sqlalchemy_metadata(p_sqlalchemy_metadata)
        raise SchemaSourceError("Supply p_db_structure, p_sqlalchemy_metadata, or p_sqlalchemy_base")

    @staticmethod
    def _action_to_legacy_code(p_action):
        """Convert SQLAlchemy foreign-key actions to legacy codes."""
        if p_action is None:
            return "N"
        action = p_action.upper().replace(" ", "_")
        action_map = {
            "CASCADE": "C",
            "RESTRICT": "R",
            "SET_DEFAULT": "D",
            "SET_NULL": "N",
        }
        return action_map[action]

    @staticmethod
    def _build_default_field_params():
        """Build the legacy default parameter block for a field."""
        return {
            "PrimaryKey": ["", ""],
            "FKey": [],
            "Index": [],
            "NN": "",
            "B": "",
            "UN": "",
            "ZF": "",
            "AI": "",
            "G": "",
            "DEF": "",
        }

    @staticmethod
    def _column_type_to_legacy(p_column):
        """Convert a SQLAlchemy column type to the legacy type list."""
        column_type = p_column.type
        type_name = column_type.__class__.__name__.lower()
        if "biginteger" in type_name:
            return ["bigint"]
        if "boolean" in type_name:
            return ["boolean"]
        if "char" in type_name or "string" in type_name or "varchar" in type_name:
            if getattr(column_type, "length", None) is None:
                return ["varchar"]
            if type_name == "char":
                return ["char", column_type.length]
            return ["varchar", column_type.length]
        if type_name == "date":
            return ["date"]
        if "datetime" in type_name:
            return ["datetime"]
        if "integer" in type_name:
            return ["int"]
        if "largebinary" in type_name or "blob" in type_name or "binary" in type_name:
            return ["blob"]
        if "numeric" in type_name or "decimal" in type_name:
            precision = getattr(column_type, "precision", None)
            scale = getattr(column_type, "scale", None)
            if precision is not None and scale is not None:
                return ["decimal", precision, scale]
            return ["decimal"]
        if type_name == "time":
            return ["time"]
        return [type_name]

    @staticmethod
    def _column_to_legacy_field(p_column):
        """Convert a SQLAlchemy column to a legacy field definition."""
        field_type = SQLDbWrpr._column_type_to_legacy(p_column)
        params = SQLDbWrpr._build_default_field_params()
        if not p_column.nullable or p_column.primary_key:
            params["NN"] = "Y"
        if p_column.autoincrement is True:
            params["AI"] = "Y"
        if p_column.default is not None and getattr(p_column.default, "is_scalar", False):
            params["DEF"] = str(p_column.default.arg)
        if field_type[0] == "blob":
            params["B"] = "Y"
        return {
            "Type": field_type,
            "Params": params,
            "Possible Values": "",
            "Comment": p_column.comment or "",
        }

    @staticmethod
    def _set_foreign_keys(p_table, p_table_structure):
        """Set legacy foreign-key metadata on converted table fields."""
        for fkey_nr, constraint in enumerate(p_table.foreign_key_constraints, start=1):
            elements = list(constraint.elements)
            for field_order, element in enumerate(elements, start=1):
                p_table_structure[element.parent.name]["Params"]["FKey"] = [
                    fkey_nr,
                    field_order,
                    element.column.table.name,
                    element.column.name,
                    SQLDbWrpr._action_to_legacy_code(constraint.ondelete),
                    SQLDbWrpr._action_to_legacy_code(constraint.onupdate),
                ]

    @staticmethod
    def _set_indexes(p_table, p_table_structure):
        """Set legacy index metadata on converted table fields."""
        indexes = sorted(p_table.indexes, key=lambda p_index: p_index.name or "")
        for idx_nr, index in enumerate(indexes, start=1):
            for field_order, column in enumerate(index.columns, start=1):
                p_table_structure[column.name]["Params"]["Index"] = [
                    idx_nr,
                    field_order,
                    "A",
                    "U" if index.unique else "",
                ]

    @staticmethod
    def _set_primary_key(p_table, p_table_structure):
        """Set legacy primary-key metadata on converted table fields."""
        for column in p_table.primary_key.columns:
            p_table_structure[column.name]["Params"]["PrimaryKey"] = ["Y", "A"]

    @staticmethod
    def _table_to_legacy_structure(p_table):
        """Convert a SQLAlchemy table to the legacy table structure."""
        table_structure = {}
        for column in p_table.columns:
            table_structure[column.name] = SQLDbWrpr._column_to_legacy_field(column)
        SQLDbWrpr._set_foreign_keys(p_table, table_structure)
        SQLDbWrpr._set_indexes(p_table, table_structure)
        SQLDbWrpr._set_primary_key(p_table, table_structure)
        return table_structure

    @staticmethod
    def _print_err_msg(p_err, p_msg=""):
        """Print a formatted database error message."""
        msg = p_msg
        if p_msg:
            msg = f"{p_msg}\n"
        print(
            bm.error(
                "{}Err No:\t\t{}\nSQL State:\t{}\nErr Msg:\t{}\nSystem terminated...".format(
                    msg, p_err.errno, p_err.sqlstate, p_err.msg
                )
            )
        )
        pass


class MySQL(SQLDbWrpr):
    """Wrapper for MySQL databases."""

    def __init__(
        self,
        p_host_name="localhost",
        p_user_name="",
        p_password="",
        p_user_rights=False,
        p_recreate_db=False,
        p_db_name=None,
        p_db_structure=None,
        p_sqlalchemy_base=None,
        p_sqlalchemy_metadata=None,
        p_batch_size=10000,
        p_bar_len=50,
        p_msg_width=50,
        p_verbose=False,
        p_admin_username=False,
        p_admin_user_password=False,
        p_db_port="3306",
        # p_ssl_ca=None,
        # p_ssl_key=None,
        # p_ssl_cert=None
        **kwargs,
    ):
        """Connect to MySQL and optionally recreate or select the target database."""
        super().__init__(
            p_host_name=p_host_name,
            p_user_name=p_user_name,
            p_password=p_password,
            p_db_name=p_db_name,
            p_recreate_db=p_recreate_db,
            p_db_structure=p_db_structure,
            p_sqlalchemy_base=p_sqlalchemy_base,
            p_sqlalchemy_metadata=p_sqlalchemy_metadata,
            p_batch_size=p_batch_size,
            p_bar_len=p_bar_len,
            p_msg_width=p_msg_width,
            p_verbose=p_verbose,
            p_db_port=p_db_port,
            # p_ssl_ca=p_ssl_ca,
            # p_ssl_key=p_ssl_key,
            # p_ssl_cert=p_ssl_cert,
        )
        try:
            # import pdb;pdb.set_trace()
            self.conn = mysql.connector.connect(
                host=self.host_name,
                user=self.user_name,
                password=self._password,
                database=None,
                auth_plugin="mysql_native_password",
                port=self.db_port,
                # ssl_ca=self.ssl_ca,
                # ssl_key=self.ssl_key,
                # ssl_cert=self.ssl_cert
                **kwargs,
            )
            self.cur = self.conn.cursor()
        except self.db_error as err:
            print(
                bm.error(
                    f"Error {err}:'({self.user_name}'@'{self.host_name}')",
                )
            )
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print(bm.error(f"User '{self.user_name}'@'{self.host_name}' does not exist\nAtempt to create it..."))
                if p_admin_username and p_admin_user_password and p_user_rights:
                    try:
                        self.conn = mysql.connector.connect(
                            host=self.host_name,
                            user=p_admin_username,
                            password=p_admin_user_password,
                            database=None,
                            auth_plugin="mysql_native_password",
                            port=self.db_port,
                        )
                    except self.db_error as err:
                        self._print_err_msg(
                            err,
                            "Admin user name and/or password not supplied or incorrect",
                        )
                    if self.conn.is_connected():
                        self.cur = self.conn.cursor()
                        self.create_users(
                            [p_admin_username, p_admin_user_password],
                            [[p_user_name, p_password]],
                        )
                        self.grant_rights([p_admin_username, p_admin_user_password], [p_user_rights])
                    else:
                        print(bm.error("Could not connect\nSystem terminated"))
                        sys.exit()
                else:
                    self._print_err_msg(
                        err,
                        "User name and/or password and/or user access rights not supplied or incorrect",
                    )
                    sys.exit()
            self.close()
        if not self.conn.is_connected():
            self.conn = mysql.connector.connect(
                host=self.host_name,
                user=self.user_name,
                password=self._password,
                database=None,
                auth_plugin="mysql_native_password",
            )
            self.cur = self.conn.cursor()
        if self.re_create_db:
            if self.create_db():
                self.create_tables()
        elif self.db_name:
            self.conn.cmd_init_db(self.db_name)
            self.conn.commit()
        self.success = True
        pass

    def create_users(self, p_admin_user, p_new_users):
        """Create MySQL users that do not already exist."""
        c_user_name = 0
        self.cur.execute("SELECT User, Host FROM mysql.user")
        curr_users = self.cur.fetchall()
        for user in p_new_users:
            user_key = (user[c_user_name], self.host_name)
            if user_key not in curr_users:
                try:
                    self.cur.execute(
                        "CREATE USER IF NOT EXISTS '{}'@'{}' IDENTIFIED BY '{}'".format(
                            user[0], self.host_name, user[1]
                        )
                    )
                except self.db_error as err:
                    self._print_err_msg(err, "Could not create user")
                    self.close()
                    sys.exit()
                self.conn.commit()
        self.success = True

    def delete_users(self, p_admin_user, p_del_users):
        """Delete MySQL users that exist."""
        c_user_name = 0
        c_host = 2
        self.cur.execute("SELECT User FROM mysql.user")
        curr_users = [x[0] for x in self.cur.fetchall()]
        for user in p_del_users:
            if user[c_user_name] in curr_users:
                try:
                    self.cur.execute(f"DROP USER '{user[c_user_name]}'@'{user[c_host]}'")
                except self.db_error as err:
                    self._print_err_msg(err, "Could not delete user")
                    self.close()
                    sys.exit()
                self.conn.commit()
        self.success = True

    def grant_rights(self, p_admin_user, p_user_rights):
        """Grant configured MySQL rights to users."""
        c_user_name = 0
        c_host = 1
        c_db = 2
        c_table = 3
        c_rights = 4
        for right in p_user_rights:
            try:
                sql_str = "GRANT {} ON {}.{} TO '{}'@'{}'".format(
                    ",".join(right[c_rights:]),
                    right[c_db],
                    right[c_table],
                    right[c_user_name],
                    right[c_host],
                )
                self.cur.execute(sql_str)
                self.conn.commit()
                sql_str = "GRANT {} ON {}.{} TO '{}'@'{}' WITH GRANT OPTION".format(
                    ",".join(right[c_rights:]),
                    right[c_db],
                    right[c_table],
                    right[c_user_name],
                    right[c_host],
                )
                self.cur.execute(sql_str)
                self.conn.commit()
            except self.db_error as err:
                self._print_err_msg(err)
                self.close()
                sys.exit()
        self.success = True


class PostgreSQL(SQLDbWrpr):
    """Wrapper for PostgreSQL databases."""

    def __init__(
        self,
        p_host_name="localhost",
        p_user_name="",
        p_password="",
        p_recreate_db=False,
        p_db_name=None,
        p_db_structure=None,
        p_sqlalchemy_base=None,
        p_sqlalchemy_metadata=None,
        p_batch_size=10000,
        p_bar_len=50,
        p_msg_width=50,
        p_verbose=False,
        p_db_port="5432",
        p_maintenance_db="postgres",
        **kwargs,
    ):
        """Create a PostgreSQL wrapper and optionally recreate the target database."""
        super().__init__(
            p_host_name=p_host_name,
            p_user_name=p_user_name,
            p_password=p_password,
            p_db_name=p_db_name,
            p_recreate_db=p_recreate_db,
            p_db_structure=p_db_structure,
            p_sqlalchemy_base=p_sqlalchemy_base,
            p_sqlalchemy_metadata=p_sqlalchemy_metadata,
            p_batch_size=p_batch_size,
            p_bar_len=p_bar_len,
            p_msg_width=p_msg_width,
            p_verbose=p_verbose,
            p_db_port=p_db_port,
        )
        self.db_error = psycopg.Error
        self.identifier_quote = '"'
        self.inline_indexes = False
        self.maintenance_db = p_maintenance_db
        self._connection_kwargs = kwargs
        connect_db = self.maintenance_db if self.re_create_db else self.db_name
        self.conn = self._connect(connect_db)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        if self.re_create_db:
            if self.create_db():
                self.create_tables()
        self.success = True

    def build_column_sql(self, p_field_name, p_field_type, p_field_params, p_field_comment):
        """Build PostgreSQL SQL for one column in a CREATE TABLE statement."""
        sql_str = f"{self.quote_identifier(p_field_name)} {self.render_field_type(p_field_type, p_field_params)}"
        if p_field_params["NN"] == "Y" and p_field_params["AI"] != "Y":
            sql_str += " NOT NULL"
        if p_field_params["DEF"]:
            sql_str += self.render_default_sql(p_field_type, p_field_params["DEF"])
        return sql_str

    def build_index_sql(self, p_table_name, p_idx_name, p_idx_fields, p_unique=False):
        """Build a PostgreSQL CREATE INDEX statement."""
        unique_sql = "UNIQUE " if p_unique else ""
        index_fields = []
        for field_det in p_idx_fields:
            index_fields.append(f"{self.quote_identifier(field_det[0])} {self.sort_order[field_det[2]]}")
        return "CREATE {}INDEX {} ON {} ({})".format(
            unique_sql,
            self.quote_identifier(p_idx_name),
            self.quote_identifier(p_table_name),
            ",".join(index_fields),
        )

    def build_insert_sql(self, p_table_name, p_header, p_replace=False):
        """Build a PostgreSQL INSERT or upsert statement."""
        insert_sql = "INSERT INTO {} ({}) VALUES ({})".format(
            self.quote_identifier(p_table_name),
            ",".join([self.quote_identifier(str(x)) for x in p_header]),
            ",".join([self.param_placeholder() for x in range(len(p_header))]),
        )
        if not p_replace:
            return insert_sql
        primary_key_fields = [
            field_name
            for field_name in self.db_structure[p_table_name]
            if self.db_structure[p_table_name][field_name]["Params"]["PrimaryKey"][0] == "Y"
        ]
        if not primary_key_fields:
            return f"{insert_sql} ON CONFLICT DO NOTHING"
        update_fields = [field_name for field_name in p_header if field_name not in primary_key_fields]
        if not update_fields:
            return f"{insert_sql} ON CONFLICT ({self.quote_identifier_list(primary_key_fields)}) DO NOTHING"
        update_sql = ",".join(
            [
                f"{self.quote_identifier(field_name)} = EXCLUDED.{self.quote_identifier(field_name)}"
                for field_name in update_fields
            ]
        )
        return f"{insert_sql} ON CONFLICT ({self.quote_identifier_list(primary_key_fields)}) DO UPDATE SET {update_sql}"

    def create_db(self):
        """Create the PostgreSQL database according to self.db_structure."""
        self.cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_name,))
        if self.cur.fetchone():
            try:
                self.cur.execute(f"DROP DATABASE {self.quote_identifier(self.db_name)} WITH (FORCE)")
            except self.db_error as err:
                self._print_err_msg(err, "Could not drop the database")
                self.close()
                sys.exit()
        try:
            self.cur.execute(f"CREATE DATABASE {self.quote_identifier(self.db_name)}")
            self.close()
            self.conn = self._connect(self.db_name)
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
        except self.db_error as err:
            self._print_err_msg(err, "Could not create the database")
            self.close()
            sys.exit()
        return True

    def render_default_sql(self, p_field_type, p_default_value):
        """Render a PostgreSQL column default expression."""
        if p_field_type[0] == "varchar" or p_field_type[0] == "char":
            escaped_value = str(p_default_value).replace("'", "''")
            return f" DEFAULT '{escaped_value}'"
        return f" DEFAULT {p_default_value}"

    def render_field_type(self, p_field_type, p_field_params):
        """Render a legacy field type as a PostgreSQL type."""
        field_type = p_field_type[0]
        if p_field_params["AI"] == "Y":
            if field_type == "bigint":
                return "BIGSERIAL"
            return "SERIAL"
        type_map = {
            "bigint": "BIGINT",
            "blob": "BYTEA",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "int": "INTEGER",
            "tinyint": "SMALLINT",
            "time": "TIME",
        }
        if field_type == "varchar" or field_type == "char":
            return f"{field_type.upper()}({str(p_field_type[1])})"
        if field_type == "decimal":
            return f"DECIMAL({str(p_field_type[1])}, {str(p_field_type[2])})"
        return type_map.get(field_type, field_type.upper())

    def _connect(self, p_db_name):
        """Open a PostgreSQL connection."""
        return psycopg.connect(
            host=self.host_name,
            user=self.user_name,
            password=self._password,
            dbname=p_db_name,
            port=self.db_port,
            **self._connection_kwargs,
        )

    def create_users(self, p_admin_user, p_new_users):
        """Create PostgreSQL login roles that do not already exist."""
        c_user_name = 0
        c_password = 1

        self.cur.execute("SELECT rolname FROM pg_roles WHERE rolcanlogin = true")
        curr_users = [row[0] for row in self.cur.fetchall()]

        for user in p_new_users:
            user_name = user[c_user_name]
            password = user[c_password]

            if user_name not in curr_users:
                try:
                    self.cur.execute(
                        f"CREATE USER {self.quote_identifier(user_name)} WITH PASSWORD %s",
                        (password,),
                    )
                except self.db_error as err:
                    self._print_err_msg(err, "Could not create user")
                    self.close()
                    sys.exit()
        self.success = True

    def delete_users(self, p_admin_user, p_del_users):
        """Delete PostgreSQL users that exist."""
        c_user_name = 0

        self.cur.execute("SELECT rolname FROM pg_roles")
        curr_users = [row[0] for row in self.cur.fetchall()]

        for user in p_del_users:
            user_name = user[c_user_name]

            if user_name in curr_users:
                try:
                    self.cur.execute(f"DROP USER {self.quote_identifier(user_name)}")
                except self.db_error as err:
                    self._print_err_msg(err, "Could not delete user")
                    self.close()
                    sys.exit()
        self.success = True

    def grant_rights(self, p_admin_user, p_user_rights):
        """Grant configured PostgreSQL rights to users.

        Expected right format:
        [user_name, host, database, table, right1, right2, ...]
        The host value is ignored because PostgreSQL does not grant privileges
        by user/host pair like MySQL.
        """
        c_user_name = 0
        c_db = 2
        c_table = 3
        c_rights = 4

        for right in p_user_rights:
            try:
                rights_sql = ",".join(right[c_rights:])
                user_sql = self.quote_identifier(right[c_user_name])
                db_sql = self.quote_identifier(right[c_db])
                table_sql = self.quote_identifier(right[c_table])

                if right[c_table] == "*":
                    sql_str = f"GRANT {rights_sql} ON DATABASE {db_sql} TO {user_sql}"
                else:
                    sql_str = f"GRANT {rights_sql} ON TABLE {table_sql} TO {user_sql}"

                self.cur.execute(sql_str)
                self.conn.commit()
            except self.db_error as err:
                self._print_err_msg(err)
                self.close()
                sys.exit()
        self.success = True
