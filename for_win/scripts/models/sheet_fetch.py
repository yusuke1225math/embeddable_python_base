import json
import os
import pandas as pd
import sys
import gspread
from config.sheet_config import JSON_PATH
from datetime import date, datetime
from oauth2client.service_account import ServiceAccountCredentials
from time import sleep

SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(JSON_PATH, SCOPE)
gc = gspread.authorize(CREDENTIALS)


def worksheet_ready(spreadsheet_key, sheet_name):
    try:
        worksheet = gc.open_by_key(spreadsheet_key).worksheet(sheet_name)
        return worksheet
    except Exception as e:
        print(e)
        return False


def toAlpha(num):
    # アルファベットから数字を返すラムダ式(A列～Z列まで) # 例：A→1、Z→26
    if num <= 26:
        return chr(64 + num)
    elif num % 26 == 0:
        return toAlpha(num // 26 - 1) + chr(90)
    else:
        return toAlpha(num // 26) + chr(64 + num % 26)


def alpha2num(c):
    return ord(c) - ord('A') + 1


def json_serial(obj):
    """sheetAPI用のdate, datetimeの変換関数"""
    # 日付型の場合には、文字列に変換します
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError("Type %s not serializable" % type(obj))


def get_current_datetime():
    """sheetAPI用のdate, datetimeの変換関数"""
    # datetime型を含むdict
    # item = {"dt": datetime.now()}
    # default引数を指定して、JSON文字列を生成します
    # jsonstr = json.dumps(item, default=json_serial)
    # jsondict = json.loads(jsonstr)
    # return jsondict['dt']
    return datetime.now().strftime('%Y/%m/%d %H:%M')


def get_col_num_from_col_name(sheet, column_name, index_row_num):
    """
    シートに対して、カラム名行番号とカラム名を与えると、所望の列番号を返す
    """
    charge_target_lists = sheet.row_values(index_row_num)
    column = charge_target_lists.index(column_name) + 1
    return column


def get_col_values(sheet, column_name, index_row_num):
    try:
        return sheet.col_values(
            get_col_num_from_col_name(sheet, column_name, index_row_num)
        )[index_row_num:]
    except Exception as e:
        print(e)
        return None


# fuetter GUI sheet
# https://docs.google.com/spreadsheets/d/1tVmOTIXtetAnEPKFhMEfl3kGoia4nZ7AgvhdnSkg4a8/edit
SPREADSHEET_KEY = '1tVmOTIXtetAnEPKFhMEfl3kGoia4nZ7AgvhdnSkg4a8'


class MonitorStatusSheet():
    def __init__(self):
        self.SHEET_NAME = 'monitor_status'

        while True:
            sheet = worksheet_ready(SPREADSHEET_KEY, self.SHEET_NAME)
            if sheet is not None:
                break
            else:
                print('WaitingForSheetAPILimit')
                sleep(100)
        self.sheet = sheet

        # CurrentStatus
        self.INDEX_NAME_UPDATE_DATE = '更新日時'
        self.INDEX_NAME_FOLOWER = 'フォロワー'
        self.INDEX_NAME_FOLLOW = 'フォロー中'
        self.INDEX_NAME_FAV = 'いいね'
        self.INDEX_NAME_TWEET = 'ツイート'
        # BaseInfomation
        self.INDEX_NAME_SCREEN_NAME = 'screen_name'
        self.INDEX_NAME_PASSWORD = 'password'
        self.INDEX_NAME_ATTRIBUTE_TAG = 'attribute_tag'
        self.INDEX_NAME_RESEARCH_URL = 'research_url'
        self.INDEX_NAME_SCRAPE_FROM = 'scrape_from'
        self.INDEX_NAME_IS_CONSUMED = 'is_consumed'
        self.INDEX_NAME_COMSUMED_AT = 'comsumed_at'
        # Status
        self.INDEX_NAME_FOLLOW = 'follow'
        self.INDEX_NAME_UNFOLLOW = 'unfollow'
        self.INDEX_NAME_LIKE = 'like'
        self.INDEX_NAME_DM = 'dm'
        self.INDEX_NAME_REPLY = 'reply'
        # Conditions
        self.INDEX_NAME_FOLLOW_LIMIT = 'follow_limit'
        self.INDEX_NAME_FOLLOW_INTERVAL = 'follow_interval'
        self.INDEX_NAME_UNFOLLOW_LIMIT = 'unfollow_limit'
        self.INDEX_NAME_UNFOLLOW_INTERVAL = 'unfollow_interval'
        self.INDEX_NAME_LIKE_TARGET_LIMIT = 'like_target_limit'
        self.INDEX_NAME_LIKE_INTERVAL = 'like_interval'
        self.INDEX_NAME_LIKE_ONCE_LIMIT = 'like_once_limit'
        self.INDEX_NAME_DM_INTERVAL = 'dm_interval'
        self.INDEX_NAME_DM_MESSAGE = 'dm_message'
        self.INDEX_NAME_DM_LIMIT = 'dm_limit'
        self.INDEX_NAME_SEARCH_CONDITIONS = 'search_conditions'
        self.INDEX_NAME_SEARCH_KEYWORDS = 'search_keywords'

        # シートの基本的な情報を格納
        self.INDEX_ROW_NUM = 2
        all_values = sheet.get_all_values()
        self.INDEX_ROW = all_values.pop(self.INDEX_ROW_NUM - 1)
        for i in range(self.INDEX_ROW_NUM - 1):
            all_values.pop(0)

        # DataFrameに変換して利用
        df_all = pd.DataFrame(all_values)
        df_all.columns = self.INDEX_ROW

        # 基本的なステータス
        self.screen_name = df_all[self.INDEX_NAME_SCREEN_NAME].tolist()
        self.password = dict(zip(self.screen_name, df_all[self.INDEX_NAME_PASSWORD].tolist()))
        self.follow_status = dict(zip(self.screen_name, df_all[self.INDEX_NAME_FOLLOW].tolist()))
        self.unfollow_status = dict(zip(self.screen_name, df_all[self.INDEX_NAME_UNFOLLOW].tolist()))
        self.like_status = dict(zip(self.screen_name, df_all[self.INDEX_NAME_LIKE].tolist()))
        self.dm_status = dict(zip(self.screen_name, df_all[self.INDEX_NAME_DM].tolist()))
        self.reply_status = dict(zip(self.screen_name, df_all[self.INDEX_NAME_REPLY].tolist()))

        # automation conditions
        self.follow_limit = dict(zip(self.screen_name, df_all[self.INDEX_NAME_FOLLOW_LIMIT].tolist()))
        self.follow_interval = dict(zip(self.screen_name, df_all[self.INDEX_NAME_FOLLOW_INTERVAL].tolist()))
        self.unfollow_limit = dict(zip(self.screen_name, df_all[self.INDEX_NAME_UNFOLLOW_LIMIT].tolist()))
        self.unfollow_interval = dict(zip(self.screen_name, df_all[self.INDEX_NAME_UNFOLLOW_INTERVAL].tolist()))
        self.like_target_limit = dict(zip(self.screen_name, df_all[self.INDEX_NAME_LIKE_TARGET_LIMIT].tolist()))
        self.like_interval = dict(zip(self.screen_name, df_all[self.INDEX_NAME_LIKE_INTERVAL].tolist()))
        self.like_once_limit = dict(zip(self.screen_name, df_all[self.INDEX_NAME_LIKE_ONCE_LIMIT].tolist()))
        self.dm_interval = dict(zip(self.screen_name, df_all[self.INDEX_NAME_DM_INTERVAL].tolist()))
        # self.dm_message = dict(zip(self.screen_name, df_all[self.INDEX_NAME_DM_MESSAGE].tolist()))
        self.dm_limit = dict(zip(self.screen_name, df_all[self.INDEX_NAME_DM_LIMIT].tolist()))
        self.search_keywords = dict(zip(self.screen_name, df_all[self.INDEX_NAME_SEARCH_KEYWORDS].tolist()))
        self.search_conditions = dict(zip(self.screen_name, df_all[self.INDEX_NAME_SEARCH_CONDITIONS].tolist()))

    def get_password(self, username):
        try:
            return self.password[username]
        except Exception as e:
            print(e)
            return False

    def get_active_follow(self):
        if self.follow_status is not None:
            return [key for key, value in self.follow_status.items() if value == '1']
        else:
            return None

    def get_active_unfollow(self):
        if self.unfollow_status is not None:
            return [key for key, value in self.unfollow_status.items() if value == '1']
        else:
            return None

    def get_active_like(self):
        if self.like_status is not None:
            return [key for key, value in self.like_status.items() if value == '1']
        else:
            return None

    def get_active_dm(self):
        if self.dm_status is not None:
            return [key for key, value in self.dm_status.items() if value == '1']
        else:
            return None

    def suspend_all_execution(self, username):
        """アカウントロック時などに、シートの実行ステータスをすべてオフにする"""
        try:
            all_column_name = [
                self.INDEX_NAME_FOLLOW,
                self.INDEX_NAME_UNFOLLOW,
                self.INDEX_NAME_LIKE,
                self.INDEX_NAME_DM,
                self.INDEX_NAME_REPLY
            ]
            while all_column_name != []:
                name = all_column_name.pop(0)
                col_num = self.INDEX_ROW.index(name) + 1
                row_num = self.INDEX_ROW_NUM + self.screen_name.index(username) + 1
                print(str(row_num) + ', ' + str(col_num))
                print('{}\'s {} status is updated to 0'.format(
                    username,
                    name
                ))
            return True
        except Exception as e:
            print('SuspensionSheetUpdateError')
            print(e)
            return False

    def get_search_conditions(self, username):
        try:
            return self.search_conditions[username]
        except Exception as e:
            print(e)
            return False

    def get_search_keywords(self, username):
        try:
            return self.search_keywords[username]
        except Exception as e:
            print(e)
            return False

    def get_follow_limit(self):
        return self.follow_limit

    def get_follow_interval(self):
        return self.follow_interval

    def get_unfollow_limit(self):
        return self.unfollow_limit

    def get_unfollow_interval(self):
        return self.unfollow_interval

    def get_like_target_limit(self):
        return self.like_target_limit

    def get_like_interval(self):
        return self.like_interval

    def get_like_once_limit(self):
        return self.like_once_limit

    def get_dm_interval(self):
        return self.dm_interval

    def get_dm_message(self):
        return self.dm_message

    def get_dm_limit(self):
        return self.dm_limit


class NgKeywordSheet():
    def __init__(self):
        self.SHEET_NAME = 'ng_keyword'
        self.INDEX_ROW_NUM = 2
        self.NG_KEYWORD = 'ng_keyword'
        self.NG_KEYWORD_ID = 'ng_keyword_id'
        self.EXECUTOR = 'executor'
        sheet = worksheet_ready(SPREADSHEET_KEY, self.SHEET_NAME)
        if sheet is not False:
            try:
                self.sheet = sheet
                self.charge_target_lists = sheet.get_all_values()
                self.column = self.charge_target_lists.pop(1)
                self.charge_target_lists.pop(0)
            except Exception as e:
                print(e)

    def get_ng_word(self, screen_name):
        try:
            df_all = pd.DataFrame(self.charge_target_lists)
            df_all.columns = self.column
            ng_words = df_all[df_all["executor"].isin([screen_name])]
            ng_words = ng_words.values.tolist()
            ng_words_list = []
            for value in ng_words:
                col_num_from_ng_keyword_id = get_col_num_from_col_name(self.sheet, self.NG_KEYWORD_ID, self.INDEX_ROW_NUM)
                col_num_from_ng_words = get_col_num_from_col_name(self.sheet, self.NG_KEYWORD, self.INDEX_ROW_NUM)
                col_num_from_executor = get_col_num_from_col_name(self.sheet, self.EXECUTOR, self.INDEX_ROW_NUM)
                ng_words_list.append((
                    value[col_num_from_ng_keyword_id - 1],
                    value[col_num_from_ng_words - 1],
                    value[col_num_from_executor - 1]
                ))
            return ng_words_list
        except Exception as e:
            print(e)
            return None


class ChargeTargetSheet():
    def __init__(self):
        self.SHEET_CHARGE_TARGET = 'charge_target'
        while True:
            sheet = worksheet_ready(SPREADSHEET_KEY, self.SHEET_CHARGE_TARGET)
            if sheet is not None:
                break
            else:
                print('WaitingForSheetAPILimit')
                sleep(100)
        self.sheet = sheet
        self.charge_target_lists = self.sheet.get_all_values()
        self.column = self.charge_target_lists.pop(1)
        self.charge_target_lists.pop(0)
        self.INDEX_ROW_NUM = 2
        self.INDEX_ROW = self.column
        self.COLUMN_NAME_CHARGE_TARGET_ID = 'charge_target_id'
        self.COLUMN_NUM_CHARGE_TARGET_ID = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_CHARGE_TARGET_ID, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_FOLLOW_USERNAME = 'follow_username'
        self.COLUMN_NUM_FOLLOW_USERNAME = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_FOLLOW_USERNAME, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_SEED_SCREEN_NAME = 'seed_screen_name'
        self.COLUMN_NUM_SEED_SCREEN_NAME = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_SEED_SCREEN_NAME, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_RESEARCH_URL = 'research_url'
        self.COLUMN_NUM_RESEARCH_URL = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_RESEARCH_URL, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_ATTRIBUTE_TAG = 'attribute_tag'
        self.COLUMN_NUM_ATTRIBUTE_TAG = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_ATTRIBUTE_TAG, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_SCRAPE_FROM = 'scrape_from'
        self.COLUMN_NUM_SCRAPE_FROM = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_SCRAPE_FROM, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_IS_CONSUMED = 'is_consumed'
        self.COLUMN_NUM_IS_CONSUMED = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_IS_CONSUMED, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_CONSUMED_AT = 'consumed_at'
        self.COLUMN_NUM_CONSUMED_AT = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_CONSUMED_AT, self.INDEX_ROW_NUM)

    def get_seed_name_list(self, executor_name):
        try:
            df_all = pd.DataFrame(self.charge_target_lists)
            df_all.columns = self.column
            is_consumed_zero = df_all[df_all["is_consumed"].isin(["0"])]
            is_consumed_zero = is_consumed_zero[is_consumed_zero["follow_username"].isin([executor_name])]
            is_consumed_zero_value = is_consumed_zero.values.tolist()
            is_consumed_zero_tuple_list = []
            for value in is_consumed_zero_value:
                is_consumed_zero_tuple_list.append(
                    value[self.COLUMN_NUM_SEED_SCREEN_NAME - 1]
                )
            return is_consumed_zero_tuple_list
        except Exception as e:
            print(e)
            return None

    def get_charge_target_of_screen_name(self, executor_name):
        """
        Spreadsheetのcharge_targetから、特定のアカウントのtargetを読み出して、付随データと一緒に返す処理
        """
        try:
            df_all = pd.DataFrame(self.charge_target_lists)
            df_all.columns = self.column
            is_consumed_zero = df_all[df_all["is_consumed"].isin(["0"])]
            is_consumed_zero = is_consumed_zero[is_consumed_zero["follow_username"].isin([executor_name])]
            is_consumed_zero_value = is_consumed_zero.values.tolist()
            is_consumed_zero_tuple_list = []
            for value in is_consumed_zero_value:
                is_consumed_zero_tuple_list.append(
                    (
                        value[self.COLUMN_NUM_CHARGE_TARGET_ID - 1],
                        value[self.COLUMN_NUM_RESEARCH_URL - 1],
                        value[self.COLUMN_NUM_SCRAPE_FROM - 1]
                    )
                )
            return is_consumed_zero_tuple_list
        except Exception as e:
            print(e)
            return None

    def consume_a_charge_target(self, charge_target_id):
        try:
            self.sheet.update_cell(
                int(charge_target_id) + int(self.INDEX_ROW_NUM),
                self.COLUMN_NUM_IS_CONSUMED,
                1
            )
            self.sheet.update_cell(
                int(charge_target_id) + int(self.INDEX_ROW_NUM),
                self.COLUMN_NUM_CONSUMED_AT,
                get_current_datetime()
            )
            return True
        except Exception as e:
            print(e)
            return False


class PostScheduleSheet():
    def __init__(self):
        self.SHEET_NAME = 'post_schedule'
        while True:
            sheet = worksheet_ready(SPREADSHEET_KEY, self.SHEET_NAME)
            if sheet is not None:
                break
            else:
                print('WaitingForSheetAPILimit')
                sleep(100)
        self.sheet = sheet
        self.all_values = self.sheet.get_all_values()
        self.column = self.all_values.pop(1)
        self.all_values.pop(0)
        self.INDEX_ROW_NUM = 2
        self.INDEX_ROW = self.column
        self.COLUMN_NAME_POST_SCHEDULE_ID = 'post_schedule_id'
        self.COLUMN_NUM_POST_SCHEDULE_ID = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_POST_SCHEDULE_ID, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_POST_EXECUTION_STATUS = 'post_execution_status'
        self.COLUMN_NUM_POST_EXECUTION_STATUS = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_POST_EXECUTION_STATUS, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_POST_EXECUTOR = 'post_executor'
        self.COLUMN_NUM_POST_EXECUTOR = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_POST_EXECUTOR, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_POST_NO_FIRST = 'post_no_01'
        self.COLUMN_NUM_POST_NO_FIRST = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_POST_NO_FIRST, self.INDEX_ROW_NUM)
        self.COLUMN_NAME_POST_NO_LAST = 'post_no_24'
        self.COLUMN_NUM_POST_NO_LAST = get_col_num_from_col_name(self.sheet, self.COLUMN_NAME_POST_NO_LAST, self.INDEX_ROW_NUM)

    def get_post_executor(self):
        try:
            df_all = pd.DataFrame(self.all_values)
            df_all.columns = self.column
            df_post_executor = df_all[self.COLUMN_NAME_POST_EXECUTOR]
            df_post_executor_list = []
            for value in df_post_executor:
                df_post_executor_list.append(value)
            return df_post_executor_list
        except Exception as e:
            print(e)
            return False
        
    def get_post_execution_status(self, executor_name):
        try:
            df_all = pd.DataFrame(self.all_values)
            df_all.columns = self.column
            df_post_execution_status = df_all[df_all[self.COLUMN_NAME_POST_EXECUTOR].isin([executor_name])]
            df_post_execution_status = df_post_execution_status[self.COLUMN_NAME_POST_EXECUTION_STATUS]
            return df_post_execution_status[0]
        except Exception as e:
            print(e)
            return False
   
    def get_all_posts(self, executor_name):
        try:
            df_all = pd.DataFrame(self.all_values)
            df_all.columns = self.column
            df_post_execution_status = df_all[df_all[self.COLUMN_NAME_POST_EXECUTOR].isin([executor_name])]
            df_post_execution_status = df_post_execution_status.loc[:, self.COLUMN_NAME_POST_NO_FIRST:self.COLUMN_NAME_POST_NO_LAST]
            df_post_execution_status = df_post_execution_status.iloc[0]
            # return df_post_execution_status
            all_posts = []
            for value in df_post_execution_status:
                all_posts.append(value)
            return all_posts
        except Exception as e:
            print(e)
            return False
   

    #     return all_posts
