import argparse
import chromedriver_binary
import os
import selenium
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from time import sleep

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
os.chdir(parent_dir)

from models import db_models_temp
from models import fuetter_driver
from models import sheet_fetch


def main():
    # argument settings
    parser = argparse.ArgumentParser()
    parser.add_argument('--search_update_interval', help='SearchUpdating', default=100, type=int)
    parser.add_argument('--total_like_limit', help='total like sending limit', default=100, type=int)
    parser.add_argument('--waiting', help='WaitingTimePerSearch', default=10, type=int)
    parser.add_argument('--search_like_limit', help='like sending limit per search', default=5, type=int)
    parser.add_argument('--time_interval', help='time interval [sec] per like', default=60, type=int)
    parser.add_argument('-u', '--user_id', help='cookies user_id', default='tabaccolasnri')
    parser.add_argument('--headless', help='headless mode[default: False]', action='store_true')
    args = parser.parse_args()

    try:
        print('Trying to like from search by {}'.format(args.user_id))
        sheet_monitor_status = sheet_fetch.MonitorStatusSheet()
        executor = args.user_id

        fuetter = fuetter_driver.FuetterDriver(headless=args.headless, noimage=True)
        fuetter.login(
            executor,
            sheet_monitor_status.get_password(args.user_id)
        )

        # シートのいいねステータスが1じゃない場合にはスクリプト終了
        if args.user_id not in sheet_monitor_status.get_active_like:
            fuetter.driver.quit()
            sys.exit()

        # アカウントロックの確認
        if fuetter.is_invalid_user():
            sheet_monitor_status.suspend_all_execution(args.user_id)
            fuetter.driver.quit()
            sys.exit()

        options = {
            'keyword_list': sheet_monitor_status.get_search_keywords(executor).split(','),
            'like_limit_per_kw': args.search_like_limit,
            'load_wait_time': 3,
            'ng_keyword_str': sheet_monitor_status.get_search_conditions(executor),
            'search_update_interval': args.search_update_interval,
            'sleep_base_sec': args.time_interval,
            'sleep_rand_upper': 5,
            'total_like_limit': args.total_like_limit,
            'waiting': args.waiting
        }

        # いいね実行処理
        fuetter.search_and_like(
            args.user_id,
            options
        )

    except selenium.common.exceptions.WebDriverException:
        pass

    finally:
        try:
            fuetter.driver.quit()
        except:
            pass


if __name__ == '__main__':
    main()
