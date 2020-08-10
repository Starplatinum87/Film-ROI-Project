import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns 

from scipy.stats import normaltest
from scipy.stats import shapiro
from scipy.stats import anderson
from scipy.stats import probplot

from sklearn.preprocessing import power_transform
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import HuberRegressor

import statsmodels.api as sm
from patsy import dmatrices



# Function to test whether all of the encodings are correct
def check_genres(df):   
    encoding_results = [] # Empty list that will hold the True/False results of genre encodings for each title
    # Loop through every row of the df checking whether there is a 1 in the column of the same name of each genre
    for i in range(len(df)):
        genres_list = df.iloc[i].genres # List of all genres for each title
        results_list = [] # Empty list to hold the results for checking each genre
        # Loop through each genre and append True to results_list if that column has a 1 and False otherwise
        for genre in genres_list:
            if df.loc[i, genre] == 1:
                results_list.append(True)
            else:
                results_list.append(False)
        # Check the results_list for any instance of False
        # If so append False to the encoding_results list, otherwise append True
        for result in results_list:
            if result == False:
                encoding_results.append(False)
                break
            else:
                continue
        encoding_results.append(True)
    # Check the encoding_results list for any instance of False. If so return False.
    # If no instance of False is in the entire list, return True
    for result in encoding_results:
        if result == False:
            return print("One of the encodings is incorrect!")
        else:
            continue
    return print("All encodings are correct!")

def transform_data(data, transform='log'):
    if transform == 'log':
        data = np.log(data)
    elif transform == 'box-cox':
        data = pd.DataFrame(power_transform(data, method='box-cox'), columns = data.columns)
    elif transform =='yeo-johnson':
        data = pd.DataFrame(power_transform(data, method='yeo-johnson'), columns = data.columns)
    else:
        pass 
    return data  

def plot_histogram(data):
    """Plot histogram"""
    plt.figure(figsize=(16,8))
    sns.distplot(data)
    plt.title("Test Histogram")
    plt.show() 

def plot_QQ(data):
    """Plot Q-Q plot to visually investigate normality"""
    plt.figure(figsize=(16,8))
    probplot(data, dist='norm', plot=plt)
    plt.title("Q-Q Plot")
    plt.show()
    print()   

def shapiro_wilk_test(data, alpha=0.05):
    print('Shapiro-Wilk Test Results')
    features = []
    statistics = []
    pvalues = []
    normal = []
    alpha = alpha
    output_df = pd.DataFrame(columns=['Features', 'Statistics', 'P-Values', 'Normal'], )
    for feature in list(data.columns):
        stat, p = shapiro(data[feature])
        features.append(feature)
        statistics.append(round(stat, 3))
        pvalues.append(round(p, 3))
        if p > alpha:
            normal.append('YES (Fail to Reject H0)')
        else: 
            normal.append('NO (Reject H0)')
    output_df['Features'] = features
    output_df['Statistics'] = statistics
    output_df['P-Values'] = pvalues
    output_df['Normal'] = normal

    return output_df 


def dagostino_test(data, alpha=0.05):
    print("D'Agostino and Pearson's Test Results")
    features = []
    statistics = []
    pvalues = []
    normal = []
    alpha = alpha
    output_df = pd.DataFrame(columns=['Features', 'Statistics', 'P-Values', 'Normal'], )
    for feature in list(data.columns):
        stat, p = normaltest(data[feature])
        features.append(feature)
        statistics.append(round(stat, 3))
        pvalues.append(round(p, 3))
        if p > alpha:
            normal.append('YES (Fail to Reject H0)')
        else: 
            normal.append('NO (Reject H0)')
    output_df['Features'] = features
    output_df['Statistics'] = statistics
    output_df['P-Values'] = pvalues
    output_df['Normal'] = normal

    return output_df 


def anderson_darling_test(data):
    result = anderson(data)
    print("Anderson-Darling Test Results")
    print('Statsistic: %.3f' % result.statistic)
    # p = 0
    for i in range(len(result.critical_values)):
        sl, cv = result.significance_level[i], result.critical_values[i]
        if result.statistic < result.critical_values[i]:
            print('%.3f: %.3f, data looks normal (fail to reject H0)' % (sl, cv))
        else:
            print('%.3f: %.3f, data does not look normal (reject H0)' % (sl, cv))
   

def normality(data, transform='yeo-johnson'):
    """
    Battery of tests for normality including a histogram, Q-Q plot, Shapiro-Wilk, D'Agostino and Person's, and Anderson-Darling tests.
    Reference: https://machinelearningmastery.com/a-gentle-introduction-to-normality-tests-in-python/
    """
    # Transform data
    data = transform_data(data, transform=transform)

    # Plot histogram
    plot_histogram(data)

    # Plot Q-Q Plot
    plot_QQ(data)
    
    # Shapiro-Wilk Test
    shapiro_wilk_test(data)
        
    # D'Agostino's K^2 Test
    dagostino_test(data)
        
    # Anderson-Darling Test
    anderson_darling_test(data)


def create_dmatrices(df):
    # Create OLS formula for dmatrices from df columns
    dformula = 'target ~ '
    dformula = dformula + df.columns[1]
    for column in df.columns[2:]:
        dformula = dformula + ' + ' + str(column)

    # Define target and variables using dmatrices and dformula
    y, X = dmatrices(dformula, data=df, return_type='dataframe')

    return y, X

