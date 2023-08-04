import streamlit as st
import pandas as pd
from datetime import datetime

def load_data(profile_name):
    uploaded_file = st.file_uploader(f"Upload {profile_name} CSV", type=["csv"])
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file, low_memory=False, encoding='ISO-8859-1')
       # st.dataframe(data)
        return data
    return None

def get_status(days):
    if days >= 0:
        return 'Active'
    elif days >= -29:
        return 'Inactive'
    else:
        return 'Suspended'

def main():
    st.title("Profile Data Analysis")

    # User inputs for profiles and report date
    st.header("Upload CSV files")
    acc_profile = load_data("Acc profile")
    video_profile = load_data("Video profile")
    pv_profile = load_data("Payment Verification")
    ot_profile = load_data("Online Transaction")

    report_date = st.date_input("Select the Report Date")

    # Convert the report_date to pandas Timestamp
    report_date = pd.Timestamp(report_date)

    # Perform analysis and display results if all inputs are available
    if acc_profile is not None and video_profile is not None and pv_profile is not None and ot_profile is not None and report_date:
        # Account Profile Wise Retail- Data Status
        acc_profile = acc_profile.drop(acc_profile[acc_profile['Status'] == 'Terminated'].index)
        acc_profile = acc_profile.drop(acc_profile[acc_profile['Data Service Status'] == 'Terminated'].index)
        acc_profile = acc_profile.drop(acc_profile[acc_profile['Data Service Type'] == 'EOC'].index)
        acc_profile = acc_profile.dropna(subset=['Data Service Type'])
        acc_profile = acc_profile.dropna(subset=['Data Expiry Date'])

        acc_profile['Data Expiry Date'] = pd.to_datetime(acc_profile['Data Expiry Date'])
        acc_profile = acc_profile[acc_profile['Data Expiry Date'].dt.year != 1899]

        acc_profile['Data Service Type'] = acc_profile['Data Service Type'].replace({'FTTX': 'FTTH',
                                                                                     'Corp Fiber': 'FTTH',
                                                                                     'FTTH With Clear TV': 'FTTH',
                                                                                     'Intranet': 'FTTH',
                                                                                     'WiFi Hotspot': 'Wireless'})

        columns = ['User Id', 'Region', 'Status', 'Data Service Status', 'Data Service Type', 'Data Expiry Date']
        acc_profile = acc_profile[columns]

        acc_profile['Data Expiry Date'] = pd.to_datetime(acc_profile['Data Expiry Date'], format='%m/%d/%Y %H:%M')

        acc_profile['Days Until Expiry'] = (acc_profile['Data Expiry Date'] - report_date).dt.days
        acc_profile['New Status'] = acc_profile['Data Expiry Date'].apply(lambda x: get_status((x - report_date).days))
        acc_profile['Region'].fillna('Inside Valley', inplace=True)

        #acc_profile.to_csv('statuscount.csv')

        pivot_table_acc = pd.pivot_table(acc_profile, index=['Region', 'Data Service Type'], columns='New Status',
                                         values='User Id', aggfunc='count', margins=True)

        pivot_table_acc = pivot_table_acc.reset_index()
        pivot_table_acc = pivot_table_acc[['Region', 'Data Service Type', 'Active', 'Inactive', 'Suspended', 'All']]

        st.header("Account Profile Wise Retail- Data Status Region Wise")
        st.dataframe(pivot_table_acc)

        pivot_table_acc.to_csv('status_pivot_table.csv', index=False)

        # VideoPlanDetail Video Status
        video_profile = video_profile.dropna(subset=['MfgUniqueId'])
        video_profile = video_profile.drop(video_profile[video_profile['Service Status'] == 'Return'].index)
        video_profile = video_profile.dropna(subset=['ExpiryDate'])
        video_profile['ExpiryDate'] = pd.to_datetime(video_profile['ExpiryDate'])
        columns = ['USERID', 'Region', 'MfgUniqueId', 'ExpiryDate']
        video_profile = video_profile[columns]
        video_profile['ExpiryDate'] = pd.to_datetime(video_profile['ExpiryDate'], format='%m/%d/%Y %H:%M')
        video_profile['Days Until Expiry'] = (video_profile['ExpiryDate'] - report_date).dt.days
        video_profile['New Status'] = video_profile['ExpiryDate'].apply(lambda x: get_status((x - report_date).days))
        video_profile['Region'].fillna('Inside Valley', inplace=True)

        pivot_table_video = pd.pivot_table(video_profile, index=['Region'], columns='New Status', values='USERID', aggfunc='count', margins=True)

        st.header("VideoPlanDetail Video Status Region Wise")
        st.dataframe(pivot_table_video)

        # Online Transaction
        columns = ['Region', 'Plan Amount', 'Gateway']
        ot_profile = ot_profile[columns]
        ot_profile.rename(columns={'Plan Amount':'Selfcare Renew Amount', 'Gateway':'Selfcare Renew'}, inplace=True)
        pivot_table_ot = pd.pivot_table(ot_profile, index='Region', values=['Selfcare Renew Amount', 'Selfcare Renew'], aggfunc={'Selfcare Renew Amount': 'sum', 'Selfcare Renew': 'count'}, margins=True)
        pivot_table_gateway = pd.pivot_table(ot_profile, index='Selfcare Renew', values=['Selfcare Renew', 'Selfcare Renew Amount'], aggfunc={'Selfcare Renew': 'count', 'Selfcare Renew Amount': 'sum'}, margins=True)
        st.header("Online Transaction Region Wise")
        st.dataframe(pivot_table_ot)

        st.header("Online Transaction Gateway Wise")
        st.dataframe(pivot_table_gateway)

        # Payment Verification-All
        pv_profile['Region'].fillna('Inside Valley', inplace=True)
        columns = ['Region', 'PaidAmount']
        pv_profile = pv_profile[columns]
        pv_profile.rename(columns={'PaidAmount':'Today Collection'}, inplace=True)
        pivot_table_pv = pd.pivot_table(pv_profile, index='Region', values='Today Collection', aggfunc='sum', margins=True)

        st.header("Payment Verification-All Gateway Wise")
        st.dataframe(pivot_table_pv)

        # ... (Update CSV files here as required)

        # Show success message
        st.success("Analysis completed and CSV files updated!")

if __name__ == "__main__":
    main()
