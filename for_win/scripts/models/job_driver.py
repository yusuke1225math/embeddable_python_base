import datetime

from models import db_models_temp
from models import sheet_fetch

DEFAULT_LIMIT = 30
DEFAULT_INTERVAL = 60
DEFAULT_TARGETS = None


class SingleJob():
    def __init__(self, sheet_monitor_status, executor_screen_name, job_name, limit=DEFAULT_LIMIT, execution_interval=DEFAULT_INTERVAL):
        self.executor_screen_name = executor_screen_name
        self.executor_password = sheet_monitor_status.get_password(executor_screen_name)
        self.job_name = job_name
        self.job_done = False
        self.last_execution_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        self.execution_count = 0
        self.execution_limit = limit
        self.execution_targets = None
        self.execution_interval = execution_interval

    def is_done(self):
        return self.job_done

    def terminate(self):
        try:
            self.job_done = True
            return True
        except Exception as e:
            print('JobTerminatingError')
            print(e)
            return False

    def get_executor_screen_name(self):
        return self.executor_screen_name

    def get_executor_password(self):
        return self.executor_password

    def get_job_name(self):
        return self.job_name

    def get_job_done(self):
        return self.job_done

    def get_last_execution_datetime(self):
        return self.last_execution_datetime

    def get_execution_count(self):
        return self.execution_count

    def get_execution_limit(self):
        return self.execution_limit

    def get_execution_targets(self):
        return self.execution_targets

    def get_execution_interval(self):
        return self.execution_interval

    def set_execution_targets(self, targets):
        """
        targetsをリスト型で与えて、jobの実行対象を登録する
        """
        try:
            self.execution_targets = targets
            return True
        except Exception as e:
            print(e)
            return False

    def set_execution_interval(self, interval_sec):
        """
        jobの実行間隔sleep秒を設定
        """
        try:
            self.execution_interval = interval_sec
            return True
        except Exception as e:
            print(e)
            return False

    def set_execution_limit(self, limit):
        """
        jobの実行間隔sleep秒を設定
        """
        try:
            self.execution_limit = limit
            return True
        except Exception as e:
            print(e)
            return False

    def print_job_result(self):
        try:
            print('------------------------------')
            print('job_type: {}'.format(self.job_name))
            print('Executor: {}'.format(self.executor_screen_name))
            print('RemainingTargetCount: {}'.format(str(len(self.execution_targets))))
            print('AlreadyDoneCount: {}'.format(str(self.execution_count)))
            print('LastExecutionDatetime: {}'.format(str(self.last_execution_datetime)))
            return True
        except Exception as e:
            print(e)
            return False