def fit_ols_model(y, X):
    # Create the OLS model instance
    ols_model = sm.OLS(y, X)
    # Fit the model to this data
    ols_fitted = ols_model.fit()

    return ols_fitted   

def get_residuals(df, ols_fitted):
    # Create residuals df
    data = pd.DataFrame()
    data['predict'] = ols_fitted.predict()
    data['resid'] = df['target'] - data.predict

    return data

def plot_residuals(data):
    # Plot residuals
    plt.figure(figsize=(16, 8))
    sns.residplot('predict', 'resid', data=data)
    plt.title("Residuals Plot")
    plt.show()  

def run_ols_plots(df):
    """
    Run OLS, plot residuals and Q-Q of residuals
    """

    y, X = create_dmatrices(df)

    ols_fitted = fit_ols_model(y, X)

    # Print a summary of the modeled data
    print(ols_fitted.summary())

    # Create dataframe of predictions and residuals
    data = get_residuals(df, ols_fitted)

    # Plot residuals
    plot_residuals(data)

    # Q-Q Plot of residuals
    plot_QQ(data['resid'])

    # Shapiro-Wilk Test
    stat, p = shapiro(data['resid'])
    alpha = 0.05
    print('Shapiro-Wilk Test Results')
    print('Statistics: {}, P-Value: {}'.format(round(stat, 3), round(p, 3)))
    if p > alpha:
        print('Data looks normal (Fail to Reject H0)')
    else: 
        print('Data does not look normal (Reject H0)')
    print()
        
    # D'Agostino's K^2 Test
    stat, p = normaltest(data['resid'])
    alpha = 0.05
    print("D'Agostino/Pearson Test Results")
    print('Statistics: {}, P-Value: {}'.format(round(stat, 3), round(p, 3)))
    if p > alpha:
        print('Data looks normal (Fail to Reject H0)')
    else: 
        print('Data does not look normal (Reject H0)')
    print()
       
    # Anderson-Darling Test
    anderson_darling_test(data['resid'])


def split_and_validate(df, test_size=0.2, random_state=42):
    y = df.loc[:, df.columns[0]]
    X = df.loc[:, df.columns[1:]]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, random_state=random_state)

    # Fit linear model
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    
    score = lr_model.score(X_val, y_val)

    # Results
    print('Validation R2 Score: {}'.format(score))
    print('Feature Coefficients: \n')
    for feature, coef in zip(X.columns, lr_model.coef_):
        print(feature, ':', f'{coef:.2f}')

def check_outliers(df, multiplier=3):
    """
    Function to check for outliers in a dataframe.

    Parameters
    ----------
    data_series : pandas series
        Pandas Series containing the values to be used in calculating outliers
    target : dataframe
        DataFrame where outliers will be removed
    multiplier: int
        Factor of the IQR 

    Returns
    -------
    outlier_df : DataFrame
        DataFrame of outlier values 
    """
    # Data lists for dataframe
    features = []
    total_outliers = []
    high_outliers = []
    low_outliers = []

    # Empty dataframe with columms
    outlier_df = pd.DataFrame(columns=['features', 'total_outliers', 'high_outliers', 'low_outliers'])

    # Loop to gather outlier data for each feature
    for feature in list(df.columns):
        data_series = df[feature]
        features.append(feature)

        # Define IQR
        iqr = data_series.quantile(0.75) - data_series.quantile(0.25)

        # Define the outlier values
        outlier_value = iqr * multiplier
        high_outlier = data_series.quantile(0.75) + outlier_value
        low_outlier = data_series.quantile(0.25) - outlier_value

        # Generate count of outliers and append to outlier_count list
        count = df.loc[(data_series > high_outlier) | (data_series < low_outlier)].shape[0]
        total_outliers.append(count)

        # Generate counts of high and low outliers and append to lists
        high_count = df.loc[data_series > high_outlier].shape[0]
        high_outliers.append(high_count)
        low_count = df.loc[data_series < low_outlier].shape[0]
        low_outliers.append(low_count)

    outlier_df['features'] = features
    outlier_df['total_outliers'] = total_outliers
    outlier_df['high_outliers']= high_outliers
    outlier_df['low_outliers'] = low_outliers

    return outlier_df


def remove_outliers(df_column, df, multiplier=3):
    """
    Function to remove outliers from a DataFrame and return the updated DataFrame. Takes a 
    pandas Series as an input, calculates the IQR based on the values in the Series then 
    the outlier values based on whether or not a value is under or over the IQR * multiplier
    value. 

    Parameters
    ----------
    data_series : pandas series
        Pandas Series containing the values to be used in calculating outliers
    target : dataframe
        DataFrame where outliers will be removed
    multiplier: int
        Factor of the IQR 

    Returns
    -------
    trimmed_df : DataFrame
        DataFrame with indices corresponding to outlier values removed.    
    """

    # Create list of indices to drop
    iqr = df_column.quantile(0.75) - df_column.quantile(0.25)
    outlier_value = iqr * multiplier
    high_outlier = df_column.quantile(0.75) + outlier_value
    low_outlier = df_column.quantile(0.25) - outlier_value

    outlier_index = df.loc[(df_column > high_outlier) | (df_column < low_outlier)].index
    drop_df = df.drop(index=outlier_index)

    return drop_df
