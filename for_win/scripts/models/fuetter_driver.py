import chromedriver_binary
import datetime
import os
import pickle
import random
import re
import selenium
import sys
import tweepy
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
from time import time
from models import db_models_temp
from models import sheet_fetch
from models import twitter_api
from module.utilities import LOAD_WAIT_TIME


# ============================================================
# driver
#
class FuetterDriver():
    def __init__(self, headless=False, noimage=False, width=False):
        self.options = Options()
        if headless is True:
            self.options.add_argument('--headless')
        if noimage is True:
            self.options.add_argument('--blink-settings=imagesEnabled=false')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--lang=ja-JP')
        self.options.add_experimental_option("prefs", {
            "download.default_directory": r"~/Downloads/",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        self.driver = webdriver.Chrome(options=self.options)
        if width:
            self.driver.set_window_size(width, 1000)

# ============================================================
# Login methods
#
    def login(self, screen_name, password):
        if self.login_by_cookies(screen_name, password):
            if not self.is_login_successful():
                self.login_by_form(screen_name, password)
        else:
            self.login_by_form(screen_name, password)

    def login_by_cookies(self, screen_name, password):
        COOKIES_FILENAME = 'cookies/cookies__{}.pkl'.format(screen_name)
        if os.path.exists(COOKIES_FILENAME):
            self.driver.get('https://twitter.com')
            sleep(1)
            try:
                cookies = pickle.load(open(COOKIES_FILENAME, "rb"))
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.driver.get('https://twitter.com')
                sleep(1)
                return True
            except Exception as e:
                print(e)
                print('No twitter login Cookies. Plz generate cookies by cookies/get_cookies.py')
                return False
        else:
            print('NoCookies')
            return False

    def login_by_form(self, screen_name, password):
        # cookiesがない場合にはログイン画面からログイン
        self.driver.quit()
        self.driver = webdriver.Chrome(options=self.options)
        XPATH_BUTTON_LOGIN = '(//div[contains(@data-testid,"Login")])[1]'
        XPATH_INPUT_ID = '(//input[@name="session[username_or_email]"])[1]'
        XPATH_PASSWORD_ID = '(//input[@name="session[password]"])[1]'
        self.driver.get('https://twitter.com/login')
        sleep(2)
        try:
            # Input user_id
            self.driver.find_element_by_xpath(XPATH_INPUT_ID).send_keys(screen_name)
            # Input password
            self.driver.find_element_by_xpath(XPATH_PASSWORD_ID).send_keys(password)
            sleep(1)
            # Push submit button
            login_button = self.driver.find_element_by_xpath(XPATH_BUTTON_LOGIN)
            self.click_element(login_button)
            sleep(3)
            # cookiesがない場合にはcookiesを保存する
            pickle.dump(self.driver.get_cookies(), open("cookies/cookies__{}.pkl".format(screen_name), "wb"))
            return True
        except Exception as e:
            print(e)
            return False

    def is_login_successful(self):
        try:
            self.driver.get('https://twitter.com/fuestagram')
            sleep(3)
            self.driver.get('https://twitter.com/fuestagram')
            sleep(3)
            self.driver.refresh()
            sleep(3)
            # ログインできなかったときに現れるパーツが取れるかどうかを確認
            self.driver.find_element_by_xpath('//a[@href="/login"][@data-testid="login"]')
            print('LoginFailedError')
            return False
        except:
            return True

    def is_invalid_user(self):
        try:
            if self.is_temporarily_suspended():
                return True
            if self.has_to_change_password():
                return True
            if self.is_action_locked():
                return True
        except:
            return False

    def is_action_locked(self):
        try:
            self.driver.find_element_by_xpath("//*[contains(text(),'次のポリシーに違反')]")
            sleep(LOAD_WAIT_TIME)
            try:
                elem_continue_button = self.driver.find_element_by_xpath('//*[contains(text(),"を続ける")]')
                self.click_element(elem_continue_button)
                sleep(LOAD_WAIT_TIME)
            except:
                print('ContinueButtonClickError')

            print('ActionLocked')
            try:
                suspend_str = self.driver.find_element_by_xpath('//*[contains(text(), "と")][contains(text(), "時間")]').text
                print('制限される期間: ' + suspend_str)
            except:
                pass
            return True
        except:
            return False

    def is_temporarily_suspended(self):
        try:
            self.driver.find_element_by_xpath("//*[contains(text(),'一時的に制限されています')]")
            return True
        except:
            return False

    def has_to_change_password(self):
        try:
            self.driver.find_element_by_xpath("//*[contains(text(),'不自然なアクティビティ')]")
            return True
        except Exception as e:
            print(e)
            return False

    def update_cookies(self, screen_name):
        try:
            pickle.dump(
                self.driver.get_cookies(),
                open("cookies/cookies__{}.pkl".format(screen_name), "wb")
            )
            return True
        except Exception as e:
            print(e)
            return False

    # ============================================================
    # いいね送信者のリストを画面からスクレイピングする
    #
    def extract_likers_from_tweet(self, tweet_url):
        try:
            '''https://twitter.com/Jujutsu_Kaisen_/status/1331387120624168960/likes'''
            self.driver.get(tweet_url)
            tweet_url = tweet_url.replace('https://twitter.com/', '').split('/')
            user_name = tweet_url[0]
            tweet_id = tweet_url[2]
            sleep(5)
            try:
                element_good = self.driver.find_element_by_xpath(
                    "//a[contains(@href, '/{0}/status/{1}/likes')]".format(user_name, tweet_id))
                element_good.click()
                sleep(3)
            except Exception as e:
                print(e)
                pass
            for i in range(5):
                self.scroll_down_once()
                sleep(1)
            t = []
            element_list = self.driver.find_elements_by_xpath('//a[@role="link"]//span[contains(text(),"@")]')
            for element in element_list:
                element_text = element.text
                t.append(element_text.replace('@', ''))
            return t
        except Exception as e:
            print('LikerExtractionError')
            print(e)
            return None

    # ============================================================
    # 汎用的画面操作（プロフィール画面で実行するもの）
    #
    def click_element(self, element):
        """WebElementをクリック"""
        try:
            self.driver.execute_script('arguments[0].click();', element)
            return True
        except Exception as e:
            print(e)
            return False

    def click_follow_button(self):
        try:
            XPATH_FOLLOW_BUTTON = "//div[@role='button'][contains(@data-testid,'-follow')]"
            follow_button = self.driver.find_element_by_xpath(XPATH_FOLLOW_BUTTON)
            self.click_element(follow_button)
            print('Followed.')
            return True
        except:
            print('FollowClickError')
            return False

    def click_unfollow_button(self):
        try:
            XPATH_UNFOLLOW_BUTTON = "(//div[@role='button'][contains(@data-testid,'follow')])[1]"
            unfollow_button = self.driver.find_element_by_xpath(XPATH_UNFOLLOW_BUTTON)
            self.click_element(unfollow_button)
            return True
        except:
            print('UnfollowClickError')
            return False

    def click_unfollow_popup(self):
        try:
            XPATH_UNFOLLOW_POPUP = "//div[@role='button'][@data-testid='confirmationSheetConfirm']"
            self.click_element(self.driver.find_element_by_xpath(XPATH_UNFOLLOW_POPUP))
            return True
        except:
            print('UnfollowPopupClickError')
            return False

    def click_seemore_button(self):
        try:
            XPATH_SEEMORE_BUTTON = '(//div[@aria-label="もっと見る"][@role="button"])[1]'
            self.click_element(self.driver.find_element_by_xpath(XPATH_SEEMORE_BUTTON))
            return True
        except:
            print('SeemoreButtonClickError')
            return False

    def click_mute_button(self):
        try:
            self.click_seemore_button()
            sleep(1)
            XPATH_MUTE_MENU = '(//div[@data-testid="mute"])[1]'
            self.click_element(self.driver.find_element_by_xpath(XPATH_MUTE_MENU))
            return True
        except:
            print('MuteButtonClickError')
            return False

    # ============================================================
    # 自動いいね関連モジュール
    #
    def search_and_like(self, executor, options):
        NO_SEARCH_RESULT_LIMIT = 20
        print('============================================================')
        print('SearchAndLikeStarted: {}'.format(executor))
        total_count = 0
        while True:
            if total_count > options['total_like_limit']:
                break

            for word in options['keyword_list']:
                word = '{} {}'.format(word, options['ng_keyword_str'])
                self.explore_word(word)
                sleep(3)
                count = 0
                no_search_result_count = 0
                while True:
                    # 検索キーワード毎のアクション上限に達したら次のキーワードへ
                    if count > options['like_limit_per_kw']:
                        break
                    sleep(1)
                    try:
                        like_elements = self.driver.find_elements_by_xpath(
                            '//div[@data-testid="like"][contains(@aria-label,"いいねする")]'
                        )

                        # 検索結果に新規いいねがない状態
                        if like_elements == []:
                            no_search_result_count += 1
                            if no_search_result_count > NO_SEARCH_RESULT_LIMIT:
                                print('NO_SEARCH_RESULT_LIMIT Exceed')
                                self.driver.quit()
                                sys.exit()

                        print('{} LikeTargetsFound'.format(len(like_elements),))
                        for elem in like_elements:
                            # unlike状態のツイートがあればいいね操作実行
                            if self.click_element(elem):
                                print('SuccessfullyClickedLikeButton')
                                count += 1
                                total_count += 1
                                # 履歴の記録
                                db_models_temp.insert_like_history(executor, word)
                                print('executor:{} , total_liked: {}, local_liked:{}, datetime: {}'.format(
                                    executor,
                                    total_count,
                                    count,
                                    datetime.datetime.now()
                                ))
                                # total count judgement
                                if total_count > options['total_like_limit']:
                                    print('AllLikeDone')
                                    self.driver.quit()
                                    sys.exit()
                                # local count judgement
                                if count > options['like_limit_per_kw']:
                                    break
                                # like click sleep
                                sleep(
                                    options['sleep_base_sec'] + random.randint(0, options['sleep_rand_upper'])
                                )
                                # search result refreshing
                                if count % options['search_update_interval'] == 0:
                                    self.driver.refresh()
                                    print('RefreshingPage')
                                    break
                            else:
                                print('FailedClickingLikeButton')
                        if like_elements == []:
                            print('ScrollingDown')
                            self.scroll_down_once()
                            self.scroll_down_once()
                            self.scroll_down_once()
                            sleep(3)
                    except Exception as e:
                        print(e)
                        print('ScrollingDown')
                        self.scroll_down_once()
                        self.scroll_down_once()
                        self.scroll_down_once()
                        sleep(5)

                sleep(options['waiting'])

    def explore_word(self, word):
        self.driver.get('https://twitter.com/search?q={}&f=live'.format(word))
        sleep(LOAD_WAIT_TIME)
        self.driver.refresh()
        sleep(LOAD_WAIT_TIME)
        try:
            self.driver.find_element_by_xpath(
                "//*[contains(text(),'起きていることを見つけよう')]")
            self.driver.refresh()
            sleep(LOAD_WAIT_TIME)
        except selenium.common.exceptions.NoSuchElementException:
            pass
            try:
                self.driver.find_element_by_xpath(
                    "//*[contains(text(), '「いいね」しましょう')]")
                self.driver.refresh()
                sleep(LOAD_WAIT_TIME)
            except selenium.common.exceptions.NoSuchElementException:
                pass

    def scroll_down_once(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 3);")
        sleep(2)

    # ============================================================
    # 自動投稿関連モジュール
    #
    def post_message(self, text):
        try:
            self.driver.get('https://twitter.com/home')
            sleep(1)
            self.driver.find_element_by_xpath('//div[@aria-label="テキストをツイート"]').send_keys(text)
            sleep(1)
            self.driver.find_element_by_xpath('//div[@data-testid="tweetButtonInline"]').click()
        except Exception as e:
            print('PostMessageError')
            print(e)
            return False

    def post_img(self, filepath, text):
        try:
            # ツイートボタンをクリック
            tweet_button_elem = self.find_element_by_xpath('//div[@id="tweet-box-home-timeline"]')
            self.click_element(tweet_button_elem)
            sleep(8)
            # 画像添付
            self.find_element_by_xpath('//input[@data-original-title="画像/動画を追加"]').send_keys(filepath)
            # 文章追加
            self.find_element_by_xpath('//div[@aria-labelledby="tweet-box-home-timeline-label"]/p').send_keys(text)
            sleep(2)
            # ツイートボタンクリック
            self.find_element_by_xpath('//button[@class="tweet-action EdgeButton EdgeButton--primary js-tweet-btn"]').click()
            return True
        except Exception as e:
            print('PostImgTweetError')
            print(e)
            return False

    def get_trend_hashtag(self):
        try:
            self.driver.get('https://twitter.com/explore/tabs/trending')
            sleep(5)
            top_trend_word = self.driver.find_element_by_xpath(
                '((//div[@data-testid="trend"])[{}]//div[@dir="ltr"])[1]'.format(
                    random.randint(2, 15)
                )
            ).text
            print(top_trend_word)
            return top_trend_word
        except Exception as e:
            print('FetchingTrendWordError')
            print(e)
            return False

    # ============================================================
    # DM送信関連モジュール
    #
    def send_direct_message(self, receiver_name, message):
        try:
            self.driver.get('https://twitter.com/' + str(receiver_name))
            sleep(5)
            try:
                dm_button_elem = self.driver.find_element_by_xpath(
                    '//div[@data-testid="sendDMFromProfile"]')
                self.click_element(dm_button_elem)
            except:
                print('DmNotOpenedUser')
                return False
            sleep(5)
            msg_box_elem = self.driver.find_element_by_xpath(
                '//div[@data-testid="dmComposerTextInput"]')
            msg_box_elem.send_keys(message)
            sleep(3)
            # Enterキーを押す
            msg_box_elem.send_keys(Keys.ENTER)
            sleep(3)
            return True
        except Exception as e:
            print(e)
            return False


# ============================================================
# ターゲットの登録収集関連モジュール
#
def get_unfollow_targets(screen_name, max=20):
    api = twitter_api.twitter_api_ready()
    print('GettingUnfollowTargets ...')
    # フォロワー
    try:
        follower_ids = []
        for page in tweepy.Cursor(api.followers_ids, screen_name).pages():
            follower_ids.extend(page)
        sleep(1)
        # フォローしているユーザー
        friends_ids = []
        for page in tweepy.Cursor(api.friends_ids, screen_name).pages():
            friends_ids.extend(page)
        sleep(1)
        # 非相互フォローのリスト
        unfollow_target_id_list = [x for x in friends_ids if x not in follower_ids]
        print('UnfollowTargetCount: {}'.format(len(unfollow_target_id_list)))
    except Exception as e:
        print('APIError')
        print(e)
        return None
    try:
        print('GettingScreennameOfUnfollowTarget ...')
        unfollow_target_list = []
        for unfollow_target_id in unfollow_target_id_list[:max]:
            user = api.get_user(unfollow_target_id)
            user_screenname = user.screen_name
            print(user_screenname)
            unfollow_target_list.append(user_screenname)
            sleep(1)
    except Exception as e:
        print(e)
        return None
    return unfollow_target_list


def get_fresh_follow_targets(executor_name, seed_name_list, conditions, max=20):
    api = twitter_api.twitter_api_ready()
    try:
        print('SeedNames: {}'.format(str(seed_name_list)))
        # 種アカウントのフォロワーから、すでに登録または消費済みのidを弾く
        target_candidate_id_list = []
        for seed_name in seed_name_list:
            for page in tweepy.Cursor(api.followers_ids, seed_name).pages():
                target_candidate_id_list.extend(page)
        for target_id in target_candidate_id_list:
            while True:
                should_remove = False
                if db_models_temp.is_already_added_follow_target_id(executor_name, target_id):
                    should_remove = True
                    break
                if db_models_temp.is_already_consumed_id(executor_name, target_id):
                    should_remove = True
                    break
                if db_models_temp.is_in_trash(executor_name, target_id):
                    should_remove = True
                    break
                break
            if should_remove:
                target_candidate_id_list.remove(target_id)
    except Exception as e:
        print('APIError')
        print(e)
        return None

    print('GettingNameOfFollowTarget ...')
    follow_target_list = []
    follow_target_id_list = []
    for follow_target_id in target_candidate_id_list:
        sleep(1)
        should_append = True
        target_obj = api.get_user(follow_target_id)
        target_name = target_obj.screen_name
        target_profile = target_obj.description
        if target_obj.friends_count > 0:
            ff_ratio = float(int(target_obj.followers_count) / int(target_obj.friends_count))
        else:
            ff_ratio = 0
        # 直近のツイート時刻
        try:
            timelines = api.user_timeline(follow_target_id, count=1)
            for timeline in timelines:
                most_recent_tweet_time = timeline.created_at
        except:
            most_recent_tweet_time = None
        # condition judgement
        while True:
            should_append = True
            if ff_ratio > conditions['ff_upper_limit']:
                should_append = False
                break
            if ff_ratio < conditions['ff_lower_limit']:
                should_append = False
                break
            try:
                day_threshold = datetime.datetime.now() - datetime.timedelta(days=30 * conditions['month_threshold'])
                if most_recent_tweet_time < day_threshold:
                    should_append = False
                    break
            except:
                pass
            # keyword check user_profile
            break
        if should_append:
            if db_models_temp.insert_a_follow_target(executor_name, target_name, follow_target_id):
                follow_target_list.append(target_name)
                follow_target_id_list.append(follow_target_id)
                print('SuccessfullyInsertFreshFollowTarget: {}'.format(target_name))
            if len(follow_target_list) == max:
                break
        else:
            db_models_temp.insert_follow_target_trash(
                executor_name,
                target_name,
                follow_target_id
            )

    return follow_target_list


# from pykakasi import kakasi
# import re

# kakasi = kakasi()

# def convert_kanji_hiragana(text):
#     kakasi.setMode('J', 'H')
#     conv = kakasi.getConverter()
#     return conv.do(text)

# def judgment_japanese(text):
#     if re.search(r'[ぁ-んァ-ン]', convert_kanji_hiragana(text)):
#         return True
#     else:
#         return False
