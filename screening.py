import os
#os.chdir('/Users/tinglam/Documents/GitHub/stock_screener')
import pandas as pd
from statements_scraper import scrape_statements, company_name
pd.options.mode.chained_assignment = None 
pd.options.display.float_format = "{:,.2f}".format


def value_to_score(value, classification = {}):
    """
    Parameters:
    classification: input a dictionary, in the format of lower boundary : score
    
    Output:
    return the score as float
    
    Example:
    value_to_score(0.31,{0:0,0.1:1,0.2:1.5,0.3:2.5,0.4:3.75,0.5:4.5,0.6:5}) --> return 2.5
    """
    for threshold in classification.keys():
        if threshold <= value:
            score = classification.get(threshold)
    return score

def weighted_average(row):
    return row[-1] * 0.7 + row[-2] * 0.2 + row[-1] * 0.1

def standard_deviation(row):
    return row.std()


def score_calculation(ticker):
    # Read the dataframe
    database = scrape_statements(str(ticker))
    summary_df = pd.DataFrame(columns=database.columns)
    score_df = pd.DataFrame(columns = ['Reference Value','Score','Weights','Weighted Score'])

    # Part 1: Sales performance
    ## 1a) Top Line Growth
    name = '1a) Top Line Growth'
    summary_df.loc['Turnover Growth (%)'] = database.loc['Total Turnover'].pct_change() * 100
    value = weighted_average(summary_df.loc['Turnover Growth (%)'])
    score = value_to_score(value,{-999:-3,-5:-1,0:0,10:1,20:1.5,30:2.5,40:3.75,50:4.5,60:5})
    weight = 5
    score_df.loc[name] = [value,score,weight,score/5 * weight]


    ## 1b) EBIT Growth
    name = '1b) EBIT Growth'
    summary_df.loc['Operating Profit Growth (%)'] = database.loc['Operating Profit'].pct_change() * 100
    value = weighted_average(summary_df.loc['Operating Profit Growth (%)'])
    score = value_to_score(value,{-999:-3,0:0,10:1,20:1.5,30:2.5,40:3.75,50:4.5,60:5})
    weight = 10
    score_df.loc[name] = [value,score,weight,score/5 * weight]


    ## 1c) Bottom Line Growth
    name = '1c) Bottom Line Growth'
    summary_df.loc['Net Profit Growth (%)'] = database.loc['Net Profit Growth (%)']
    value = weighted_average(summary_df.loc['Operating Profit Growth (%)'])
    score = value_to_score(value,{-999:-3,0:0,5:1,10:2,20:3,30:4,40:5})
    weight = 10
    score_df.loc[name] = [value,score,weight,score/5 * weight]


    # Part 2: Earnings Quality
    ## 2a) Profit Margin
    name = '2a) Profit Margin'
    summary_df.loc['Net Profit Margin (%)'] = database.loc['Net Profit Margin (%)']
    value = weighted_average(summary_df.loc['Net Profit Margin (%)'])
    score = value_to_score(value,{-999:-3,0:0,6:1,10:1.5,13:2.5,17:3.75,19:4.5,22:5})
    weight = 10
    score_df.loc[name] = [value,score,weight,score/5 * weight]



    ## 2b) Stability of Profit Margin
    name = '2b) Stability of Profit Margin'
    summary_df.loc['Net Profit Margin (%)'] = database.loc['Net Profit Margin (%)']
    value = standard_deviation(summary_df.loc['Net Profit Margin (%)'])
    score = 5/3 if value < 5 else 0
    weight = 5
    score_df.loc[name] = [value,score,weight,score/5 * weight]



    ## 2c) Sign of Operating CF
    name = '2c) Sign of Operating CF'
    summary_df.loc['Net Cash Flow from Operating Activities'] = database.loc['Net Cash Flow from Operating Activities'] + database.loc['Taxes (Paid) / Refunded']
    value = -1 if (summary_df.loc['Net Cash Flow from Operating Activities'][-2:].astype(float) < 0).any() == True else 1
    score = -999 if value == -1 else 0
    weight = 1000
    score_df.loc[name] = [value,score,weight,score/5 * weight]


    ## 2d) Total Accruals to Total Assets
    name = '2d) Total Accruals to Total Assets'
    summary_df.loc['Total Accruals'] = database.loc['Operating Profit'] - database.loc['Net Cash Flow from Operating Activities']
    value = (summary_df.loc['Total Accruals'] / database.loc['Total Assets'])[-1]
    score = value_to_score(value,{-999:5,0:0,0.01:-5})
    weight = 5
    score_df.loc[name] = [value,score,weight,score/5 * weight]
    



    # Part 3: Profitability
    ## 3a) ROE
    name = '3a) ROE'
    summary_df.loc['Return on Equity (%)'] = database.loc['Return on Equity (%)']
    value = weighted_average(summary_df.loc['Return on Equity (%)'])
    score = value_to_score(value,{-999:-3,0:1,12:2,18:3,21:4,24:5})
    weight = 7
    score_df.loc[name] = [value,score,weight,score/5 * weight]




    ## 3b) ROIC
    name = '3b) ROIC'
    summary_df.loc['ROIC'] = database.loc['Operating Profit'] / (database.loc['Total Equity'] + database.loc['Total Debt'] - database.loc['Cash & Cash Equivalents at End of Year']) * 100
    value = weighted_average(summary_df.loc['ROIC'])
    score = value_to_score(value,{-999:-3,0:1,12:2,18:3,21:4,24:5})
    weight = 13
    score_df.loc[name] = [value,score,weight,score/5 * weight]




    ## 3c) Stability of Returns
    name = '3c) Stability of Returns'
    summary_df.loc['Stability of Returns'] = database.loc['Net Profit Margin (%)']
    value = (standard_deviation(summary_df.loc['Return on Equity (%)']) + standard_deviation(summary_df.loc['ROIC'])) / 2
    score = 5/3 if value < 5 else 0
    weight = 3
    score_df.loc[name] = [value,score,weight,score/5 * weight]



    ## 3d) Sign of FCF
    name = '3d) Sign of FCF'
    summary_df.loc['FCF'] = (database.loc['Net Cash Flow from Operating Activities'] + database.loc['Taxes (Paid) / Refunded']) - database.loc['Net Cash Flow from Investing Activities']
    value = -1 if (summary_df.loc['FCF'][-2:].astype(float) < 0).any() == True else 1
    score = -999 if value == -1 else 0
    weight = 1000
    score_df.loc[name] = [value,score,weight,score/5 * weight]


    ## 3e) Cash Reinvestment Rate
    name = '3e) Cash Reinvestment Rate'
    summary_df.loc['Cash Reinvestment Rate'] = -database.loc['Net Cash Flow from Investing Activities'] / (database.loc['Net Cash Flow from Operating Activities'] - database.loc['Taxes (Paid) / Refunded']) * 100
    value = weighted_average(summary_df.loc['Cash Reinvestment Rate'])
    score = value_to_score(value,{-999:5,0:4,15:3,30:2,45:1,60:0})
    weight = 7
    score_df.loc[name] = [value,score,weight,score/5 * weight]



    # Part 4: Solvency
    ## 4a) Net Debt to Operating CF
    name = '4a) Net Debt to Operating CF'
    summary_df.loc['Net Debt'] = database.loc['Total Debt'] - database.loc['Cash & Cash Equivalents at End of Year']
    summary_df.loc['Net Debt to Operating CF'] = summary_df.loc['Net Debt'] / database.loc['Net Cash Flow from Operating Activities']
    value = weighted_average(summary_df.loc['Net Debt to Operating CF'])
    score = value_to_score(value,{-999:5,0:4,3:3,4:2,6:1,8:0})
    weight = 10
    score_df.loc[name] = [value,score,weight,score/5 * weight]


    ## 4b) Net Debt to Equity
    name = '4b) Net Debt to Equity'
    summary_df.loc['Net Debt to Equity'] = summary_df.loc['Net Debt'] / database.loc['Total Equity']
    value = weighted_average(summary_df.loc['Net Debt to Equity'])
    score = value_to_score(value,{-999:5,0:4,15:3,30:2,45:1,55:0})
    weight = 10
    score_df.loc[name] = [value,score,weight,score/5 * weight]




    # Part 5: Calculate scores
    score = score_df['Weighted Score'].sum()
    
    return summary_df, score_df, score


def main():
    ticker = ' '
    ticker = input('Please Input the Ticker: ')
    while ticker != '':
        summary_df,score_df,score = score_calculation(ticker)

        print(summary_df)
        print('-------')
        print(score_df)
        print('-------')
        print('Total Score of ' + company_name(ticker) + ': ' + str("{:.2f}".format(score)))
        print('-------')
        
        ticker = input('Please Input the Ticker: ')


if __name__ == "__main__":
    main()