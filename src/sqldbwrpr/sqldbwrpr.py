"""Wrapper for importing CSV and Text files into MySQL and Postgresql.

Only the MySQL implementation is working.  The MSSQL ODBC implementation
is giving me a lot of shit with the connection and I gave up for now to
get it working.
"""

import datetime
import logging
import os
import sys

import csvwrpr
import displayfx
import fixdate
import mysql.connector
import pyodbc
from beetools import msg as bm
from mysql.connector import Error
from mysql.connector import errorcode

# from pathlib import Path


# _PROJ_DESC = __doc__.split("\n")[0]
# _PROJ_PATH = Path(__file__)
# _PROJ_NAME = _PROJ_PATH.stem


class SQLDbWrpr:
    """This module creates a wrapper for the MySql database."""

    def __init__(
        self,
        p_host_name="localhost",
        p_user_name="",
        p_password="",
        p_recreate_db=False,
        p_db_name="",
        p_db_structure=None,
        p_batch_size=10000,
        p_bar_len=50,
        p_msg_width=50,
        p_verbose=False,
        p_db_port="3306",
        p_ssl_ca=None,
        p_ssl_key=None,
        p_ssl_cert=None,
    ):
        """Create database with supplied structure and return a connector to the database

        Parameters
        - p_host_name = Host to connect to
        - p_user_name = User name for connection
        - p_password = paswword of user
        - ReCreate = Recresate the database or connect to existing database
        - db_name =
        - table_details: Details of the tables to be created
        - batch_size:    Bulk data will be managed by batch_size to commit
        - p_bar_len:     Length for the progress bar
        - p_msg_width:   Width of message before progress bar
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
        if p_db_structure:
            self.db_structure = p_db_structure
        else:
            self.db_structure = {}
        self.delimiter = ","
        self.fkey_ref_act = {
            "C": "CASCADE",
            "R": "RESTRICT",
            "D": "SET DEFAULT",
            "N": "SET NULL",
        }
        self.host_name = p_host_name
        self.idx_type = {"U": "UNIQUE", "F": "FULLTEXT", "S": "SPATIAL"}
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
        """Close the connention"""
        if self.conn:
            self.conn.close()

    def create_db(self):
        """Create the database according to self.db_structure."""
        self.cur.execute("SHOW DATABASES")
        db_res = [x[0].decode() if isinstance(x[0], (bytearray, bytes)) else str(x[0]) for x in self.cur.fetchall()]
        # if self.db_name.lower() in db_res:
        if self.db_name in db_res:
            try:
                self.cur.execute(f"DROP DATABASE {self.db_name}")
                self.conn.commit()
            except mysql.connector.Error as err:
                self._print_err_msg(err, "Could not drop the database")
                self.close()
                sys.exit()
        try:
            self.cur.execute(f'CREATE DATABASE {self.db_name} DEFAULT CHARACTER SET "utf8"')
            self.conn.commit()
            self.cur.execute(f"USE {self.db_name}")
            self.conn.commit()
        except mysql.connector.Error as err:
            self._print_err_msg(err, "Could not create the database")
            self.close()
            sys.exit()
        return True

    def create_tables(self):
        """Create db tables from MySQL.table_details dict"""

        def build_db(p_db_sql_str_set):
            """Description"""
            for sql_set in p_db_sql_str_set:
                try:
                    self.cur.execute(sql_set[1])
                    if self.silent:
                        print(f"Created table = {sql_set[0]}")
                except mysql.connector.Error as err:
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
            """Description"""
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
            """Description"""
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
                            ".".join(fkey["FKeyFlds"]),
                            fkey["RefTable"],
                            ".".join(fkey["RefFields"]),
                            self.fkey_ref_act[fkey["OnDelete"]],
                            self.fkey_ref_act[fkey["OnUpdate"]],
                        )
                    )
                    constraint_list.append([fkey["FKeyTable"], fkey["RefTable"], fkey_str])
                    pass
            return constraint_list

        # def build_constraints

        def build_all_indexes(p_table_name):
            """Description"""

            # def build_primary_key_idx(p_table_name):
            #     '''Description'''
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
                """Description"""
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
                        if field_det[3] == "U":
                            idx_str = f"{self.idx_type[field_det[3]]} INDEX {idx_name} ("
                        else:
                            idx_str = f"INDEX {idx_name} ("
                        for field_det in idx_instance_order:
                            idx_str += f"{field_det[0]} {self.sort_order[field_det[2]]}, "
                        idx_str = idx_str[:-2] + ") VISIBLE, "
                        idx_str_list.append(idx_str)
                return idx_str_list, idx_name_list

            # end build_unique_key_idx

            idx_name_list = []
            idx_list = []
            idx_list, idx_name_list = build_unique_key_idx(p_table_name, idx_name_list, idx_list)
            return idx_list

        # def build_all_indexes

        def build_primary_key_sql_str(p_table_name):
            """Description"""
            primary_key_det = get_primary_key(p_table_name)
            sql_str = "PRIMARY KEY ({}), ".format(",".join(primary_key_det["Flds"]))
            return sql_str

        # def build_primary_key_sql_str

        def build_table_sql_str(p_table_name):
            """Description"""
            sql_str = f"CREATE TABLE {p_table_name} ("
            for field_name in self.db_structure[p_table_name]:
                field_type_st_ref = self.db_structure[p_table_name][field_name]["Type"]
                field_param_st_ref = self.db_structure[p_table_name][field_name]["Params"]
                field_comment_st_ref = self.db_structure[p_table_name][field_name]["Comment"]
                sql_str += f"{field_name} {field_type_st_ref[0]}"
                if field_type_st_ref[0] == "varchar" or field_type_st_ref[0] == "char":
                    sql_str += f" ({str(field_type_st_ref[1])})"
                elif field_type_st_ref[0] == "decimal":
                    sql_str += f"({str(field_type_st_ref[1])}, {str(field_type_st_ref[2])})"
                if field_param_st_ref["AI"] == "Y":
                    sql_str += " AUTO_INCREMENT"
                if field_param_st_ref["UN"] == "Y" and field_param_st_ref["AI"] != "Y":
                    sql_str += " UNSIGNED"
                if field_param_st_ref["NN"] == "Y":
                    sql_str += " NOT NULL"
                if field_param_st_ref["ZF"] == "Y":
                    sql_str += " ZEROFILL"
                if field_param_st_ref["DEF"]:
                    if field_type_st_ref[0] == "varchar" or field_type_st_ref[0] == "char":
                        sql_str += ' DEFAULT "{}"'.format(field_param_st_ref["DEF"])
                    else:
                        sql_str += " DEFAULT {}".format(field_param_st_ref["DEF"])
                if field_comment_st_ref:
                    sql_str += f' COMMENT "{field_comment_st_ref}"'
                sql_str += ", "
            return sql_str

        # end build_table_sql_str

        def get_foreign_key(p_table_name, p_field_name):
            """Description"""
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
            """Description"""
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
            """Description"""
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
            """Description"""

            def check_pkey_fkey_overlap(p_remove_fkey_pkey__overlap=True):
                """Description"""

                def partial_overlap(p_fkey, p_pkey):
                    """Description"""
                    is_overlap = False
                    for field_name in p_fkey["FKeyFlds"]:
                        if field_name in p_pkey["Flds"]:
                            is_overlap = True
                    return is_overlap

                # end partial_overlap

                def remove_fkey(p_fkey):
                    """Description"""
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
        return success

    def create_users(self, p_admin_user, p_new_users):
        c_user_name = 0
        self.cur.execute("SELECT User, Host FROM mysql.user")
        curr_users = self.cur.fetchall()
        for user in p_new_users:
            if not user[c_user_name] in curr_users:
                try:
                    self.cur.execute(
                        "CREATE USER IF NOT EXISTS '{}'@'{}' IDENTIFIED BY '{}'".format(
                            user[0], self.host_name, user[1]
                        )
                    )
                except mysql.connector.Error as err:
                    self._print_err_msg(err, "Could not create user")
                    self.close()
                    sys.exit()
            self.conn.commit()
        self.success = True

    def delete_users(self, p_admin_user, p_del_users):
        c_user_name = 0
        # c_password = 1
        c_host = 2
        self.cur.execute("SELECT User FROM mysql.user")
        curr_users = [x[0] for x in self.cur.fetchall()]
        for user in p_del_users:
            if user[c_user_name] in curr_users:
                try:
                    self.cur.execute(f"DROP USER '{user[c_user_name]}'@'{user[c_host]}'")
                except mysql.connector.Error as err:
                    self._print_err_msg(err, "Could not delete user")
                    self.close()
                    sys.exit()
        self.success = True

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
            all_sql_str = "SELECT " + header.replace(p_delimeter, ",") + " FROM " + p_table_name + " WHERE "
            for i, field in enumerate(self.db_structure[p_table_name]):
                if self.db_structure[p_table_name][field]["Params"]["PrimaryKey"][0] == "Y":
                    prim_key_sql_str += field + ", "
                    all_sql_str += field + " = %s and "
            prim_key_sql_str = prim_key_sql_str[:-2] + " FROM " + p_table_name
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
                sql_str = "SELECT " + header.replace(p_delimeter, ",") + " FROM " + p_table_name
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
            self.cur.execute("SELECT COUNT(*) FROM " + p_table_name)
        except mysql.connector.Error as err:
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
        """Description"""
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

    def grant_rights(self, p_admin_user, p_user_rights):
        c_user_name = 0
        # c_password = 1
        c_host = 1
        c_db = 2
        c_table = 3
        c_rights = 4
        # success = True
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
            except mysql.connector.Error as err:
                self._print_err_msg(err)
                self.close()
                sys.exit()
        self.success = True

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
        """Import a csv file into a database table.

        Parameters
        - p_table_name
          Table name to import the csv data into
        - p_csv_file_name = ''
          Csv file name.  Empty if structure contained in p_csv_db
        - p_key = ''
          Key used to insert in table
        - p_header = ''
          - Header of csv files
        - p_del_head = ''
          - Delete the header
        - p_csv_db = ''
          - Contains the csv table in a structure and makes p_csv_file_name obsolete.
        - p_csv_corr_str_file_name = ''
          - String that contains any strings that should be replace in the csv
            file before parsing
        - p_vol_type = 'Multi'
          - Multi - Read multiple volume
          - Single - Read single file
        - p_verbose = False
          - Determine if there are any output to screen
        - debug = False
          - Switch debug on
        - p_replace = False
          - False - INSERT into database
          - True - REPLACE into database
        """

        def import_volume(p_csv_db, p_header, p_verbose):
            """Description"""

            def convert_str_to_none(p_non_char_fields_idx, p_csv_db):
                """Description"""
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
                """Find the index of the fields that could potentially contain mepty strings."""
                non_char_fields_idx = []
                for header_field_name in self.non_char_fields[p_table_name]:
                    for row_idx, data_field_name in enumerate(p_csv_db[0]):
                        if header_field_name == data_field_name:
                            non_char_fields_idx.append(row_idx)
                            break
                return non_char_fields_idx

            # end find_non_char_field_idx

            def fix_dates(p_csv_db, p_table_name, p_header):
                """Ensure date and datetime fields in the database is valid."""
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
                """Write the data to a table"""
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
                # sql_str = 'REPLACE'
                if p_replace:
                    sql_str = "REPLACE"
                else:
                    sql_str = "INSERT"
                sql_str = "{} INTO {} ({}) VALUES ({})".format(
                    sql_str,
                    p_table_name,
                    ",".join([str(x) for x in header]),
                    ",".join(["%s" for x in range(len(header))]),
                )
                for j in range(self.batch_size, list_len, self.batch_size):
                    try:
                        self.cur.executemany(sql_str, p_csv_db[i : j + 1])
                    except Error as err:
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
            """Description"""
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
            """Description"""
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
        """Import a csv file into a database table.

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
          - OrgFieldN (str):     Field name from the csv file top copy to the database table
          - DestFieldN (str):    Destination filed where OrgFieldN will be copied into
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

    @staticmethod
    def _print_err_msg(p_err, p_msg=""):
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
    """This module creates a wrapper for the MySql database."""

    def __init__(
        self,
        p_host_name="localhost",
        p_user_name="",
        p_password="",
        p_user_rights=False,
        p_recreate_db=False,
        p_db_name=None,
        p_db_structure=None,
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
        """Description"""
        super().__init__(
            p_host_name=p_host_name,
            p_user_name=p_user_name,
            p_password=p_password,
            p_db_name=p_db_name,
            p_recreate_db=p_recreate_db,
            p_db_structure=p_db_structure,
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
        except mysql.connector.Error as err:
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
                    except mysql.connector.Error as err:
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


class MSSQL(SQLDbWrpr):
    """This module creates a wrapper for the MySql database."""

    def __init__(
        self,
        p_host_name="localhost",
        p_user_name="",
        p_password="",
        p_recreate_db=False,
        p_db_name=None,
        p_db_structure=None,
        p_batch_size=10000,
        p_bar_len=50,
        p_msg_width=50,
        p_verbose=False,
    ):
        """Description"""
        super().__init__(
            p_host_name=p_host_name,
            p_user_name=p_user_name,
            p_password=p_password,
            p_db_name=p_db_name,
            p_recreate_db=p_recreate_db,
            p_db_structure=p_db_structure,
            p_batch_size=p_batch_size,
            p_bar_len=p_bar_len,
            p_msg_width=p_msg_width,
            p_verbose=p_verbose,
        )
        try:
            self.host_name = "156.38.224.15,1433"
            self.user_name = "chessaco_chessanew"
            self._password = "@Jv&F77%"
            self.db_name = "chessaco_analytics"
            self.driver = "{ODBC Driver 17 for SQL Server}"
            # driver = pyodbc.drivers()
            # con_str_1 = 'DRIVER={};SERVER={};DATABASE={};UID={};PWD={}'.format( self.driver, self.host_name, self.db_name, self.user_name, self._password )
            con_str_2 = (
                "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
                + self.host_name
                + ";DATABASE="
                + self.db_name
                + ";UID="
                + self.user_name
                + ";PWD="
                + self._password
            )
            self.conn = pyodbc.connect(con_str_2)
            pass
        except Error as err:
            self.logger.error(err)
        self.success = self.conn.is_connected()
        if self.conn.is_connected():
            self.cur = self.conn.cursor()
            if self.re_create_db:
                self.create_db()
                self.success = self.create_tables()
