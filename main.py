import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def get_relative_change(df):
    """
    Return the dataframe with the percent change between this month and last month
    :param df: Dataframe with raw values
    :return: Dataframe with the relative differences
    """
    month, year = df.dim_month, df.dim_year
    df = df.drop(columns=['dim_year', 'dim_month'])
    df = df.pct_change()[1:]
    df['type'] = 'relative_difference'
    df['dim_month'] = month
    df['dim_year'] = year
    return df


def get_absolute_change(df):
    """
    Return the difference of the current month from the prior month
    :param df: Dataframe of raw values
    :return: Dataframe with the differences
    """
    month, year = df.dim_month, df.dim_year
    df = df.drop(columns=['dim_year', 'dim_month'])
    df = df.diff(1)[1:]
    df['type'] = 'absolute_difference'
    df['dim_month'] = month
    df['dim_year'] = year
    return df


def get_lagged_month(df):
    """
    Return the previous month's value
    :param df: Dataframe of raw values by month
    :return: Dataframe of shifted values
    """
    month, year = df.dim_month, df.dim_year
    df = df.drop(columns=['dim_year', 'dim_month'])
    df = df.shift(1)[1:]
    df['type'] = 'last_month'
    df['dim_month'] = month
    df['dim_year'] = year
    return df


def create_viz(session_agg, MoM):
    """
    Creating the visualizations to be utilised in the presentation
    :param session_agg: first xslx sheet as a Dataframe
    :param MoM: second xslx sheet as a Dataframe
    :return: N/A
    """
    session_agg['dim_month'] = session_agg['dim_month'].astype(str)
    MoM['dim_month'] = MoM['dim_month'].astype(str)
    fig = sns.relplot(data=session_agg, x='dim_month', y='transactions', hue='dim_deviceCategory', kind='line')
    fig.set(xlabel='Month', ylabel='Transactions')
    fig._legend.set_title('Device')
    plt.savefig('transactions.png')

    fig, ax = plt.subplots()
    fig = sns.relplot(data=session_agg, x='dim_month', y='ECR', hue='dim_deviceCategory', kind='line')
    fig.set(xlabel='Month', ylabel='ECR')
    fig._legend.set_title('Device')
    plt.savefig('ECR.png')

    fig, ax = plt.subplots()
    fig = sns.relplot(data=MoM, x='dim_month', y='purchase_rate', kind='line', hue='type')
    fig.set(xlabel='Month', ylabel='Purchase Rate')
    fig._legend.set_title('Data Format')
    plt.savefig('Purchase_Rate.png')


if __name__ == '__main__':
    cart = pd.read_csv('~/Downloads/DataAnalyst_Ecom_data_addsToCart.csv')
    session = pd.read_csv('~/Downloads/DataAnalyst_Ecom_data_sessionCounts.csv')

    session.dim_date = pd.to_datetime(session.dim_date)
    session['dim_month'] = session.dim_date.dt.month
    session['dim_year'] = session.dim_date.dt.year

    session_agg = pd.DataFrame(session.groupby(['dim_deviceCategory',
                                                'dim_month',
                                                'dim_year'])['transactions',
                                                             'QTY',
                                                             'sessions'].sum()).reset_index()

    session_agg['ECR'] = session_agg['transactions'] / session_agg['sessions']
    session_agg['items_per_transaction'] = session_agg['QTY'] / session_agg['transactions']

    session_agg = session_agg.sort_values(by=['dim_year', 'dim_month'], ascending=True)

    MoM = pd.DataFrame(session.groupby(['dim_month'])['transactions',
                                                      'QTY',
                                                      'sessions'].sum()).reset_index()
    MoM['ECR'] = MoM['transactions'] / MoM['sessions']
    MoM['items_per_transaction'] = MoM['QTY'] / MoM['transactions']

    MoM = pd.merge(MoM, cart.tail(2), on='dim_month').sort_values(by=['dim_year',
                                                              'dim_month'], ascending=True)

    MoM['purchase_rate'] = MoM['QTY'] / MoM['addsToCart']

    relative = get_relative_change(MoM)
    absolute = get_absolute_change(MoM)
    lagged = get_lagged_month(MoM)

    MoM['type'] = 'current_month'
    final_MoM = pd.concat([MoM[1:], lagged, relative, absolute], axis=0)

    create_viz(session_agg, final_MoM.reset_index(drop=True))

    with pd.ExcelWriter('final_sheet.xlsx') as writer:
        session_agg.to_excel(writer, 'Aggregations', index=False)
        final_MoM.to_excel(writer, 'Month-over-Month', index=False)
