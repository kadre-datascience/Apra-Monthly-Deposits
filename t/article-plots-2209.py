import pandas as pd
import numpy as np 
import plotly_express as px
import plotly.graph_objects as go
pd.set_option('display.max_rows', 500)


def get_full_result():
    xls = pd.ExcelFile('../Data/Monthly authorised deposit-taking institution statistics back-series March 2019 - July 2022.xlsx')
    df = pd.read_excel(xls, sheet_name='Table 1', header=1)
    df.columns = df.columns.str.replace(' ','_')
    list_of_names=df.Institution_Name.unique()
    df['total_deposits'] = df['Intra-group_deposits']+df['Total_residents_deposits']+df['Cash_and_deposits_with_financial_institutions']
    df['total_burrowings'] = df['Total_short-term_borrowings']+df['Total_long-term_borrowings']+df['Negotiable_Certificates_of_Deposit']
    df['total_deposits+burrow'] = df['total_deposits'] + df['total_burrowings'] 
    df['deposit_ratio'] = df['total_deposits'] /df['total_deposits+burrow'] 
    df['Total_Assests'] = df['Total_residents_assets'] + df['Total_securitised_assets_on_balance_sheet'] 
    df['Total_Loans'] = df['Total_residents_loans_and_finance_leases'] + df['Intra-group_loans_and_finance_leases'] +df['Total_securitised_assets_on_balance_sheet']
    #df['LDR_asset'] =  df['Total_residents_assets']/ df['total_deposits+burrow']
    #df['LDR'] = df['Total_Loans']/ df['total_deposits+burrow']
    df['DLR'] = df['Total_residents_deposits']/ df['Total_residents_loans_and_finance_leases']
    #df['totalloan ratio'] = df['Total_Loans'] / df['total_deposits+burrow']
    #total hosuing
    df['Deposit/Asset'] = df['Total_residents_deposits']/ df['Total_residents_assets']
    df['Total_Housing_Loans'] =  df['Loans_to_households:_Housing:_Owner-occupied'] +  df['Loans_to_households:_Housing:_Investment'] 
    df_filt = df[['Period', 'Institution_Name','Deposits_by_households','Total_residents_loans_and_finance_leases','Total_residents_deposits','Total_Housing_Loans','Loans_to_households:_Credit_cards','Loans_to_households:_Other' ,'DLR', 'Deposit/Asset']]
    xls = pd.ExcelFile('../Data/APRA Reporting Institute Names by Sector.xlsx')
    categories = pd.read_excel(xls, sheet_name='Sheet1')
    categories.columns
    categoriesReal = categories.iloc[:,1:4]
    categoriesReal=categoriesReal.rename(columns={'Institute_Name':'Institution_Name'})
    fullresult = pd.merge(df,categoriesReal, how="left", on="Institution_Name")
    result = pd.merge(df_filt, categoriesReal, how="left", on="Institution_Name")
    result['sector_housing'] = result.groupby(['Sector','Period'])['Total_Housing_Loans'].transform('mean')
    result['sector_creditcards'] = result.groupby(['Sector','Period'])['Loans_to_households:_Credit_cards'].transform('mean')
    result['sector_OtherLoans'] = result.groupby(['Sector','Period'])['Loans_to_households:_Other'].transform('mean')
    result['sector_DLR'] = result.groupby(['Sector','Period'])['DLR'].transform('mean')
    result['sector_Deposit/Asset'] = result.groupby(['Sector','Period'])['Deposit/Asset'].transform('mean')
    result['sector_Total_residents_deposits'] = result.groupby(['Sector','Period'])['Total_residents_deposits'].transform('mean')
    result['sector_Total_residents_loans_and_finance_leases'] = result.groupby(['Sector','Period'])['Total_residents_loans_and_finance_leases'].transform('mean')
    result['sum_depo']= result.groupby(['Period','Sector'])['sector_Total_residents_deposits'].transform('sum')
    result['sum_loans']= result.groupby(['Period','Sector'])['sector_Total_residents_loans_and_finance_leases'].transform('sum')
    result['sector_DLR'] = result['sum_depo']/result['sum_loans']
    #Loans_to_non-financial_businesses	Loans_to_financial_institutions
    fullresult['sector_housing'] = fullresult.groupby(['Sector','Period'])['Total_Housing_Loans'].transform('mean')
    fullresult['sector_creditcards'] = fullresult.groupby(['Sector','Period'])['Loans_to_households:_Credit_cards'].transform('mean')
    fullresult['sector_OtherLoans'] = fullresult.groupby(['Sector','Period'])['Loans_to_households:_Other'].transform('mean')
    fullresult['sector_DLR'] = fullresult.groupby(['Sector','Period'])['DLR'].transform('mean')
    fullresult['sector_Deposit/Asset'] = fullresult.groupby(['Sector','Period'])['Deposit/Asset'].transform('mean')
    fullresult['sector_Loans_to_non_financial_businesses'] = fullresult.groupby(['Sector','Period'])['Loans_to_non-financial_businesses'].transform('mean')
    fullresult['sector_Loans_to_financial_institutions'] = fullresult.groupby(['Sector','Period'])['Loans_to_financial_institutions'].transform('mean')
    return fullresult


def get_cash_rate():
    cashrate = pd.read_csv("../Data/rba-cashrate.csv")
    cashrate.rename(columns={'Cash Rate Target':'cash-rate'},inplace=True)
    cashrate['Date'] = pd.to_datetime(cashrate['Date'])
    cashrate = cashrate[cashrate['Date']>'2020-01-31']
    cashrate = cashrate['Date cash-rate'.split()] 
    cashrate.drop_duplicates('cash-rate',inplace=True)
    display(cashrate)
    px.line(cashrate,x='Date',y='cash-rate').show()
    return cashrate


