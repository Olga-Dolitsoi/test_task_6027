import os
import pandas as pd


class ProcessRomi:
    def __init__(self):
        self._df_transactions = None
        self._df_marketing_costs = None
        self._merged_df = None

    # File names
    USER_TRANSACTIONS_FILE = 'Product analyst - File 1.xlsx'
    MARKETING_COSTS_FILE = 'Файл 2 fix.xlsx'

    # Product names (subscription types)
    PRODUCT_TENWORDS_1w_7_99_7FREE = 'tenwords_1w_7.99_7free'
    PRODUCT_TENWORDS_1w_9_99_OFFER = 'tenwords_1w_9.99_offer'
    PRODUCT_TENWORDS_LIFETIME_LIMITED_49_99 = 'tenwords_lifetime_limited_49.99'

    # Subscription (Product) prices
    PRICE_1_1w_7_99_7FREE = 0.0
    PRICE_NEXT_1w_7_99_7FREE = 7.99
    PRICE_1_1w_9_99_OFFER = 0.5
    PRICE_NEXT_1w_9_99_OFFER = 9.99
    PRICE_LIFETIME_LIMITED_49_99 = 49.99

    @property
    def df_transactions(self):
        return self._df_transactions

    @df_transactions.setter
    def df_transactions(self, df):
        self._df_transactions = df

    @property
    def merged_df(self):
        return self._merged_df

    @merged_df.setter
    def merged_df(self, df):
        self._merged_df = df

    @property
    def df_marketing_cost(self):
        return self._df_marketing_costs

    @df_marketing_cost.setter
    def df_marketing_cost(self, df):
        self._df_marketing_costs = df


    def extruct_data_to_df(self, file_name):
        """Extract excel by file name to df (both placed in current dir)
        :param file_name: Product analyst - File 1.xlsx or Файл 2.xlsx
        :type file_name: str"""
        current_dir = os.getcwd()
        if file_name == self.USER_TRANSACTIONS_FILE:
            self.df_transactions = pd.read_excel(f'{current_dir}/{file_name}')
        elif file_name == self.MARKETING_COSTS_FILE:
            self.df_marketing_cost = pd.read_excel(f'{current_dir}/{file_name}')

        else:
            print(f"Your file name seems to be wrong. Please check your file is in your working directory")


    def filter_by_product(self, product_name):
        """Filter df by product name (subscription type)
        :param product_name: product name (subscription type)
        (possible options in class constants)
        :type product_name: str"""
        self.df_transactions = self.df_transactions[self.df_transactions['product_id'] == product_name]

    def get_not_returned(self, ):
        """Get not refunded payments from user transactions"""
        self.df_transactions = self.df_transactions[self.df_transactions['refunded'] == False]

    def get_refunded(self):
        refunded = self.df_transactions['refunded'].value_counts(True)
        return refunded[True]


    def convert_date(self, df_transactions=True, df_marketing_costs=False):
        """Converts dates in selected df to datetime
        :param df_transactions: if true converts dates in df_transactions
        :type df_transactions: bool
        :param df_marketing_costs: if true converts dates in df_marketing_costs
        :type df_marketing_costs: bool"""
        if df_transactions:
            self.df_transactions['purchase_date'] = pd.to_datetime(self.df_transactions['purchase_date'])
        if df_marketing_costs:
            self.df_marketing_cost['date'] = pd.to_datetime(self.df_marketing_cost['date'])

    def date_to_month(self, df_transactions=True, df_marketing_costs=False):
        """Converts dates in selected df to month
        :param df_transactions: if true converts dates to month in df_transactions
        :type df_transactions: bool
        :param df_marketing_costs: if true converts dates to month in df_marketing_costs
        :type df_marketing_costs: bool"""
        if df_transactions:
            self.df_transactions['month'] = self.df_transactions['purchase_date'].dt.to_period('M')
        if df_marketing_costs:
            self.df_marketing_cost['month'] = self.df_marketing_cost['date'].dt.to_period('M')

    def set_transaction_nums_for_users(self):
        """Assign new column 'transaction_number' for each user transaction"""
        self.df_transactions = self.df_transactions.sort_values(by=['user_id', 'purchase_date'])
        self.df_transactions['transaction_number'] = self.df_transactions.groupby('user_id').cumcount() + 1


    def assign_amount(self, row):
        """Assigns amount of transaction depending on subscription and transaction number based on pricing
        Apply only to self.df_transactions when transaction numbers assigned"""
        product = row['product_id']
        transaction_number = row['transaction_number']

        if product == 'tenwords_1w_7.99_7free':
            if transaction_number == 1:
                return self.PRICE_1_1w_7_99_7FREE
            else:
                return self.PRICE_NEXT_1w_7_99_7FREE

        elif product == 'tenwords_1w_9.99_offer':
            if transaction_number == 1:
                return self.PRICE_1_1w_9_99_OFFER
            else:
                return self.PRICE_NEXT_1w_9_99_OFFER

        elif product == 'tenwords_lifetime_limited_49.99':
            return self.PRICE_LIFETIME_LIMITED_49_99

    def assign_amount_to_df(self):
        """Creates new amount column to df and fill it based on pricing"""
        self.df_transactions['amount'] = self.df_transactions.apply(self.assign_amount, axis=1)

    def count_conversion_first_second_payment(self):
        """Count percent of users who did second payment
        :return conversion_rate (prcent of users who did second payment)"""
        first_payment_users = self.df_transactions[self.df_transactions['transaction_number'] == 1]['user_id'].unique()
        second_payment_users = self.df_transactions[self.df_transactions['transaction_number'] >= 2]['user_id'].unique()
        conversion_rate = len(set(second_payment_users)) / len(set(first_payment_users)) * 100
        return conversion_rate

    def get_arpu(self):
        """Get average user revenue per month"""
        # self.df_transactions.reset_index(inplace=True, drop=True)
        total_revenue_per_day = self.df_transactions.groupby(self.df_transactions['purchase_date'].dt.date)['amount'].sum().reset_index()
        unique_users_per_day = self.df_transactions.groupby(self.df_transactions['purchase_date'].dt.date)['user_id'].nunique().reset_index()
        daily_data = pd.merge(total_revenue_per_day, unique_users_per_day, on='purchase_date')
        daily_data['arpu'] = daily_data['amount'] / daily_data['user_id'].nunique()
        avg_arpu = daily_data['arpu'].mean()
        return daily_data, avg_arpu


    def get_lifetime(self):
        user_lifetime = self.df_transactions.groupby('user_id')['purchase_date'].agg(['min', 'max']).reset_index()
        user_lifetime['lifetime_days'] = (user_lifetime['max'] - user_lifetime['min']).dt.days
        average_lifetime_months = user_lifetime['lifetime_days'].mean()
        return average_lifetime_months


    @staticmethod
    def predict_ltv(arpu_day, awg_lifetime, refund_rate):
        ltv_180 = min(awg_lifetime, 180) * arpu_day * (1 - refund_rate)
        return ltv_180



    def prepare_cost_data(self):
        self.df_marketing_cost.drop(['cost_wrong', 'type', 'format'], axis=1, inplace=True)

    def merge_dataframes(self):
        self.df_transactions = self.df_transactions.groupby(['purchase_date', 'country_code', 'media_source']).agg({
            'amount': 'sum'
        }).reset_index()
        self.df_transactions.rename(columns={'purchase_date': 'date'}, inplace=True)
        self.merged_df = pd.merge(self.df_transactions, self.df_marketing_cost,
                             left_on=['date', 'media_source', 'country_code'],
                             right_on=['date', 'media_source', 'country_code'])



    def count_romi(self):
        self.merged_df['romi'] = ((self.merged_df['amount'] - self.merged_df['costs']) / self.merged_df['costs']) * 100


