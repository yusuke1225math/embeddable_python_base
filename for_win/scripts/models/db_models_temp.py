import datetime
import sqlite3

from config import db_settings


# class LikeHistory():


# class UnfollowHistory():


# class FollowHistory():


# class DmHistory():


# class DmTarget():


# class FollowTarget():


# class Target():


# db related functions template
# def ():
#     try:
#         conn = sqlite3.connect(db_settings.DB_PATH)
#         cur = conn.cursor()
#         cur.execute(
#             ';',
#             (,)
#         )
#         conn.commit()
#     except Exception as e:
#         print(e)
#     finally:
#         try:
#             conn.close()
#         except:
#             pass
#
def is_sufficiently_old_follow(executor, followee, expiration=48):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            '''select created_at from follow_histories where
            follow_executor = ? and followee = ?;
            ''',
            (executor, followee)
        )
        results = cur.fetchall()
        true_or_false = True
        if results == []:
            true_or_false = False
        else:
            results = [x[0] for x in results]
            result_dt_str = results[0]
            result_dt = datetime.strptime(result_dt_str, '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > result_dt + datetime.timedelta(hours=expiration):
            true_or_false = True
        else:
            true_or_false = False
    except Exception as e:
        print(e)
    finally:
        try:
            conn.close()
        except:
            pass
        return true_or_false


def is_automatically_followed(executor, followee):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            '''select created_at from follow_histories where
            follow_executor = ? and followee = ?;
            ''',
            (executor, followee)
        )
        results = cur.fetchall()
        true_or_false = True
        if results == []:
            true_or_false = False
    except Exception as e:
        print(e)
    finally:
        try:
            conn.close()
        except:
            pass
        return true_or_false


#
# like_historiesテーブル
#
def insert_like_history(executor, query):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'insert into like_histories (like_executor, query) values (?, ?);',
            (
                executor,
                query
            )
        )
        conn.commit()
    except Exception as e:
        print('ErrorCouldNotInsertlikeHistory')
        print(e)
        return False
    finally:
        try:
            conn.close()
            # print('SuccessfullyInsertlikeHistory')
            return True
        except Exception as e:
            print('ErrorCouldNotInsertlikeHistory')
            print(e)
            return False


#
# follow_historiesテーブル
#
def insert_follow_histories(executor_id, history_list):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        sql = 'insert into follow_histories (follow_executor, followee) values (?, ?);'
        args = []
        for history in history_list:
            args.append((executor_id, history))
        cur.executemany(sql, args)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        try:
            conn.close()
        except:
            pass


def insert_follow_history(executor, followee):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'insert into follow_histories (follow_executor, followee) values (?, ?);',
            (
                executor,
                followee
            )
        )
        conn.commit()
    except Exception as e:
        print('ErrorCouldNotInsertFollowHistory')
        return False
    finally:
        try:
            conn.close()
            print('SuccessfullyInsertFollowHistory')
            return True
        except Exception as e:
            print('ErrorCouldNotInsertFollowHistory')
            return False


#
# follow_targetsテーブル
#
def insert_follow_targets(executor, target_list, ids=None):
    count = 0
    for i, target in enumerate(target_list):
        conn = sqlite3.connect(db_settings.DB_PATH)
        try:
            cur = conn.cursor()
            if ids is None:
                cur.execute(
                    '''insert into follow_targets
                    (follow_executor, followee) values (?, ?);''',
                    (executor, target)
                )
            else:
                cur.execute(
                    '''insert into follow_targets
                    (follow_executor, followee, followee_id) values (?, ?, ?);''',
                    (executor, target, ids[i])
                )
            conn.commit()
            count += 1
        except Exception as e:
            print(e)
        finally:
            try:
                conn.close()
            except:
                pass
    return count


def insert_a_follow_target(executor, target, target_id=None):
    conn = sqlite3.connect(db_settings.DB_PATH)
    try:
        cur = conn.cursor()
        if target_id is None:
            cur.execute(
                '''insert into follow_targets
                (follow_executor, followee) values (?, ?);''',
                (executor, target)
            )
        else:
            cur.execute(
                '''insert into follow_targets
                (follow_executor, followee, followee_id) values (?, ?, ?);''',
                (executor, target, target_id)
            )
        conn.commit()
        result = True
    except Exception as e:
        print(e)
        result = False
    finally:
        try:
            conn.close()
        except:
            pass
    return result


def consume_a_follow_target(executor, followee):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'update follow_targets set consumed_at = ? where follow_executor = ? and followee = ?;',
            (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                executor,
                followee
            )
        )
        conn.commit()
    except Exception as e:
        print('ErrorCouldNotConsumeFollowTarget')
        print(e)
    finally:
        try:
            conn.close()
            print('SuccessfullyConsumedFollowTarget')
            return True
        except Exception as e:
            print('ErrorCouldNotConsumeFollowTarget')
            print(e)
            return False


def insert_follow_target_trash(executor, followee_name, followee_id):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            '''insert into follow_targets_trash
            (follow_executor, followee, followee_id) values (?, ?, ?);''',
            (
                executor,
                followee_name,
                followee_id
            )
        )
        conn.commit()
    except Exception as e:
        print('ErrorCouldNotInsertFollowTrash')
        return False
    finally:
        try:
            conn.close()
            print('SuccessfullyInsertFollowTrash')
            return True
        except Exception as e:
            print('ErrorCouldNotInsertFollowTrash')
            return False