def get_plot_data(fullresult):
    pdf = fullresult

    #date work
    pdf['Date'] = pd.to_datetime(pdf['Period'])
    dates = ['2022-12-31', '2021-12-31', '2020-12-31',
    '2022-06-30', '2021-06-30', '2020-06-30',
    '2022-03-31', '2021-03-31', '2020-03-31',
    '2022-09-30', '2021-09-30', '2020-09-30']
    pdf = pdf[pdf['Date'].isin(dates)]
#    pdf['Date'] = pdf['Date'].dt.to_period('Q')
    pdf.sort_values('Date Institution_Name'.split(),inplace=True)

    #sample institutions
    tmp = pdf[pdf.Institution_Name.str.contains('Macq|Common|Westpac|Bendi|New Z|HS|BNK|National Aust')]
    display(tmp.Institution_Name.value_counts())
    tmp = tmp['Institution_Name Date Total_Housing_Loans'.split()]
    sample = tmp.copy()

    #agg big 4
    tmp = pdf[pdf.Institution_Name.str.contains('Common|Westpac|New Z|National Aust')]
    tmp = tmp['Institution_Name Date Total_Housing_Loans'.split()]
    tmp = tmp.pivot_table(index='Date',values='Total_Housing_Loans',aggfunc='sum')
    tmp['Institution_Name'] = 'Big 4'
    tmp.reset_index(inplace=True)
    big4 = tmp.copy()

    #mins
    sample = sample.append(big4)
    min_date = sample.Date.min()
    mins = sample[sample.Date==f'{min_date}']
    mins.rename(columns={'Total_Housing_Loans':'min'},inplace=True)

    #percent change
    sample = sample.merge(mins.drop('Date',axis=1),how='left',on='Institution_Name')
    sample['percentage_growth'] = round((sample['Total_Housing_Loans']-sample['min'])/sample['min'],2)

    #keep + censor institutions
    sample = sample[sample.Institution_Name.str.contains('Big|Macq|Bendi|HS|BNK')]
    sample.loc[sample.Institution_Name.str.contains('BNK'),'Institution_Name'] = 'Other bank'
    sample.loc[sample.Institution_Name.str.contains('Macq'),'Institution_Name'] = 'Tier 2 bank (1)'
    sample.loc[sample.Institution_Name.str.contains('Ben'),'Institution_Name'] = 'Tier 2 bank (2)'
    sample.loc[sample.Institution_Name.str.contains('HS'),'Institution_Name'] = 'International retail bank'
    sample = sample.drop('min',axis=1).sort_values('Date Institution_Name'.split())
    display(sample)
    
    return sample


def growth_plot():
    fig = px.line(plot_data,y='percentage_growth',x=plot_data.Date.astype(str),color='Institution_Name',template='plotly_white',
    labels={"percentage_growth":"Growth"}, title="Housing loan growth since Mar'20",render_mode='svg',
    color_discrete_map={
                    "Big 4": "brown",
                    "International retail bank": "#565656",
                    "Tier 2 bank (1)": "#316395",
                    "Tier 2 bank (2)": "rgb(15,133,84)",
                    "Other bank": "rgb(111,64,112)"},)
    fig.update_layout(legend=dict(
        orientation="h",
        title="",
#        yanchor="bottom",
#        y=1.2,
#        xanchor="left",
 #       x=0.4)
        ))
    fig.update_xaxes(title= "")
    fig.update_traces(mode='lines+markers')
    fig.add_annotation(x='2022-08-01', y=2.81,
                text="+281%",
                showarrow=False,def growth_plot():
    fig = px.line(plot_data,y='percentage_growth',x=plot_data.Date.astype(str),color='Institution_Name',template='plotly_white',
    labels={"percentage_growth":"Growth"}, title="Housing loan growth since Mar'20",render_mode='svg',
    color_discrete_map={
                    "Big 4": "brown",
                    "International retail bank": "#565656",
                    "Tier 2 bank (1)": "#316395",
                    "Tier 2 bank (2)": "rgb(15,133,84)",
                    "Other bank": "rgb(111,64,112)"},)
    fig.update_layout(legend=dict(
        orientation="h",
        title="",
#        yanchor="bottom",
#        y=1.2,
#        xanchor="left",
 #       x=0.4)
        ))
    fig.update_xaxes(title= "")
    fig.update_traces(mode='lines+markers')
    fig.add_annotation(x='2022-08-01', y=2.81,
                text="+281%",
                showarrow=False,
                arrowhead=1)
    fig.add_annotation(x='2022-08-01', y=0.35,
                text="+31%",
                showarrow=False,
                arrowhead=1)
    fig.add_annotation(x='2022-08-01', y=0.97,
                text="+97%",
                showarrow=False,
                arrowhead=1)
    fig.add_annotation(x='2022-08-15', y=0.11,
                text="Big4 +11%",
                showarrow=False,
                arrowhead=2)
    fig.show()  
    return fig


def cashrate_plot():
    fig = px.line(cashrate,y='cash-rate',x=cashrate.Date.astype(str),template='plotly_white',color_discrete_sequence=['black'],text=[f'{y}%' for y in cashrate['cash-rate']],title="Cash rate movement since Jan'20")
    fig.update_traces(textposition="top center",)
    fig.update_traces(mode='lines+markers+text',line=dict(dash='dash'))
    fig.update_yaxes(title= "Cash rate")
    fig.update_xaxes(title= "")
    fig.show()
    return fig

fullresult = get_full_result()
cashrate = get_cash_rate()
plot_data = get_plot_data(fullresult)
fig_growth = growth_plot()
fig_cashrate = cashrate_plot()