def task_1_2():
    task = ProcessRomi()

    # Prepare df
    task.extruct_data_to_df(task.USER_TRANSACTIONS_FILE)
    task.set_transaction_nums_for_users()
    task.assign_amount_to_df()
    task.extruct_data_to_df(task.MARKETING_COSTS_FILE)
    task.prepare_cost_data()
    task.convert_date(df_transactions=True, df_marketing_costs=True)
    task.merge_dataframes()
    task.count_romi()
    task.merged_df.to_excel('romi_result.xlsx', index=False)


"""Було обрано розрахунок LTV на основі ARPU та середнього часу життя клієнта, 
оскільки цей підхід є простим, точним та базується на історичних даних. 
Ми мали всі необхідні дані, що дозволило зробити якісну оцінку без використання складних моделей. 
Це забезпечило швидкий і реалістичний прогноз доходу від клієнтів."""

def task_1_1():
    task = ProcessRomi()

    # Prepare df
    task.extruct_data_to_df(task.USER_TRANSACTIONS_FILE)
    task.convert_date()
    task.set_transaction_nums_for_users()
    task.assign_amount_to_df()

    # Get refunded rate
    refund_rate = task.get_refunded()

    # Filter df
    task.filter_by_product(task.PRODUCT_TENWORDS_1w_9_99_OFFER)
    task.get_not_returned()

    # Find LTV components
    dayly_data, arpu = task.get_arpu()
    avg_lifetime = task.get_lifetime()

    ltv_forecast = task.predict_ltv(arpu_day=arpu, awg_lifetime=avg_lifetime, refund_rate=refund_rate)
    return ltv_forecast

def task_1_0():
    task = ProcessRomi()

    # Prepare df
    task.extruct_data_to_df(task.USER_TRANSACTIONS_FILE)
    task.convert_date()
    task.set_transaction_nums_for_users()
    task.assign_amount_to_df()

    # Filter df
    task.get_not_returned()
    task.filter_by_product(task.PRODUCT_TENWORDS_1w_9_99_OFFER)

    # Find conversion
    conversion = task.count_conversion_first_second_payment()

    return conversion

res1 = task_1_0()
res2 = task_1_1()

print(f"First-second payment user conversion: {res1:.2f}%")
print (f'LTV forecast based on ARPU and avarage lifetime {res2:.2f}')
