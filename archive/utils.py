import pandas as pd


###### University_Grant_Processing_and_Analysis #########
def load_dataset(csv_path):
    return pd.read_csv(csv_path)

def add_location_column(df):
    df['Location'] = df['Institution_City'] + ", " + df['Institution_State']
    return df

def get_unique_locations(df):
    return df['Location'].unique()

def filter_by_city(df, city_name):
    return df[df['Institution_City'].str.upper() == city_name.upper()]

def get_unique_schools(df):
    return df['Institution_Name'].unique()

def filter_by_region_cities(df, cities):
    return df[df['Institution_City'].str.upper().isin(cities)]

def filter_by_institution_name(df, institution_name):
    return df[df['Institution_Name'].str.contains(institution_name, case=False, na=False)]

def count_grants_per_investigator(df):
    df['GrantCount'] = df.groupby('Investigator1_FullName')['AwardID'].transform('count')
    return df

def sort_by_columns(df, columns, ascending_orders):
    return df.sort_values(by=columns, ascending=ascending_orders)

def save_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")

def reshape_investigator_data(df, num_investigators=3):
    for i in range(1, num_investigators + 1):
        for col in df.columns:
            if f'Investigator{i}_' in col:
                new_col_name = col.replace(f'Investigator{i}_', f'Investigator_') + str(i)
                df.rename(columns={col: new_col_name}, inplace=True)
    
    df_long = pd.wide_to_long(df, 
                              stubnames=['Investigator_FirstName', 'Investigator_LastName', 'Investigator_MiddleInitial', 
                                         'Investigator_Suffix', 'Investigator_FullName', 'Investigator_Email', 
                                         'Investigator_NSFID', 'Investigator_StartDate', 'Investigator_EndDate', 
                                         'Investigator_RoleCode'],
                              i=['Institution_Name', 'Year', 'GrantCount', 'AwardID'], 
                              j='Investigator_Number', 
                              sep='',  
                              suffix=r'\d+')
    
    df_long = df_long.reset_index()
    return df_long


########