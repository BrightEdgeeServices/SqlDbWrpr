from conftest import db_structure

from sqldbwrpr.sqldbwrpr import MySQL


class TestSqlDbWrpr:
    def test_init(self, get_settings):
        sqldb = MySQL(
            p_host_name=get_settings.MYSQL_HOST,
            p_user_name="root",
            p_password=get_settings.MYSQL_ROOT_PASSWORD,
            p_recreate_db=True,
            p_db_name=get_settings.MYSQL_DATABASE,
            p_db_structure=db_structure,
            p_batch_size=10000,
            p_bar_len=50,
            p_msg_width=50,
            p_verbose=False,
            p_db_port=get_settings.MYSQL_TCP_PORT,
            # p_ssl_ca=None,
            # p_ssl_key=None,
            # p_ssl_cert=None,
        )
        sqldb.cur.execute("SHOW DATABASES")
        dbs = [x[0].decode() if isinstance(x[0], (bytearray, bytes)) else str(x[0]) for x in sqldb.cur.fetchall()]
        assert get_settings.MYSQL_DATABASE in dbs
        pass


# def do_tests(p_app_path='', p_cls=True):
#     '''Test the class methods.  Also called by the PackageIt PIP app to
#     test the module during PIP installation.
#
#     Parameters
#     - baseFolder   : Base folder for source code
#     - cls = True   : Clear the screen at start-up
#     '''
#
#     def basic_test():
#         '''Basic and mandatory scenario tests for certification of the class'''
#
#         def timport_csv(p_mysql_db_wrpr):
#             '''Basic and mandatory scenario tests for certification of the class'''
#             success = True
#             print('\nTest import of Csv files...')
#             tablest_o_load = {
#                 'Country': [country_path, t_country_db01],
#                 'Member': [member_path, t_member_db01],
#                 'MemberOrg': [member_org_path, t_member_org_db01],
#                 'Organization': [organization_path, t_organization_db01],
#                 'Rating': [rating_path, t_rating_db01],
#             }
#             for table_name in p_mysql_db_wrpr.table_load_order:
#                 if table_name in tablest_o_load:
#                     p_mysql_db_wrpr.import_csv(table_name, tablest_o_load[table_name][0])
#                     success = p_mysql_db_wrpr.success and success
#                     p_mysql_db_wrpr.cur.execute(
#                         'SELECT {} FROM {}'.format(
#                             ','.join(my_sql_db.db_structure[table_name]),
#                             table_name,
#                         )
#                     )
#                     table_res = p_mysql_db_wrpr.cur.fetchall()
#                     if beetools.is_struct_the_same(table_res, tablest_o_load[table_name][1]):
#                         success = True and success
#             return success
#
#         # end timport_csv
#
#         def t_export_db(p_mysql_db_wrpr):
#             '''Basic and mandatory scenario tests for certification of the class'''
#             success = True
#             print('\nTest export of tables to Csv files...')
#             tables_to_export = {
#                 'Member': [member_export_path, t_member_db01],
#                 'MemberOrg': [member_org_export_path, t_member_org_db01],
#                 'Organization': [organization_export_path, t_organization_db01],
#             }
#
#             for table_name in p_mysql_db_wrpr.table_load_order:
#                 if table_name in tables_to_export:
#                     vol_csv_file_name = tables_to_export[table_name][0]
#                     vol_cntr = 1
#                     while os.path.isfile(vol_csv_file_name):
#                         os.remove(vol_csv_file_name)
#                         vol_cntr += 1
#                         vol_csv_file_name = member_export_path[:-4] + f'{vol_cntr:0>2}' + member_export_path[-4:]
#                     p_mysql_db_wrpr.export_to_csv(tables_to_export[table_name][0], table_name)
#                     success = p_mysql_db_wrpr.success and success
#                     p_mysql_db_wrpr.cur.execute(f'TRUNCATE TABLE {table_name}')
#                     p_mysql_db_wrpr.conn.commit()
#                     p_mysql_db_wrpr.import_csv(table_name, tables_to_export[table_name][0])
#                     p_mysql_db_wrpr.cur.execute(
#                         'SELECT {} FROM {}'.format(
#                             ','.join(my_sql_db.db_structure[table_name]),
#                             table_name,
#                         )
#                     )
#                     table_res = p_mysql_db_wrpr.cur.fetchall()
#                     if not beetools.is_struct_the_same(table_res, tables_to_export[table_name][1]):
#                         success = False and success
#             return success
#
#         # end t_export_db
#
#         def tsql_query(p_mysql_db_wrpr):
#             '''Basic and mandatory scenario tests for certification of the class'''
#             success = True
#             print('\nTest SQL query feature...')
#             sql_query = [
#                 ['Surname', 'Name', 'OrgName'],
#                 '''SELECT Member.Surname, Member.Name, Organization.OrgName
#                                                               FROM Member
#                                                                 JOIN MemberOrg ON Member.Surname = MemberOrg.Surname AND Member.Name = MemberOrg.Name
#                                                                 JOIN Organization ON MemberOrg.OrgId = Organization.OrgId
#                                                                   WHERE Organization.OrgName = "St Louis Chess Club"''',
#             ]
#             my_sql_db.export_to_csv(export_join_path, 'Member', p_sql_query=sql_query)
#             csv_file_join_data = csvwrpr.CsvWrpr(
#                 _PROJ_NAME,
#                 p_csv_file_name=export_join_path,
#                 p_key1='Surname',
#                 p_header=sql_query[0],
#                 p_del_head=True,
#                 p_struc_type=[],
#             )
#             if not beetools.is_struct_the_same(csv_file_join_data.csv_db, t_join_member_member_org_db):
#                 success = False
#             return success
#
#         # end tsql_query
#
#         def t_multi_volume(p_mysql_db_wrpr):
#             '''Basic and mandatory scenario tests for certification of the class'''
#             success = True
#             print('\nTest multi volume import of Csv files...')
#             vol_csv_file_name = member_export_path
#             vol_cntr = 1
#             while os.path.isfile(vol_csv_file_name):
#                 os.remove(vol_csv_file_name)
#                 vol_cntr += 1
#                 vol_csv_file_name = member_export_path[:-4] + f'{vol_cntr:0>2}' + member_export_path[-4:]
#             p_mysql_db_wrpr.export_to_csv(member_export_path, 'Member')
#             p_mysql_db_wrpr.cur.execute('TRUNCATE TABLE Member')
#             p_mysql_db_wrpr.conn.commit()
#             p_mysql_db_wrpr.import_csv('Member', member_export_path)
#             p_mysql_db_wrpr.cur.execute(
#                 'SELECT Surname, Name, SosSec, Country, PassportNr, Race, RegDateTime, Picture, ActiveStatus, BirthYear, DOB FROM Member'
#             )
#             t_vol_test01 = p_mysql_db_wrpr.cur.fetchall()
#             if not beetools.is_struct_the_same(t_vol_test01, t_member_db01):
#                 success = False
#
#             # multi_vol_csv_path = os.path.join(test_data_folder, 'MultiVolCsv1.csv')
#             if os.path.isfile(member_export_path):
#                 os.remove(member_export_path)
#             file_name_list = p_mysql_db_wrpr.export_to_csv(member_export_path, 'Member', p__vol_size=1)
#             p_mysql_db_wrpr.cur.execute('TRUNCATE TABLE Member')
#             p_mysql_db_wrpr.conn.commit()
#             p_mysql_db_wrpr.import_csv('Member', member_export_path, p_vol_type='Multi')
#             p_mysql_db_wrpr.cur.execute('SELECT Surname, Name, ActiveStatus FROM Member ORDER BY Surname')
#             t_multi_vol_test01 = p_mysql_db_wrpr.cur.fetchall()
#             if not beetools.is_struct_the_same(t_multi_vol_test01, t_member_db02) and not file_name_list:
#                 success = False
#             return success
#
#         # end p_mysql_db_wrpr
#
#         def t_split_file01(p_mysql_db_wrpr):
#             '''Basic and mandatory scenario tests for certification of the class'''
#             success = True
#             print('\nTest split file structure feature...')
#             look_up_tbl = {'Asian': 1, 'Black': 2, 'White': 5}
#             tablest_o_load = {
#                 'Country': [country_path, t_country_db01],
#                 'Rating': [rating_path, t_rating_db01],
#             }
#             my_sql_db = MySQL(
#                 _PROJ_NAME,
#                 p_host_name=db_host_name,
#                 p_user_name=db_user[0],
#                 p_password=db_user[1],
#                 p_recreate_db=True,
#                 p_db_name=db_name,
#                 p_db_structure=db_structure,
#                 p_batch_size=1,
#             )
#             for table_name in p_mysql_db_wrpr.table_load_order:
#                 if table_name in tablest_o_load:
#                     p_mysql_db_wrpr.import_csv(table_name, tablest_o_load[table_name][0])
#                     success = p_mysql_db_wrpr.success and success
#                     p_mysql_db_wrpr.cur.execute(
#                         'SELECT {} FROM {}'.format(
#                             ','.join(my_sql_db.db_structure[table_name]),
#                             table_name,
#                         )
#                     )
#                     table_res = p_mysql_db_wrpr.cur.fetchall()
#                     if beetools.is_struct_the_same(table_res, tablest_o_load[table_name][1]):
#                         success = True and success
#
#             split_struct = {
#                 'Seq01': {
#                     'TableName': 'Member',
#                     'Key': 'Surname',
#                     'Replace': False,
#                     'Flds': [
#                         ['SurnameName', 'Surname', [2, 0, True]],
#                         ['SurnameName', 'Name', [2, 1, True]],
#                         [
#                             'IDNr',
#                             'SosSec',
#                             [
#                                 0,
#                                 0,
#                                 True,
#                                 [
#                                     [],
#                                 ],
#                             ],
#                         ],
#                         ['Country', 'Country', [0, 0, True, [['', None], 'CHN']]],
#                         ['None', 'PassportNr', [6, 100, True]],
#                         ['Race', 'Race', [4, look_up_tbl, True]],
#                         ['Picture', 'Picture', [1, None, False]],
#                         ['ActiveStatus', 'ActiveStatus', [1, 1, True]],
#                         [
#                             'BirthYear',
#                             'BirthYear',
#                             [
#                                 0,
#                                 0,
#                                 True,
#                                 [
#                                     [],
#                                 ],
#                             ],
#                         ],
#                         ['BirthYear', 'DOB', [3, 'Date', True]],
#                     ],
#                 },
#                 'Seq02': {
#                     'TableName': 'Organization',
#                     'Key': 'OrgId',
#                     'Replace': True,
#                     'Flds': [
#                         ['OrgId', 'OrgId', [0, 0, True]],
#                         ['OrgName', 'OrgName', [5, [0, 8], True]],
#                         ['RegFee', 'RegFee', [0, 0, True]],
#                         ['OpenTrading', 'OpenTrading', [0, 0, True]],
#                     ],
#                 },
#                 'Seq03': {
#                     'TableName': 'MemberOrg',
#                     'Key': 'Surname',
#                     'Replace': False,
#                     'Flds': [
#                         ['SurnameName', 'Surname', [2, 0, True]],
#                         ['SurnameName', 'Name', [2, 1, True]],
#                         ['OrgId', 'OrgId', [0, 0, True]],
#                     ],
#                 },
#             }
#             my_sql_db.import_and_split_csv(
#                 split_struct,
#                 split_test_csv_path,
#                 p_header=[
#                     'SurnameName',
#                     'IDNr',
#                     'Country',
#                     'PassportNr',
#                     'Race',
#                     'Picture',
#                     'ActiveStatus',
#                     'OrgId',
#                     'OrgName',
#                     'RegFee',
#                     'OpenTrading',
#                 ],
#                 p_verbose=True,
#             )
#             my_sql_db.cur.execute('SELECT {} FROM Member'.format(','.join(p_mysql_db_wrpr.db_structure['Member'])))
#             t_member_split_res = my_sql_db.cur.fetchall()
#             if not beetools.is_struct_the_same(t_member_split_res, t_member_db03):
#                 success = False
#             my_sql_db.cur.execute(
#                 'SELECT {} FROM Organization'.format(','.join(p_mysql_db_wrpr.db_structure['Organization']))
#             )
#             t_org_split_res = my_sql_db.cur.fetchall()
#             if not beetools.is_struct_the_same(t_org_split_res, t_organization_db02):
#                 success = False
#             my_sql_db.cur.execute(
#                 'SELECT {} FROM MemberOrg'.format(','.join(p_mysql_db_wrpr.db_structure['MemberOrg']))
#             )
#             t_member_org_split_res = my_sql_db.cur.fetchall()
#             if not beetools.is_struct_the_same(t_member_org_split_res, t_member_org_db02):
#                 success = False
#             my_sql_db.close()
#             return success
#
#         # end t_split_file01
#
#         def t_incomplete_records():
#             '''Read file with incomplete records'''
#             success = True
#             print('\nTest import of incomplete records...')
#             tablest_o_load = {
#                 'Country': [country_path, t_country_db01],
#                 'Member': [incomplete_records_path, t_member_db04],
#             }
#
#             my_sql_db = MySQL(
#                 _PROJ_NAME,
#                 p_host_name=db_host_name,
#                 p_user_name=db_user[0],
#                 p_password=db_user[1],
#                 p_recreate_db=True,
#                 p_db_name=db_name,
#                 p_db_structure=db_structure,
#                 p_batch_size=1,
#             )
#             for table_name in my_sql_db.table_load_order:
#                 if table_name in tablest_o_load:
#                     my_sql_db.import_csv(table_name, tablest_o_load[table_name][0])
#                     success = my_sql_db.success and success
#                     my_sql_db.cur.execute(
#                         'SELECT {} FROM {}'.format(
#                             ','.join(my_sql_db.db_structure[table_name]),
#                             table_name,
#                         )
#                     )
#                     table_res = my_sql_db.cur.fetchall()
#                     if not beetools.is_struct_the_same(table_res, tablest_o_load[table_name][1]):
#                         success = False and success
#             my_sql_db.close()
#             return success
#
#         # end t_incomplete_records
#
#         def t_user_creation(
#             p_db_host_name,
#             p_db_user,
#             p_db_name,
#             p_user_rights,
#             p_db_structure,
#             p_admin_user,
#             p_new_users,
#             p_new_user_rights,
#         ):
#             success = True
#             print('\nTest initialization, creation and population of database...')
#             for db_vendor in ['MySQL']:
#                 if db_vendor == 'MySQL':
#                     my_sql_db = MySQL(
#                         _PROJ_NAME,
#                         p_host_name=p_db_host_name,
#                         p_user_name=p_db_user[0],
#                         p_password=p_db_user[1],
#                         p_user_rights=p_user_rights,
#                         p_admin_username=p_admin_user[0],
#                         p_admin_user_password=p_admin_user[1],
#                     )
#                     my_sql_db.create_users(p_admin_user, p_new_users)
#                     my_sql_db.grant_rights(p_admin_user, p_new_user_rights)
#                     my_sql_db.delete_users(p_admin_user, p_new_users)
#             return success
#
#         # end t_user_creation
#
#         success = True
#         system_PROJ_NAME = platform.node()
#         if system_PROJ_NAME in ['ip-172-31-18-250']:
#             db_host_name = 'ccstldb.c9dax5ifrbth.us-east-1.rds.amazonaws.com'
#             db_name = 'urs_v2_dev2'
#             db_user = ['urs_devuser', '31u!Rg1UEmv9Iw$x']
#         else:
#             admin_user = ['root', 'En0l@Gay']
#             db_host_name = 'localhost'
#             db_name = 'SQLDbWrpr'
#             db_user = ['rtinstall', 'Rt1nst@ll']
#             db_user_rights = [db_user[0], db_host_name, '*', '*', 'ALL']
#             # db_port = '3306'
#             new_users = [
#                 ['Testing01', '1re$UtseT', 'localhost'],
#                 ['Testing02', '2re$UtseT', 'localhost'],
#             ]
#             new_user_rights = [
#                 [new_users[0][0], new_users[0][2], '*', '*', 'ALL'],
#                 [new_users[1][0], new_users[1][2], '*', '*', 'SELECT', 'INSERT'],
#             ]
#         test_data_folder = Path(__file__).absolute().parents[3] / _PROJ_NAME / 'Data'
#         country_path = os.path.join(test_data_folder, 'Country.csv')
#         # country_export_path = os.path.join(test_data_folder, 'CountryExport.csv')
#         export_join_path = os.path.join(test_data_folder, 'JoinExport.csv')
#         incomplete_records_path = os.path.join(test_data_folder, 'IncompleteRecords.csv')
#         member_export_path = os.path.join(test_data_folder, 'MemberExport.csv')
#         member_org_export_path = os.path.join(test_data_folder, 'MemberOrgExport.csv')
#         member_org_path = os.path.join(test_data_folder, 'MemberOrg.csv')
#         member_path = os.path.join(test_data_folder, 'Member.csv')
#         organization_export_path = os.path.join(test_data_folder, 'OrganizationExport.csv')
#         organization_path = os.path.join(test_data_folder, 'Organization.csv')
#         # rating_export_path = os.path.join(test_data_folder, 'RatingExport.csv')
#         # rating_export_path = os.path.join( test_data_folder, 'RatingExport.csv' )
#         rating_path = os.path.join(test_data_folder, 'Rating.csv')
#         split_test_csv_path = os.path.join(test_data_folder, 'SplitFile01.csv')
#         db_structure = {
#             'Rating': {
#                 'Date': {
#                     'Type': ['date'],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [1, 1, 'A', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Rate of publication',
#                 },
#                 'Name': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [1, 2, 'Member', 'Name', 'C', 'C'],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name from Member',
#                 },
#                 'Surname': {
#                     'Type': ['varchar', 45],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [1, 1, 'Member', 'Surname', 'C', 'C'],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Surname from Member',
#                 },
#                 'Rating': {
#                     'Type': ['int'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Rating of member',
#                 },
#                 'OrgMemberId': {
#                     'Type': ['int'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [1, 2, 'A', 'U'],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Rating of member',
#                 },
#             },
#             'Member': {
#                 'Surname': {
#                     'Type': ['varchar', 45],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Surname of member',
#                 },
#                 'Name': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name of the member',
#                 },
#                 'SosSec': {
#                     'Type': ['varchar', 10],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [1, 1, 'D', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Sosial security nr filled with zeros',
#                 },
#                 'Country': {
#                     'Type': ['char', 3],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [1, 1, 'Country', 'Code', 'R', 'C'],
#                         'Index': [2, 2, 'A', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Country passport',
#                 },
#                 'PassportNr': {
#                     'Type': ['char', 15],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [2, 1, 'D', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Passport number',
#                 },
#                 'Race': {
#                     'Type': ['tinyint'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '1',
#                     },
#                     'Possible Values': '1=White,2=Balck',
#                     'Comment': 'Race of member',
#                 },
#                 'RegDateTime': {
#                     'Type': ['datetime'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [3, 1, 'D', 'U'],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Registration date',
#                 },
#                 'Picture': {
#                     'Type': ['blob'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': 'Y',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Photo of member',
#                 },
#                 'ActiveStatus': {
#                     'Type': ['boolean'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Active | Inactive',
#                 },
#                 'BirthYear': {
#                     'Type': ['int'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Birth year of member',
#                 },
#                 'DOB': {
#                     'Type': ['date'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Date of Birth',
#                 },
#             },
#             'Country': {
#                 'Code': {
#                     'Type': ['char', 3],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'D'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': '3 digit country code',
#                 },
#                 'Description': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name of country',
#                 },
#             },
#             'Organization': {
#                 'OrgId': {
#                     'Type': ['bigint'],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'D'],
#                         'FKey': [],
#                         'Index': [1, 1, 'A', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': 'Y',
#                         'G': 'Y',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Organization id auto generated',
#                 },
#                 'OrgName': {
#                     'Type': ['varchar', 20],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [2, 1, 'A', ''],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Organization name',
#                 },
#                 'RegFee': {
#                     'Type': ['decimal', 5, 2],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Registration fee',
#                 },
#                 'OpenTrading': {
#                     'Type': ['time'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Opening time for trading',
#                 },
#             },
#             'MemberOrg': {
#                 'Surname': {
#                     'Type': ['varchar', 45],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Surname from Member',
#                 },
#                 'Name': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name from Member',
#                 },
#                 'OrgId': {
#                     'Type': [
#                         'bigint',
#                     ],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'D'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'OrgId from Organizarion',
#                 },
#             },
#         }
#         t_db_structure = {
#             'Rating': {
#                 'Date': {
#                     'Type': ['date'],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [1, 1, 'A', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Rate of publication',
#                 },
#                 'Name': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name from Member',
#                 },
#                 'Surname': {
#                     'Type': ['varchar', 45],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Surname from Member',
#                 },
#                 'Rating': {
#                     'Type': ['int'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Rating of member',
#                 },
#                 'OrgMemberId': {
#                     'Type': ['int'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [1, 2, 'A', 'U'],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Rating of member',
#                 },
#             },
#             'Member': {
#                 'Surname': {
#                     'Type': ['varchar', 45],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Surname of member',
#                 },
#                 'Name': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name of the member',
#                 },
#                 'SosSec': {
#                     'Type': ['varchar', 10],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [1, 1, 'D', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Sosial security nr filled with zeros',
#                 },
#                 'Country': {
#                     'Type': ['char', 3],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [1, 1, 'Country', 'Code', 'R', 'C'],
#                         'Index': [2, 2, 'A', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Country passport',
#                 },
#                 'PassportNr': {
#                     'Type': ['char', 15],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [2, 1, 'D', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Passport number',
#                 },
#                 'Race': {
#                     'Type': ['tinyint'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '1',
#                     },
#                     'Possible Values': '1=White,2=Balck',
#                     'Comment': 'Race of member',
#                 },
#                 'RegDateTime': {
#                     'Type': ['datetime'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [3, 1, 'D', 'U'],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Registration date',
#                 },
#                 'Picture': {
#                     'Type': ['blob'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': 'Y',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Photo of member',
#                 },
#                 'ActiveStatus': {
#                     'Type': ['boolean'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Active | Inactive',
#                 },
#                 'BirthYear': {
#                     'Type': ['int'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Birth year of member',
#                 },
#                 'DOB': {
#                     'Type': ['date'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Date of Birth',
#                 },
#             },
#             'Country': {
#                 'Code': {
#                     'Type': ['char', 3],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'D'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': '3 digit country code',
#                 },
#                 'Description': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name of country',
#                 },
#             },
#             'Organization': {
#                 'OrgId': {
#                     'Type': ['bigint'],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'D'],
#                         'FKey': [],
#                         'Index': [1, 1, 'A', 'U'],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': 'Y',
#                         'G': 'Y',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Organization id auto generated',
#                 },
#                 'OrgName': {
#                     'Type': ['varchar', 20],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [2, 1, 'A', ''],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Organization name',
#                 },
#                 'RegFee': {
#                     'Type': ['decimal', 5, 2],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Registration fee',
#                 },
#                 'OpenTrading': {
#                     'Type': ['time'],
#                     'Params': {
#                         'PrimaryKey': ['', ''],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': '',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Opening time for trading',
#                 },
#             },
#             'MemberOrg': {
#                 'Surname': {
#                     'Type': ['varchar', 45],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Surname from Member',
#                 },
#                 'Name': {
#                     'Type': ['varchar', 30],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'A'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': '',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'Name from Member',
#                 },
#                 'OrgId': {
#                     'Type': ['bigint'],
#                     'Params': {
#                         'PrimaryKey': ['Y', 'D'],
#                         'FKey': [],
#                         'Index': [],
#                         'NN': 'Y',
#                         'B': '',
#                         'UN': 'Y',
#                         'ZF': '',
#                         'AI': '',
#                         'G': '',
#                         'DEF': '',
#                     },
#                     'Possible Values': '',
#                     'Comment': 'OrgId from Organizarion',
#                 },
#             },
#         }
#         t_join_member_member_org_db = [
#             ['Ding', 'Liren', 'St Louis Chess Club'],
#             ['Nakamura', 'Hikaru', 'St Louis Chess Club'],
#         ]
#         t_member_db01 = [
#             (
#                 'Carlsen',
#                 'Magnus',
#                 'A123456781',
#                 'NOR',
#                 'AB12CD34',
#                 5,
#                 datetime.datetime(year=2020, month=3, day=26, hour=7, minute=0),
#                 None,
#                 1,
#                 1990,
#                 datetime.date(1990, 11, 30),
#             ),
#             (
#                 'Ding',
#                 'Liren',
#                 'B123456791',
#                 'CHN',
#                 'CD56EF78',
#                 1,
#                 datetime.datetime(year=2020, month=4, day=16, hour=8, minute=10),
#                 None,
#                 1,
#                 2000,
#                 datetime.date(1992, 10, 24),
#             ),
#             (
#                 'Nakamura',
#                 'Hikaru',
#                 'C123456793',
#                 'USA',
#                 'EF90GH12',
#                 5,
#                 datetime.datetime(year=2020, month=4, day=30, hour=9, minute=20, second=10),
#                 None,
#                 0,
#                 1980,
#                 datetime.date(2002, 11, 30),
#             ),
#         ]
#         t_member_db02 = [
#             ('Carlsen', 'Magnus', 1),
#             ('Ding', 'Liren', 1),
#             ('Nakamura', 'Hikaru', 0),
#         ]
#         t_member_db03 = [
#             (
#                 'Carlsen',
#                 'Magnus',
#                 'A123456781',
#                 'NOR',
#                 '100',
#                 5,
#                 None,
#                 None,
#                 1,
#                 1990,
#                 datetime.date(year=1990, month=1, day=1),
#             ),
#             (
#                 'Ding',
#                 'Liren',
#                 'B123456791',
#                 'CHN',
#                 '101',
#                 1,
#                 None,
#                 None,
#                 1,
#                 2000,
#                 datetime.date(year=2000, month=1, day=1),
#             ),
#             (
#                 'Nakamura',
#                 'Hikaru',
#                 'C123456793',
#                 'USA',
#                 '102',
#                 5,
#                 None,
#                 None,
#                 1,
#                 1980,
#                 datetime.date(year=1980, month=1, day=1),
#             ),
#         ]
#         t_member_db04 = [
#             (
#                 'Carlsen',
#                 'Magnus',
#                 'A123456781',
#                 'NOR',
#                 'AB12CD34',
#                 5,
#                 datetime.datetime(year=2020, month=3, day=26, hour=7, minute=0),
#                 None,
#                 1,
#                 1990,
#                 None,
#             ),
#             (
#                 'Ding',
#                 'Liren',
#                 'B123456791',
#                 'CHN',
#                 'CD56EF78',
#                 1,
#                 datetime.datetime(year=2020, month=4, day=16, hour=8, minute=10),
#                 None,
#                 1,
#                 2000,
#                 None,
#             ),
#             (
#                 'Nakamura',
#                 'Hikaru',
#                 'C123456793',
#                 'USA',
#                 'EF90GH12',
#                 5,
#                 datetime.datetime(year=2020, month=4, day=30, hour=9, minute=20, second=10),
#                 None,
#                 0,
#                 1980,
#                 None,
#             ),
#         ]
#         t_member_org_db01 = [
#             ('Carlsen', 'Magnus', 6),
#             ('Ding', 'Liren', 3),
#             ('Nakamura', 'Hikaru', 3),
#         ]
#         t_member_org_db02 = [
#             ('Carlsen', 'Magnus', 6),
#             # ( 'Ding'   ,  'Liren',  3 ),
#             ('Nakamura', 'Hikaru', 3),
#         ]
#         t_country_db01 = [
#             ('CHN', 'China'),
#             ('NOR', 'Norway'),
#             ('USA', 'United States of America'),
#         ]
#         t_organization_db01 = [
#             (2, 'Boondocs Chess Club', 150.00, datetime.timedelta(seconds=68400)),
#             (3, 'St Louis Chess Club', 100.00, datetime.timedelta(seconds=32400)),
#             (6, 'Ice Cold Chess Club', 20.00, datetime.timedelta(seconds=28800)),
#         ]
#         t_organization_db02 = [
#             (3, 'St Louis', 100.00, datetime.timedelta(seconds=32400)),
#             (6, 'Ice Cold', 20.00, datetime.timedelta(seconds=28800)),
#         ]
#         t_rating_db01 = [
#             (datetime.date(2020, 2, 29), 'Hikaru', 'Nakamura', 2750, 123456),
#             (datetime.date(2020, 2, 29), 'Liren', 'Ding', 2800, 234567),
#             (datetime.date(2020, 2, 29), 'Magnus', 'Carlsen', 2850, 456789),
#             (datetime.date(2020, 3, 31), 'Hikaru', 'Nakamura', 2760, 123456),
#             (datetime.date(2020, 3, 31), 'Liren', 'Ding', 2830, 234567),
#             (datetime.date(2020, 3, 31), 'Magnus', 'Carlsen', 2845, 456789),
#         ]
#         # del_users = [[x[0], x[2]] for x in new_users]
#
#         # success = (
#         #     t_init(
#         #         db_host_name,
#         #         db_user,
#         #         db_name,
#         #         db_user_rights,
#         #         db_structure,
#         #         admin_user,
#         #         db_port,
#         #     )
#         #     and success
#         # )
#         success = (
#             t_user_creation(
#                 db_host_name,
#                 db_user,
#                 db_name,
#                 db_user_rights,
#                 db_structure,
#                 admin_user,
#                 new_users,
#                 new_user_rights,
#             )
#             and success
#         )
#         my_sql_db = MySQL(
#             _PROJ_NAME,
#             p_host_name=db_host_name,
#             p_user_name=db_user[0],
#             p_password=db_user[1],
#             p_recreate_db=True,
#             p_db_name=db_name,
#             p_db_structure=db_structure,
#             p_batch_size=1,
#         )
#         success = my_sql_db.success and success
#         if not beetools.is_struct_the_same(my_sql_db.db_structure, t_db_structure):
#             success = False and success
#         success = timport_csv(my_sql_db) and success
#         success = t_export_db(my_sql_db) and success
#         success = tsql_query(my_sql_db) and success
#         success = t_multi_volume(my_sql_db) and success
#         my_sql_db.close()
#         my_sql_db = MySQL(
#             _PROJ_NAME,
#             p_host_name=db_host_name,
#             p_user_name=db_user[0],
#             p_password=db_user[1],
#             p_recreate_db=True,
#             p_db_name=db_name,
#             p_db_structure=db_structure,
#             p_batch_size=1,
#         )
#         success = t_split_file01(my_sql_db) and success
#         my_sql_db.close()
#         success = t_incomplete_records() and success
#         return success
#
#     success = True
#     b_tls = beetools.Archiver(
#         _PROJ_DESC,
#         _PROJ_PATH,
#         p_app_ini_file_name=None,
#         p_cls=True,
#         # p_logger = False,
#         p_arc_excl_dir=None,
#         p_arc_extern_dir=None,
#         p_arc_incl_ext=None,
#     )
#     logger = logging.getLogger(_PROJ_NAME)
#     logger.setLevel(beetools.DEF_LOG_LEV)
#     file_handle = logging.FileHandler(beetools.LOG_FILE_NAME, mode='w')
#     file_handle.setLevel(beetools.DEF_LOG_LEV_FILE)
#     console_handle = logging.StreamHandler()
#     console_handle.setLevel(beetools.DEF_LOG_LEV_CON)
#     file_format = logging.Formatter(beetools.LOG_FILE_FORMAT, datefmt=beetools.LOG_DATE_FORMAT)
#     console_format = logging.Formatter(beetools.LOG_CONSOLE_FORMAT)
#     file_handle.setFormatter(file_format)
#     console_handle.setFormatter(console_format)
#     logger.addHandler(file_handle)
#     logger.addHandler(console_handle)
#
#     b_tls.print_header(p_cls=p_cls)
#     success = basic_test()
#     beetools.result_rep(success, 'Done')
#     b_tls.print_footer()
#     if success:
#         return b_tls.arc_pth
#     return False
#
#
# # end do_tests
#
# if __name__ == '__main__':
#     do_tests(p_app_path=str(_PROJ_PATH))
# # end __main__