def is_in_trash(executor, followee_id):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'select followee_id from follow_targets_trash where follow_executor = ?;',
            (executor,)
        )
        results = cur.fetchall()
        alreadies = [x[0] for x in results]
        if followee_id in alreadies:
            value = True
        else:
            value = False
    except:
        value = False
    finally:
        try:
            conn.close()
        except:
            pass
        return value


def is_already_added_follow_target_id(executor, followee_id):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'select followee_id from follow_targets where follow_executor = ?;',
            (executor,)
        )
        results = cur.fetchall()
        alreadies = [x[0] for x in results]
        if followee_id in alreadies:
            value = True
        else:
            value = False
    except:
        value = False
    finally:
        try:
            conn.close()
        except:
            pass
        return value


def is_already_consumed_id(executor, followee_id):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            '''
            select followee_id from follow_histories where follow_executor = ?;
            ''',
            (executor,)
        )
        results = cur.fetchall()
        alreadies = [x[0] for x in results]
        if followee_id in alreadies:
            value = True
        else:
            value = False
    except:
        value = False
    finally:
        try:
            conn.close()
        except:
            pass
        return value


def is_already_consumed(executor, followee):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'select followee from follow_histories where follow_executor = ?;',
            (executor,)
        )
        results = cur.fetchall()
        alreadies = [x[0] for x in results]
        if followee in alreadies:
            value = True
        else:
            value = False
    except:
        value = False
    finally:
        try:
            conn.close()
        except:
            pass
        return value


def select_follow_targets(executor):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'select followee from follow_targets where follow_executor = ? and consumed_at is NULL;',
            (executor,)
        )
        followees = cur.fetchall()
        followees = [x[0] for x in followees]
    except:
        followees = None
    finally:
        try:
            conn.close()
        except:
            pass
        return followees


#
# dm_targetsテーブル
#
def insert_dm_targets(sender, recipient_list, ids=None):
    count = 0
    for i, target in enumerate(recipient_list):
        conn = sqlite3.connect(db_settings.DB_PATH)
        try:
            cur = conn.cursor()
            if ids is None:
                cur.execute(
                    '''insert into dm_targets
                    (sender, recipient) values (?, ?);''',
                    (sender, target)
                )
            else:
                cur.execute(
                    '''insert into dm_targets
                    (sender, recipient, recipient_id) values (?, ?, ?);''',
                    (sender, target, ids[i])
                )
            conn.commit()
            count += 1
        except Exception as e:
            print(e)
        finally:
            try:
                conn.close()
            except:
                pass
    return count


def select_dm_targets(sender):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'select recipient from dm_targets where sender = ? and consumed_at is NULL;',
            (sender,)
        )
        recipients = cur.fetchall()
        recipients = [x[0] for x in recipients]
    except:
        recipients = None
    finally:
        try:
            conn.close()
        except:
            pass
        return recipients


def consume_a_dm_target(sender, recipient, status='successful'):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'update dm_targets set consumed_at = ?, status = ? where sender = ? and recipient = ?;',
            (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                status,
                sender,
                recipient
            )
        )
        conn.commit()
    except Exception as e:
        print('ErrorCouldNotConsumeDMTarget')
        print(e)
    finally:
        try:
            conn.close()
            print('SuccessfullyConsumedDMTarget')
            return True
        except Exception as e:
            print('ErrorCouldNotConsumeDMTarget')
            print(e)
            return False


#
# dm_historiesテーブル
#
def insert_dm_history(sender, recipient, status='successful'):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        sql = 'insert into dm_histories (sender, recipient, status) values (?, ?, ?);'
        args = (
            sender,
            recipient,
            status
        )
        cur.execute(sql, args)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        try:
            conn.close()
        except:
            pass


def is_already_sent(sender, recipient):
    try:
        conn = sqlite3.connect(db_settings.DB_PATH)
        cur = conn.cursor()
        sql = 'select * from dm_histories where sender = ? and recipient = ?;'
        args = (sender, recipient)
        cur.execute(sql, args)
        results = cur.fetchall()
        if results == []:
            value = False
        else:
            value = True
    except Exception as e:
        print(e)
    finally:
        try:
            conn.close()
            return value
        except:
            return False


# ============================================================
# csv読み込み系モジュール
#
def get_unfollow_targets_from_csv(username):
    """csvからunfollow_targetを取り出す"""
    try:
        with open('list/unfollow_target__{}.csv'.format(username), 'r') as f_u:
            targets = f_u.read().split('\n')
        try:
            targets.remove('\n')
        except:
            pass
        try:
            targets.remove('')
        except:
            pass
        return targets
    except Exception as e:
        print('GettingUnfollowTargetsError')
        print(e)
        return []


def update_unfollow_target_csv(screen_name, targets):
    try:
        with open('list/unfollow_target__{}.csv'.format(screen_name), 'w') as f_n:
            f_n.write('\n'.join(targets))
        return True
    except Exception as e:
        print('UpdatingUnfollowTargetsError')
        print(e)
        return False
